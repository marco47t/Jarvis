# commands/optimizer/orchestrator.py
import logging
from .workspace_manager import setup_workspace, cleanup_workspace
from .analyzer import analyze_codebase
from .transformer import apply_improvements
from .validator import validate_changes
from .reporter import generate_report

logger = logging.getLogger(__name__)

def run_optimization_pipeline():
    """
    The main orchestrator for the code optimization workflow.
    Coordinates copying, analyzing, transforming, validating, and reporting.
    """
    logger.info("===== STARTING OPTIMIZATION PIPELINE =====")
    workspace_path = None
    try:
        # 1. Setup Workspace (Copy project and init Git)
        branch_name, workspace_path = setup_workspace()
        if not workspace_path:
            raise RuntimeError("Workspace setup failed.")

        # 2. Analyze Codebase to find improvement candidates
        improvement_candidates = analyze_codebase(workspace_path)
        if not improvement_candidates:
            logger.info("Analysis found no improvement candidates. Ending run.")
            cleanup_workspace(workspace_path) # Clean up since there's nothing to do
            return "Analysis complete. No improvement candidates were found."

        # 3. Apply Transformations and validate each one
        successful_commits = apply_improvements(workspace_path, improvement_candidates)
        if not successful_commits:
            logger.info("No improvements were successfully applied. Ending run.")
            # The workspace is left for review as changes might have been attempted
            logger.info(f"Workspace at '{workspace_path}' has been left for manual review.")
            return "No improvements could be applied successfully after validation."
            
        # 4. Final Validation (run on the entire modified branch)
        final_validation_passed, validation_results = validate_changes(workspace_path)

        # 5. Generate Report
        report = generate_report(successful_commits, final_validation_passed, validation_results, workspace_path)
        
        logger.info("===== OPTIMIZATION PIPELINE FINISHED =====")
        print(report) # Print to console for now
        
        return f"Optimization run complete. See console for the full report. Modified code is available for review at:\n{workspace_path}"

    except Exception as e:
        logger.error(f"Optimization pipeline failed with a critical error: {e}", exc_info=True)
        return f"Optimizer failed critically: {e}"
    finally:
        # The workspace is intentionally left for the user to inspect.
        if workspace_path:
            logger.info(f"Workspace at '{workspace_path}' has been left for manual review.")