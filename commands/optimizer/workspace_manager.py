# commands/optimizer/workspace_manager.py
import os
import git
import shutil
from datetime import datetime
from config import OPTIMIZER_WORKSPACE_DIR, OPTIMIZER_SOURCE_DIR, OPTIMIZER_IGNORE_PATTERNS

def setup_workspace():
    """
    Copies the local project source into an isolated workspace.
    Initializes a new Git repository in the workspace to track changes.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir_name = f"run_{timestamp}"
    workspace_path = os.path.join(OPTIMIZER_WORKSPACE_DIR, run_dir_name)

    # Clean up the main workspace directory before starting
    if not os.path.exists(OPTIMIZER_WORKSPACE_DIR):
        os.makedirs(OPTIMIZER_WORKSPACE_DIR)

    print(f"Setting up isolated workspace at: {workspace_path}")

    # --- Copy the project source, ignoring specified patterns ---
    ignore_patterns = shutil.ignore_patterns(*OPTIMIZER_IGNORE_PATTERNS)
    shutil.copytree(OPTIMIZER_SOURCE_DIR, workspace_path, ignore=ignore_patterns)

    # --- Initialize a new Git repo in the workspace to manage changes ---
    repo = git.Repo.init(workspace_path)
    
    # Create an initial commit with all the original files
    repo.index.add(repo.git.ls_files().splitlines())
    repo.index.commit("Initial state before optimization")
    
    # We are already on the 'master' branch, which is fine for a local repo.
    # No need to create a named branch unless desired.
    branch_name = repo.active_branch.name

    print(f"Workspace setup complete. Initialized Git repo on branch '{branch_name}'.")
    return branch_name, workspace_path

def cleanup_workspace(workspace_path):
    """Removes the specific run's workspace directory."""
    if os.path.exists(workspace_path):
        print(f"Cleaning up workspace: {workspace_path}")
        shutil.rmtree(workspace_path)