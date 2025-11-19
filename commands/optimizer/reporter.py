# commands/optimizer/reporter.py
import git

def generate_report(commits, validation_passed, validation_results, repo_path):
    """Generates a human-readable report of the optimization run."""
    repo = git.Repo(repo_path)

    report_lines = [
        "## 🤖 Code Optimizer Run Report",
        "\n**Status:** " + ("✅ All changes passed final validation." if validation_passed else "❌ Final validation failed."),
        f"\n**Workspace:** `{repo_path}`",
        "\n### Validation Suite Results:",
        f"- Ruff Linting: {validation_results.get('ruff_check', 'N/A')}",
        f"- MyPy Type Checking: {validation_results.get('mypy_check', 'N/A')}",
        f"- Pytest Unit Tests: {validation_results.get('pytest_run', 'N/A')}",
        "\n### Applied Changes (Commits):",
    ]
    if not commits:
        report_lines.append("- No changes were successfully applied.")
    else:
        for commit_info in commits:
            commit = repo.commit(commit_info['commit_hash'])
            report_lines.append(f"\n- **Commit:** `{commit.hexsha[:7]}`")
            report_lines.append(f"  - **Description:** {commit_info['description']}")
            report_lines.append(f"  - **File:** `{commit_info['file']}`")
            
    return "\n".join(report_lines)