# commands/task_runner.py
# This module defines and executes multi-step automation tasks
# by coordinating calls to various AI and utility modules.

import logging
from config import ENABLE_LOGGING, LOG_FILE
from commands.ai_chat import GeminiClient # For AI interactions
# from commands.file_organizer import some_file_function # Example for future integration
# from commands.clipboard_tools import some_clipboard_function # Example for future integration

# --- Logger Setup ---
# Configure logging for this module.
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(LOG_FILE, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def run_report_builder_task(gemini_client: GeminiClient, topic: str) -> str:
    """
    Executes a multi-step task to build a simple report on a given topic.
    Steps: Query AI for information -> (Placeholder: Research) -> (Placeholder: Format).

    Args:
        gemini_client (GeminiClient): An initialized instance of the GeminiClient.
        topic (str): The topic for which to build the report.

    Returns:
        str: The generated report content or an error message.
    """
    logger.info(f"Starting 'report_builder' task for topic: '{topic}'")

    report_content = []

    # Step 1: Query AI for initial information
    query_prompt = f"Provide a concise overview of '{topic}', including key facts and a brief introduction."
    logger.info(f"AI Query (Report Builder - Step 1): {query_prompt}")
    initial_overview = gemini_client.generate_text(query_prompt)
    if "error" in initial_overview.lower() or "blocked" in initial_overview.lower():
        logger.error(f"Failed to get initial overview for '{topic}': {initial_overview}")
        return f"Failed to get initial overview for '{topic}'. Error: {initial_overview}"
    report_content.append(f"## Overview of {topic}\n\n{initial_overview}\n")
    logger.info(f"Received initial overview for '{topic}'.")

    # Step 2: (Placeholder) Simulate Research - In a real scenario, this might involve
    # using a search tool, reading files, or further AI queries.
    # For now, we'll ask the AI for a bit more detail.
    detail_prompt = f"Expand on the key aspects of '{topic}'. Provide 2-3 important details or sub-topics related to the overview you just provided."
    logger.info(f"AI Query (Report Builder - Step 2): {detail_prompt}")
    additional_details = gemini_client.generate_text(detail_prompt)
    if "error" in additional_details.lower() or "blocked" in additional_details.lower():
        logger.warning(f"Failed to get additional details for '{topic}': {additional_details}")
        report_content.append(f"\n*Could not retrieve additional details: {additional_details}*\n")
    else:
        report_content.append(f"### Key Details\n\n{additional_details}\n")
    logger.info(f"Received additional details for '{topic}'.")


    # Step 3: (Placeholder) Simulate Formatting and Conclusion
    # In a real scenario, this might involve structuring the text, adding headers,
    # or saving to a specific file format. For now, we'll ask the AI for a conclusion.
    conclusion_prompt = f"Write a brief concluding remark for a report on '{topic}', summarizing its importance or future outlook."
    logger.info(f"AI Query (Report Builder - Step 3): {conclusion_prompt}")
    conclusion = gemini_client.generate_text(conclusion_prompt)
    if "error" in conclusion.lower() or "blocked" in conclusion.lower():
        logger.warning(f"Failed to get conclusion for '{topic}': {conclusion}")
        report_content.append(f"\n*Could not generate a conclusion: {conclusion}*\n")
    else:
        report_content.append(f"### Conclusion\n\n{conclusion}\n")
    logger.info(f"Received conclusion for '{topic}'.")


    final_report = "\n".join(report_content)
    logger.info(f"Finished 'report_builder' task for topic: '{topic}'.")
    return final_report

# Dictionary to map task names to their respective functions
TASK_FUNCTIONS = {
    "report_builder": run_report_builder_task,
    # Add other multi-step tasks here as you develop them
    # "another_task": run_another_task_function,
}
