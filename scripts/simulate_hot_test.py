import os
import sys
import time
import subprocess
import requests
import json
import tempfile
import shutil
from pathlib import Path

# Add src directories to python path
sys.path.append(str(Path(__file__).parent.parent / "git-ai/src"))
sys.path.append(str(Path(__file__).parent.parent / "indexer-service/src"))

from git_ai.domain.factory import CodeChangeTaskFactory
from git_ai.domain.ooi import TaskRequested, ContextRetrieved, PatchGenerated, ChangeCommitted
from git_ai.tools import semantic_search_tool
from git_ai.commit_tool import structured_commit_tool

# Configuration
INDEXER_PORT = 8002
INDEXER_HOST = "localhost"
INDEXER_URL = f"http://{INDEXER_HOST}:{INDEXER_PORT}"

def start_indexer_service():
    print(f"[*] Starting Indexer Service on port {INDEXER_PORT}...")
    env = os.environ.copy()
    env["QDRANT_LOCATION"] = ":memory:"
    env["PORT"] = str(INDEXER_PORT)

    # Add indexer-service/src to PYTHONPATH for the subprocess
    indexer_src = str(Path(__file__).parent.parent / "indexer-service/src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] += f":{indexer_src}"
    else:
        env["PYTHONPATH"] = indexer_src

    process = subprocess.Popen(
        ["uvicorn", "indexer_service.main:app", "--host", INDEXER_HOST, "--port", str(INDEXER_PORT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for startup
    for i in range(30): # Increased timeout
        try:
            resp = requests.get(INDEXER_URL)
            if resp.status_code == 200:
                print("[*] Indexer Service is UP.")
                return process
        except requests.ConnectionError:
            time.sleep(1)
            print(f"    Waiting for service... ({i+1}/30)")

    stdout, stderr = process.communicate()
    raise RuntimeError(f"Failed to start indexer service:\n{stderr.decode()}")

def seed_indexer():
    print("[*] Seeding Indexer with fake codebase...")
    documents = [
        "def hello():\n    print('Hello World')",
        "def login(user, password):\n    if not password:\n        raise ValueError('No password')\n    print('Logged in')",
        "# README\nThis is a sample project."
    ]
    metadatas = [
        {"filename": "src/main.py"},
        {"filename": "src/auth.py"},
        {"filename": "README.md"}
    ]

    resp = requests.post(f"{INDEXER_URL}/index", json={"texts": documents, "metadatas": metadatas})
    if resp.status_code == 200:
        print(f"[*] Indexed {len(documents)} documents.")
    else:
        raise RuntimeError(f"Failed to index: {resp.text}")

def create_temp_codebase():
    """Creates a temporary directory with the fake codebase."""
    temp_dir = tempfile.mkdtemp()
    print(f"[*] Created temporary codebase at: {temp_dir}")

    # Create structure
    os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)

    files = {
        "src/main.py": "def hello():\n    print('Hello World')",
        "src/auth.py": "def login(user, password):\n    if not password:\n        raise ValueError('No password')\n    print('Logged in')",
        "README.md": "# README\nThis is a sample project."
    }

    for path, content in files.items():
        with open(os.path.join(temp_dir, path), "w") as f:
            f.write(content)

    return temp_dir

def simulate_agent_workflow():
    # Setup temporary filesystem
    temp_root = create_temp_codebase()

    try:
        print("\n=== STARTING AGENT SIMULATION ===\n")

        # 1. Define Task
        query = "Improve error handling in login function"
        print(f"[1] User Request: '{query}'")

        task = CodeChangeTaskFactory.create_initial(query)
        print(f"    -> State: {type(task).__name__} | ID: {task.task_id}")

        # 2. Retrieve Context
        print(f"[2] Agent 'Thinking': Searching for context...")
        os.environ["INDEXER_URL"] = INDEXER_URL # Configure tool

        # Agent decides to search for 'login error'
        search_query = "login function error handling"
        results = semantic_search_tool(search_query)
        print(f"    -> Found {len(results)} relevant code snippets.")
        for r in results:
            print(f"       - {r['payload']['filename']} (Score: {r['score']:.2f})")

        # Transition State
        task = CodeChangeTaskFactory.transition_to_context_retrieved(task, results)
        print(f"    -> State: {type(task).__name__}")

        # 3. Generate Patch (Mocking LLM)
        print(f"[3] Agent 'Thinking': Generating JSON Patch...")

        # Mock LLM Output based on context found (src/auth.py)
        # We want to change ValueError to PermissionError for demo
        patch = [
            {
                "op": "replace",
                "path": "/src~1auth.py", # Note escaping
                "value": "def login(user, password):\n    if not password:\n        raise PermissionError('Access Denied')\n    print('Logged in')"
            }
        ]
        print(f"    -> Generated Patch: {json.dumps(patch, indent=2)}")

        task = CodeChangeTaskFactory.transition_to_patch_generated(task, patch)
        print(f"    -> State: {type(task).__name__}")

        # 4. Apply Commit (Filesystem Mode)
        print(f"[4] Agent 'Acting': Applying Patch to Filesystem ({temp_root})...")

        # Using root_dir argument for the new Scalable Tool
        result = structured_commit_tool(task.patch, root_dir=temp_root)

        if "error" in result:
            print(f"    [!] Error applying patch: {result['error']}")
            return

        print("    -> Patch Applied Successfully.")

        # Verify file content on disk
        with open(os.path.join(temp_root, "src/auth.py"), "r") as f:
            new_content = f.read()
            print(f"    -> New Content of src/auth.py (from disk):\n{new_content}")

        # Transition State
        commit_hash = "abc123fakehash"
        task = CodeChangeTaskFactory.transition_to_change_committed(task, commit_hash)
        print(f"    -> State: {type(task).__name__} | Commit: {task.commit_hash}")

        print("\n=== SIMULATION COMPLETE ===")

    finally:
        # Cleanup
        print(f"[*] Cleaning up {temp_root}")
        shutil.rmtree(temp_root)

if __name__ == "__main__":
    service_process = None
    try:
        service_process = start_indexer_service()
        seed_indexer()
        simulate_agent_workflow()
    except Exception as e:
        print(f"\n[!] Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if service_process:
            print("\n[*] Stopping Indexer Service...")
            service_process.terminate()
            service_process.wait()
