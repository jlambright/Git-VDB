import os
import pytest
from fastapi.testclient import TestClient
from git_ai.tools import semantic_search_tool

# Since we are using TestClient, we need to make sure the indexer_service is in the PYTHONPATH
# This is usually handled by the pytest configuration, but we can add it explicitly if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'indexer-service' / 'src'))

# Now we can import the app
from indexer_service.main import app

@pytest.fixture(scope="module")
def indexer_service():
    """Starts the indexer service with in-memory Qdrant."""
    env = os.environ.copy()
    env["QDRANT_LOCATION"] = ":memory:"  # Ensure we use in-memory Qdrant for tests
    env["PORT"] = str(INDEXER_PORT)
    env["QDRANT_HOST"] = "localhost"
    env["QDRANT_PORT"] = "6333" # Default, but should be ignored if location is :memory:

    # Add src directories to PYTHONPATH for the subprocess
    git_ai_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'git-ai', 'src'))
    indexer_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'indexer-service', 'src'))
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{git_ai_src}:{indexer_src}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = f"{git_ai_src}:{indexer_src}"


    # Start the service in the background
    uvicorn_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'venv', 'bin', 'uvicorn'))
    main_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'indexer-service', 'src', 'indexer_service', 'main.py'))
    process = subprocess.Popen(
        [uvicorn_path, "main:app", "--host", INDEXER_HOST, "--port", str(INDEXER_PORT)],
        env=env,
        cwd=os.path.dirname(main_app_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for the service to be ready
    for _ in range(30):
        try:
            requests.get(INDEXER_URL)
            break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        process.terminate()
        stdout, stderr = process.communicate()
        pytest.fail(f"Indexer service failed to start:\nStdout: {stdout.decode()}\nStderr: {stderr.decode()}")

# Set environment variables for in-memory Qdrant *before* the client is created
os.environ["QDRANT_LOCATION"] = ":memory:"

@pytest.fixture(scope="module")
def test_client():
    """Create a TestClient instance for the indexer service."""
    with TestClient(app) as client:
        yield client

def test_semantic_search_integration(test_client):
    # The TestClient will make requests to this URL, so we need to set it for the tool
    # Even though it's not a real server, the tool needs a URL to make the request to the TestClient
    os.environ["INDEXER_URL"] = "http://testserver"

    # 1. Index some data
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a popular programming language.",
        "Git is a version control system.",
        "Qdrant is a vector database.",
        "JSON Patch is a format for describing changes to a JSON document."
    ]
    metadatas = [{"source": "doc1"}, {"source": "doc2"}, {"source": "doc3"}, {"source": "doc4"}, {"source": "doc5"}]

    response = test_client.post("/index", json={"texts": documents, "metadatas": metadatas})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Perform search using the tool
    # We need to patch requests.post to redirect to the test_client
    def mock_post(url, json, timeout=None):
        return test_client.post(url, json=json)

    import requests
    original_post = requests.post
    requests.post = mock_post

    results = semantic_search_tool("version control")

    # Restore the original requests.post
    requests.post = original_post

    # 3. Verify results
    assert len(results) > 0
    # The "Git" document should be the top result or near top
    top_result = results[0]
    # Debug: Print top_result structure
    print(f"\nTop Result Structure: {top_result}")

    assert "payload" in top_result, f"Expected 'payload' key in result, got: {top_result.keys()}"
    assert "Git is a version control system" in top_result["payload"]["text"]
    assert top_result["payload"]["source"] == "doc3"
