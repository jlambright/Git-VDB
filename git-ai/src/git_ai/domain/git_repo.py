import git
from typing import List, Optional
import os

class GitRepository:
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.environ.get("GIT_REPO_PATH", ".")
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {self.repo_path}")

    def commit_changes(self, message: str, files: List[str] = None) -> str:
        """
        Stages files (or all changes if files is None) and commits them.
        Returns the new commit hash.
        """
        if not self.repo.is_dirty(untracked_files=True):
             # Nothing to commit, check if we assume success or fail
             # Generally if nothing to commit, we return HEAD
             return self.repo.head.commit.hexsha

        self._stage_files(files)
        commit = self.repo.index.commit(message)
        return commit.hexsha

    def amend_changes(self, message: str, files: List[str] = None) -> str:
        """
        Stages changes and amends the previous commit.
        Returns the new commit hash.
        """
        # Even if not dirty, we might want to change the message, so we allow amend.
        self._stage_files(files)

        # git commit --amend -m message
        self.repo.git.commit(amend=True, m=message)
        return self.repo.head.commit.hexsha

    def revert_commit(self, commit_hash: str) -> str:
        """
        Reverts the specified commit using 'git revert'.
        Returns the hash of the new revert commit.
        """
        # git revert --no-edit <hash>
        self.repo.git.revert(commit_hash, no_edit=True)
        return self.repo.head.commit.hexsha

    def _stage_files(self, files: List[str] = None):
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)

    def get_file_content(self, file_path: str, ref: str = "HEAD") -> str:
        """
        Reads content of a file from a specific git ref.
        """
        try:
            return self.repo.git.show(f"{ref}:{file_path}")
        except git.Exc:
            raise FileNotFoundError(f"File {file_path} not found at {ref}")
