# commands/optimizer/transformer.py
import os
import git
import logging
from .validator import validate_changes

logger = logging.getLogger(__name__)

def apply_improvements(repo_path, candidates):
    """
    Applies proposed changes as individual commits and validates each one.
    If a change fails validation, it's reverted.
    """
    repo = git.Repo(repo_path)
    successful_commits = []

    # Sort candidates to apply low-risk changes first
    for candidate in sorted(candidates, key=lambda x: x['risk_score']):
        logger.info(f"Attempting to apply: {candidate['description']}")
        
        try:
            # --- STUB IMPLEMENTATION ---
            # In a real system, this would use an LLM or a codemod tool to generate
            # and apply the patch from the analyzer.
            # For this stub, we'll just append a comment to the file to simulate a change.
            file_to_modify = os.path.join(repo_path, candidate['file'])
            if os.path.exists(file_to_modify):
                with open(file_to_modify, 'a', encoding='utf-8') as f:
                    f.write(f"\n# OPTIMIZER_APPLIED_FIX: {candidate['id']}\n")
            else:
                logger.warning(f"  -> File '{candidate['file']}' not found. Skipping.")
                continue

            # Commit the change
            repo.index.add([file_to_modify])
            commit_message = f"refactor(optimizer): {candidate['description']}"
            commit = repo.index.commit(commit_message)
            
            # Validate this specific change
            passed, _ = validate_changes(repo_path)
            if passed:
                logger.info(f"  -> Change validated and committed: {commit.hexsha[:7]}")
                successful_commits.append({
                    "id": candidate['id'],
                    "commit_hash": commit.hexsha,
                    "commit_message": commit_message,
                    "description": candidate['description'],
                    "file": candidate['file']
                })
            else:
                logger.warning("  -> Change failed validation. Reverting commit.")
                repo.git.reset('--hard', 'HEAD~1') # Revert the last commit

        except Exception as e:
            logger.error(f"  -> Failed to apply change due to an error: {e}")
            repo.git.reset('--hard') # Reset any staged changes to be safe

    logger.info(f"Successfully applied and validated {len(successful_commits)} improvements.")
    return successful_commits