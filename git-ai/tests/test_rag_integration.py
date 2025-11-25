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
