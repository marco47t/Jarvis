# commands/document_processor.py
import os
import base64
import logging
import fitz  # PyMuPDF
import docx

from config import ENABLE_LOGGING

if ENABLE_LOGGING:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def process_document_for_viewing(file_path: str) -> dict:
    """
    Processes a PDF or DOCX file for web viewing.
    - PDFs are converted page-by-page into PNG images (Base64 encoded).
    - DOCX files have their text content extracted.
    """
    logger.info(f"Processing document for viewing: {file_path}")
    if not os.path.exists(file_path):
        return {"error": "File not found."}

    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    try:
        if extension == '.pdf':
            doc = fitz.open(file_path)
            pages_data = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Render page to a PNG pixmap in memory
                pix = page.get_pixmap(dpi=150) 
                img_bytes = pix.tobytes("png")
                # Encode the bytes to a Base64 string for a data URL
                base64_string = base64.b64encode(img_bytes).decode('utf-8')
                pages_data.append(base64_string)
            
            logger.info(f"Successfully converted {len(pages_data)} PDF pages to images.")
            return {"type": "pdf", "pages": pages_data, "filename": os.path.basename(file_path)}

        elif extension == '.docx':
            doc = docx.Document(file_path)
            full_text = [para.text for para in doc.paragraphs]
            content = '\n'.join(full_text)
            logger.info(f"Successfully extracted text from DOCX file.")
            return {"type": "docx", "content": content, "filename": os.path.basename(file_path)}

        else:
            return {"error": f"Unsupported file type: {extension}"}
            
    except Exception as e:
        logger.error(f"Failed to process document '{file_path}': {e}", exc_info=True)
        return {"error": f"An error occurred while processing the file: {e}"}