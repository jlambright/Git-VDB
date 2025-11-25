import os
import sys
import subprocess
import shutil
import tempfile
import json
from pathlib import Path
import pytest

# Add src directories
sys.path.append(str(Path(__file__).parent.parent / "git-ai/src"))

from git_ai.domain.git_repo import GitRepository
from git_ai.commit_tool import structured_commit_tool
from git_ai.revert_tool import revert_change_tool

def create_temp_repo():
    repo_dir = tempfile.mkdtemp()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)

    # Initial file
    with open(os.path.join(repo_dir, "test.txt"), "w") as f:
        f.write("initial content")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    return repo_dir

@pytest.fixture
def repo_dir():
    repo_dir = create_temp_repo()
    yield repo_dir
    shutil.rmtree(repo_dir)

def test_amend_flow(repo_dir):
    print(f"\n[*] Testing Amend Flow in {repo_dir}...")
    repo = GitRepository(repo_dir)
    initial_hash = repo.repo.head.commit.hexsha
    print(f"    Initial Hash: {initial_hash}")

    # Make a commit
    patch = json.dumps([{"op": "replace", "path": "/test.txt", "value": "change 1"}])
    res = structured_commit_tool(patch, root_dir=repo_dir, commit_message="change 1", vdb_id="dummy_id_1")
    commit_1 = res["commit_hash"]
    print(f"    Commit 1: {commit_1}")

    assert commit_1 != initial_hash
    with open(os.path.join(repo_dir, "test.txt"), "r") as f:
        assert f.read() == "change 1"

    # Amend that commit
    print("    Amending Commit 1...")
    patch_amend = json.dumps([{"op": "replace", "path": "/test.txt", "value": "change 1 amended"}])
    res_amend = structured_commit_tool(
        patch=patch_amend,
        root_dir=repo_dir,
        commit_message="change 1 amended",
        amend=True,
        vdb_id="dummy_id_2"
    )
    assert "error" in res_amend
    assert "disallowed" in res_amend["error"]

def test_revert_flow(repo_dir):
    print(f"\n[*] Testing Revert Flow in {repo_dir}...")
    repo = GitRepository(repo_dir)

    # Ensure clean slate or just continue
    # Let's add a file to revert
    patch = json.dumps([{"op": "add", "path": "/bad_file.txt", "value": "bad content"}])
    res = structured_commit_tool(patch, root_dir=repo_dir, commit_message="bad commit", vdb_id="dummy_id_3")
    bad_commit_hash = res["commit_hash"]
    print(f"    Bad Commit: {bad_commit_hash}")

    assert os.path.exists(os.path.join(repo_dir, "bad_file.txt"))

    # Revert it
    print("    Reverting Bad Commit...")
    res_revert = revert_change_tool(bad_commit_hash, repo_dir)
    revert_hash = res_revert["revert_commit_hash"]
    print(f"    Revert Commit: {revert_hash}")

    # Verify file is gone (since we added it, revert should delete it)
    # git revert of an add is a delete.
    if os.path.exists(os.path.join(repo_dir, "bad_file.txt")):
        print("    [!] File still exists! Checking content...")
        # Note: git revert might conflict if working tree is dirty, but here it should be clean.
        # Check git status
        print(repo.repo.git.status())
        raise AssertionError("File should have been deleted by revert")
    else:
        print("    Success: bad_file.txt is gone.")

if __name__ == "__main__":
    repo_dir = create_temp_repo()
    try:
        test_amend_flow(repo_dir)
        test_revert_flow(repo_dir)
        print("\n[SUCCESS] Advanced Git Capabilities Verified.")
    finally:
        shutil.rmtree(repo_dir)
