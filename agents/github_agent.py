"""GitHub agent for handling repository operations."""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from github import Github, GithubException
from core.agent_base import BaseAgent, Task
from core.config_models import GitHubAgentConfig
from core.exceptions import FatalError

class GitHubAgent(BaseAgent):
    """Agent responsible for GitHub repository operations."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, GitHubAgentConfig):
            raise FatalError(f"Invalid configuration for GitHubAgent {agent_id}")
            
        # Initialize GitHub client
        self.github = Github(self.config.metadata.get("access_token"))
        self.repo = None
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the GitHub task."""
        logger.info(f"Preprocessing GitHub task: {task.task_id}")
        
        # Validate repository
        repo_name = task.metadata.get("repository")
        if not repo_name:
            raise FatalError("Repository name is required")
            
        try:
            self.repo = self.github.get_repo(repo_name)
        except GithubException as e:
            raise FatalError(f"Failed to access repository: {e}")
            
        return {
            "repository": repo_name,
            "branch": task.metadata.get("branch", "main"),
            "commit_message": task.metadata.get("commit_message", "Update from P.E.P.P.E.R.")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the GitHub task."""
        logger.info(f"Executing GitHub task: {task.task_id}")
        
        if task.task_type == "github.commit":
            return await self._commit_changes(task)
        elif task.task_type == "github.create_branch":
            return await self._create_branch(task)
        elif task.task_type == "github.create_pull_request":
            return await self._create_pull_request(task)
        elif task.task_type == "github.merge":
            return await self._merge_changes(task)
        else:
            raise FatalError(f"Unsupported task type: {task.task_type}")
            
    async def _commit_changes(self, task: Task) -> Dict[str, Any]:
        """Commit changes to the repository."""
        branch = task.metadata.get("branch", "main")
        commit_message = task.metadata.get("commit_message", "Update from P.E.P.P.E.R.")
        files = task.metadata.get("files", [])
        
        try:
            # Create or get branch
            try:
                git_ref = self.repo.get_git_ref(f"heads/{branch}")
            except GithubException:
                git_ref = self.repo.get_git_ref("heads/main")
                self.repo.create_git_ref(f"refs/heads/{branch}", git_ref.object.sha)
                
            # Create blobs for each file
            blobs = []
            for file_path in files:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                blob = self.repo.create_git_blob(
                    content=content,
                    encoding='base64',
                    owner=self.repo.owner.login,
                    repo=self.repo.name
                )
                blobs.append(blob)
                
            # Create tree
            tree_elements = []
            for file_path, blob in zip(files, blobs):
                tree_elements.append({
                    'path': os.path.basename(file_path),
                    'mode': '100644',
                    'type': 'blob',
                    'sha': blob.sha
                })
                
            tree = self.repo.create_git_tree(
                tree_elements,
                base_tree=git_ref.object.sha
            )
            
            # Create commit
            commit = self.repo.create_git_commit(
                message=commit_message,
                tree=tree,
                parents=[git_ref.object.sha]
            )
            
            # Update reference
            git_ref.edit(sha=commit.sha)
            
            return {
                "status": "success",
                "message": f"Committed changes to {branch}",
                "details": {
                    "commit_sha": commit.sha,
                    "branch": branch,
                    "files": files
                }
            }
        except GithubException as e:
            logger.error(f"Failed to commit changes: {e}")
            raise
            
    async def _create_branch(self, task: Task) -> Dict[str, Any]:
        """Create a new branch."""
        branch_name = task.metadata.get("branch_name")
        base_branch = task.metadata.get("base_branch", "main")
        
        if not branch_name:
            raise FatalError("Branch name is required")
            
        try:
            # Get base branch reference
            base_ref = self.repo.get_git_ref(f"heads/{base_branch}")
            
            # Create new branch
            self.repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
            
            return {
                "status": "success",
                "message": f"Created branch {branch_name}",
                "details": {
                    "branch": branch_name,
                    "base_branch": base_branch
                }
            }
        except GithubException as e:
            logger.error(f"Failed to create branch: {e}")
            raise
            
    async def _create_pull_request(self, task: Task) -> Dict[str, Any]:
        """Create a pull request."""
        title = task.metadata.get("title", "Update from P.E.P.P.E.R.")
        body = task.metadata.get("body", "")
        head_branch = task.metadata.get("head_branch")
        base_branch = task.metadata.get("base_branch", "main")
        
        if not head_branch:
            raise FatalError("Head branch is required")
            
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            return {
                "status": "success",
                "message": f"Created pull request #{pr.number}",
                "details": {
                    "pr_number": pr.number,
                    "title": title,
                    "head_branch": head_branch,
                    "base_branch": base_branch
                }
            }
        except GithubException as e:
            logger.error(f"Failed to create pull request: {e}")
            raise
            
    async def _merge_changes(self, task: Task) -> Dict[str, Any]:
        """Merge changes from a branch."""
        branch = task.metadata.get("branch")
        base_branch = task.metadata.get("base_branch", "main")
        
        if not branch:
            raise FatalError("Branch to merge is required")
            
        try:
            # Create pull request
            pr = self.repo.create_pull(
                title=f"Merge {branch} into {base_branch}",
                body="Automated merge by P.E.P.P.E.R.",
                head=branch,
                base=base_branch
            )
            
            # Merge pull request
            pr.merge(merge_method="squash")
            
            return {
                "status": "success",
                "message": f"Merged {branch} into {base_branch}",
                "details": {
                    "pr_number": pr.number,
                    "branch": branch,
                    "base_branch": base_branch
                }
            }
        except GithubException as e:
            logger.error(f"Failed to merge changes: {e}")
            raise
            
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing GitHub task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "repository": task.metadata.get("repository"),
            "branch": task.metadata.get("branch"),
            "commit_message": task.metadata.get("commit_message")
        }
        
        return result 