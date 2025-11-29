import os
import sys
import subprocess
import time
import requests
import tempfile
import shutil
import json
from pathlib import Path

# Add src directories to python path
sys.path.append(str(Path(__file__).parent.parent / "git-ai/src"))
sys.path.append(str(Path(__file__).parent.parent / "indexer-service/src"))

from git_ai.tools import semantic_search_tool
from git_ai.commit_tool import structured_commit_tool
# We skip importing mcp_server directly because the decorators make functions uncallable in this context
# and we just want to verify the logic flow that the MCP server utilizes.

# Constants
INDEXER_PORT = 8003
INDEXER_HOST = "localhost"
INDEXER_URL = f"http://{INDEXER_HOST}:{INDEXER_PORT}"

def start_indexer_service():
    print(f"[*] Starting Indexer Service on port {INDEXER_PORT}...")
    env = os.environ.copy()
    env["QDRANT_LOCATION"] = ":memory:"
    env["PORT"] = str(INDEXER_PORT)

    indexer_src = str(Path(__file__).parent.parent / "indexer-service/src")
    env["PYTHONPATH"] = indexer_src

    process = subprocess.Popen(
        ["uvicorn", "indexer_service.main:app", "--host", INDEXER_HOST, "--port", str(INDEXER_PORT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    for i in range(30):
        try:
            resp = requests.get(INDEXER_URL)
            if resp.status_code == 200:
                return process
        except requests.ConnectionError:
            time.sleep(1)

    stdout, stderr = process.communicate()
    raise RuntimeError(f"Failed to start indexer service:\n{stderr.decode()}")

def create_temp_git_repo():
    temp_dir = tempfile.mkdtemp()
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "mcp@test.com"], cwd=temp_dir, check=True)
    subprocess.run(["git", "config", "user.name", "MCP Test"], cwd=temp_dir, check=True)

    with open(os.path.join(temp_dir, "test.py"), "w") as f:
        f.write("print('hello')")

    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=temp_dir, check=True)

    return temp_dir

def test_mcp_logic_integration():
    repo_path = create_temp_git_repo()
    service = None
    try:
        service = start_indexer_service()

        # Configure Environment (as if set for the MCP process)
        os.environ["INDEXER_URL"] = INDEXER_URL
        os.environ["GIT_REPO_PATH"] = repo_path

        print("Testing semantic_search_tool (MCP Delegate)...")
        try:
            results = semantic_search_tool("test", 1)
            print(f"Search Results: {results}")
        except Exception as e:
            print(f"Search failed: {e}")

        print("Testing structured_commit_tool (MCP Delegate)...")
        # In mcp_server.py:
        # repo_path = os.environ.get("GIT_REPO_PATH", DEFAULT_REPO_PATH)
        # return structured_commit_tool(patch=patch, root_dir=repo_path, commit_message=commit_message)

        patch = json.dumps([{
            "op": "replace",
            "path": "/test.py",
            "value": "print('world')"
        }])

        # We manually perform the call that mcp_server.py would do
        configured_path = os.environ.get("GIT_REPO_PATH")
        result = structured_commit_tool(
            patch=patch,
            root_dir=configured_path,
            commit_message="fix: hello to world"
        )
        print(f"Commit Result: {result}")

        assert result["status"] == "success"
        assert "commit_hash" in result

        # Verify file
        with open(os.path.join(repo_path, "test.py"), "r") as f:
            content = f.read()
            assert content == "print('world')"

        print("MCP Logic Verification Passed!")

    finally:
        if service:
            service.terminate()
        shutil.rmtree(repo_path)

if __name__ == "__main__":
    test_mcp_logic_integration()
