import git
from typing import List, Optional
import os

class GitRepository:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {repo_path}")

    def commit_changes(self, message: str, files: List[str] = None) -> str:
        """
        Stages files (or all changes if files is None) and commits them.
        Returns the new commit hash.
        """
        if not self.repo.is_dirty(untracked_files=True):
             # Nothing to commit
             return self.repo.head.commit.hexsha

        if files:
            # Stage specific files
            self.repo.index.add(files)
        else:
            # Stage all changes (including untracked)
            self.repo.git.add(A=True)

        commit = self.repo.index.commit(message)
        return commit.hexsha

    def get_file_content(self, file_path: str, ref: str = "HEAD") -> str:
        """
        Reads content of a file from a specific git ref.
        """
        try:
            return self.repo.git.show(f"{ref}:{file_path}")
        except git.Exc:
            raise FileNotFoundError(f"File {file_path} not found at {ref}")
