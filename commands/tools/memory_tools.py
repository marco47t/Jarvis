# commands/tools/memory_tools.py
import datetime
import json
import os
from ..memory_manager import MemoryManager

# We assume a singleton instance of MemoryManager will be passed or available
# For now, we'll instantiate it here. A better approach in a larger app
# would be to use dependency injection.
memory_manager = MemoryManager()

def save_task_summary_to_memory(task_summary: str, tools_used: list, final_result: str) -> str:
    """
    Saves a summary of a completed task to the agent's long-term memory.
    This should be called as the very last step after a goal is achieved.
    """
    memory_manager.add_memory(task_summary, tools_used, final_result)
    return "Task summary has been committed to long-term memory."

def save_user_preference(preference_key: str, preference_value: str) -> str:
    """
    Saves a user preference to the agent's profile for future reference.
    For example, 'preferred_summary_style', 'bullet_points'.
    """
    memory_manager.save_user_preference(preference_key, preference_value)
    return f"Preference '{preference_key}' has been saved."

def get_user_preferences() -> str:
    """
    Retrieves all currently saved user preferences.
    """
    prefs = memory_manager.get_all_preferences()
    if not prefs:
        return "No user preferences have been saved yet."
    return "Current User Preferences:\n" + "\n".join(f"- {k}: {v}" for k, v in prefs.items())

def save_feedback(feature: str, rating: int, comment: str) -> str:
    """Saves user feedback to a log file."""
    feedback_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "feature": feature,
        "rating": rating,
        "comment": comment
    }
    log_path = os.path.join("data", "feature_feedback.jsonl")
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry) + '\n')
        return "Feedback submitted successfully. Thank you!"
    except Exception as e:
        return f"Error saving feedback: {e}"