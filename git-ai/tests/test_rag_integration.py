import os
import subprocess
import time
import requests
import pytest
import signal
from git_ai.tools import semantic_search_tool

# Constants
INDEXER_HOST = "localhost"
INDEXER_PORT = 8001  # Use a different port than default to avoid conflict if running
INDEXER_URL = f"http://{INDEXER_HOST}:{INDEXER_PORT}"

@pytest.fixture(scope="module")
def indexer_service():
    """Starts the indexer service with in-memory Qdrant."""
    env = os.environ.copy()
    env["QDRANT_LOCATION"] = ":memory:"  # Ensure we use in-memory Qdrant for tests
    env["PORT"] = str(INDEXER_PORT)
    env["QDRANT_HOST"] = "localhost"
    env["QDRANT_PORT"] = "6333" # Default, but should be ignored if location is :memory:

    # Check if QDRANT_LOCATION is being respected by indexer-service/src/indexer_service/main.py
    # In main.py:
    # if os.environ.get("QDRANT_LOCATION") == ":memory:":
    #      client = QdrantClient(location=":memory:")

    # Start the service in the background
    process = subprocess.Popen(
        ["uvicorn", "indexer_service.main:app", "--host", INDEXER_HOST, "--port", str(INDEXER_PORT)],
        env=env,
        cwd="indexer-service/src", # Adjust cwd to find the module
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

    yield process

    # Cleanup
    # Send SIGTERM first
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def test_semantic_search_integration(indexer_service):
    # Set environment variable for the tool
    os.environ["INDEXER_URL"] = INDEXER_URL

    # 1. Index some data
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a popular programming language.",
        "Git is a version control system.",
        "Qdrant is a vector database.",
        "JSON Patch is a format for describing changes to a JSON document."
    ]
    metadatas = [{"source": "doc1"}, {"source": "doc2"}, {"source": "doc3"}, {"source": "doc4"}, {"source": "doc5"}]

    response = requests.post(f"{INDEXER_URL}/index", json={"texts": documents, "metadatas": metadatas})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Perform search using the tool
    results = semantic_search_tool("version control")

    # 3. Verify results
    assert len(results) > 0
    # The "Git" document should be the top result or near top
    top_result = results[0]
    # Debug: Print top_result structure
    print(f"\nTop Result Structure: {top_result}")

    assert "payload" in top_result, f"Expected 'payload' key in result, got: {top_result.keys()}"
    assert "Git is a version control system" in top_result["payload"]["text"]
    assert top_result["payload"]["source"] == "doc3"
