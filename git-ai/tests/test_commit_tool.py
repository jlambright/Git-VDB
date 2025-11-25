import pytest
from unittest.mock import MagicMock, patch, mock_open
from git_ai.commit_tool import structured_commit_tool

# Mock the GitRepository class
@pytest.fixture
def mock_git_repo():
    with patch('git_ai.commit_tool.GitRepository') as mock:
        yield mock

@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('builtins.open')
def test_commit_tool_success(mock_open, mock_exists, mock_makedirs, mock_git_repo):
    """Tests a successful commit with a VDB ID."""
    mock_repo_instance = mock_git_repo.return_value
    mock_repo_instance.commit_changes.return_value = "mock_commit_hash"

    result = structured_commit_tool(
        patch=[{"op": "add", "path": "/test.txt", "value": "hello"}],
        vdb_id="01F8X3Z2Y4Z4Q4Z4Z4Z4Q4Z4Z4",
        commit_message="Test commit",
        root_dir="/fake/dir"
    )

    assert result["commit_status"] == "success"
    assert result["commit_hash"] == "mock_commit_hash"

    # Verify the commit message format
    expected_message = "Test commit\n\nGit-VDB-ID: 01F8X3Z2Y4Z4Q4Z4Z4Z4Q4Z4Z4"
    mock_repo_instance.commit_changes.assert_called_once_with(expected_message)

def test_commit_tool_amend_disallowed(mock_git_repo):
    """Tests that amending a commit is disallowed."""
    result = structured_commit_tool(
        patch=[{"op": "add", "path": "/test.txt", "value": "hello"}],
        vdb_id="01F8X3Z2Y4Z4Q4Z4Z4Z4Q4Z4Z5",
        commit_message="Test commit",
        root_dir="/fake/dir",
        amend=True
    )

    assert "error" in result
    assert "disallowed" in result["error"]
    mock_git_repo.return_value.commit_changes.assert_not_called()
    mock_git_repo.return_value.amend_changes.assert_not_called()

@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_patch_application_called(mock_open_func, mock_exists, mock_makedirs, mock_git_repo):
    """Verify that the patch is applied before commit."""
    mock_repo_instance = mock_git_repo.return_value
    mock_repo_instance.commit_changes.return_value = "mock_commit_hash"

    structured_commit_tool(
        patch=[{"op": "replace", "path": "/src~1test.txt", "value": "new content"}],
        vdb_id="01F8X3Z2Y4Z4Q4Z4Z4Z4Q4Z4Z6",
        commit_message="Patch test",
        root_dir="/fake/dir"
    )

    mock_makedirs.assert_called_once_with('/fake/dir/src', exist_ok=True)
    mock_open_func.assert_called_once_with('/fake/dir/src/test.txt', 'w', encoding='utf-8')
    mock_open_func().write.assert_called_once_with('new content')
