# commands/clipboard_tools.py
import pyperclip
import logging

logger = logging.getLogger(__name__)

def get_clipboard_content() -> str:
    """
    Returns the current text content of the system clipboard.
    """
    try:
        content = pyperclip.paste()
        logger.info("Successfully retrieved content from clipboard.")
        # Return a truncated version if it's very long, for display purposes
        return content if len(content) < 2000 else content[:2000] + "\n... [content truncated]"
    except Exception as e:
        logger.error(f"Could not read from clipboard: {e}")
        return f"Error: Could not read from clipboard. It might be empty or contain non-text data. Details: {e}"

def set_clipboard_content(text: str) -> str:
    """
    Sets the system clipboard to the given text.

    Args:
        text (str): The text to place in the clipboard.
    """
    try:
        pyperclip.copy(text)
        logger.info("Successfully set clipboard content.")
        return "Clipboard content has been updated successfully."
    except Exception as e:
        logger.error(f"Could not write to clipboard: {e}")
        return f"Error: Could not write to clipboard. Details: {e}"