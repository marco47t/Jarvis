# commands/document_tools.py
import logging
import os
import fitz  # PyMuPDF
import docx  # python-docx

from config import ENABLE_LOGGING, LOG_FILE

# --- Logger Setup ---
if ENABLE_LOGGING:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def read_pdf_content(file_path: str) -> str:
    """
    Reads and extracts all text content from a specified PDF file.

    Args:
        file_path (str): The absolute or relative path to the PDF file.

    Returns:
        str: The extracted text content of the PDF, or an error message if it fails.
    """
    logger.info(f"Attempting to read PDF content from: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' was not found."
    
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")
        
        logger.info(f"Successfully extracted {len(text)} characters from '{os.path.basename(file_path)}'.")
        # Return a subset if it's too long to avoid overwhelming the context window
        return text if len(text) < 8000 else text[:8000] + "\n... [content truncated]"
    except Exception as e:
        logger.error(f"Failed to read PDF file '{file_path}': {e}", exc_info=True)
        return f"Error: Could not read the PDF file. It might be corrupted or password-protected. Details: {e}"


def read_docx_content(file_path: str) -> str:
    """
    Reads and extracts all text content from a specified DOCX (Microsoft Word) file.

    Args:
        file_path (str): The absolute or relative path to the DOCX file.

    Returns:
        str: The extracted text content of the document, or an error message if it fails.
    """
    logger.info(f"Attempting to read DOCX content from: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' was not found."

    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        text = '\n'.join(full_text)

        logger.info(f"Successfully extracted {len(text)} characters from '{os.path.basename(file_path)}'.")
        # Return a subset if it's too long
        return text if len(text) < 8000 else text[:8000] + "\n... [content truncated]"
    except Exception as e:
        logger.error(f"Failed to read DOCX file '{file_path}': {e}", exc_info=True)
        return f"Error: Could not read the DOCX file. It might be an older format (.doc) or corrupted. Details: {e}"