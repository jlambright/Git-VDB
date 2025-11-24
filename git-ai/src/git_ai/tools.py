import os
import requests
from typing import List, Dict, Any

def semantic_search_tool(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a semantic search to retrieve relevant code context or documentation.

    Args:
        query (str): The search query describing what you are looking for.
        limit (int): The maximum number of results to return. Defaults to 5.

    Returns:
        List[Dict[str, Any]]: A list of search results, each containing 'text', 'metadata', etc.
    """
    indexer_url = os.environ.get("INDEXER_URL", "http://indexer-service:8000")
    endpoint = f"{indexer_url}/search"

    try:
        response = requests.post(endpoint, json={"query": query, "limit": limit}, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        return [{"error": f"Failed to connect to indexer service: {str(e)}"}]
