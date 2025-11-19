# commands/file_organizer.py
import os
import shutil
import re
import time
from pathlib import Path
import datetime

# Helper function to prevent filename collisions
def _get_unique_path(destination_path: Path) -> Path:
    if not destination_path.exists():
        return destination_path
    
    base_name = destination_path.stem
    suffix = destination_path.suffix
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{suffix}"
        new_path = destination_path.with_name(new_name)
        if not new_path.exists():
            return new_path
        counter += 1

# --- NEW: General Purpose File Tools ---

def move_file(source_path: str, destination_folder: str) -> str:
    """
    Moves a file from a source path to a destination folder.
    This tool is for moving to specific, user-defined locations.

    Args:
        source_path (str): The full path of the file to move.
        destination_folder (str): The full path of the folder to move the file into.
    
    Returns:
        str: A confirmation message or an error.
    """
    try:
        source = Path(source_path)
        destination = Path(destination_folder)
        
        if not source.is_file():
            return f"Error: Source path '{source_path}' is not a valid file."
            
        destination.mkdir(parents=True, exist_ok=True)
        
        final_path = _get_unique_path(destination / source.name)
        shutil.move(source, final_path)
        return f"Successfully moved '{source.name}' to '{final_path}'."
    except Exception as e:
        return f"Error moving file: {e}"

def rename_file(current_path: str, new_name: str) -> str:
    """
    Renames a file. The new name should include the extension.

    Args:
        current_path (str): The full path of the file to rename.
        new_name (str): The new name for the file (e.g., 'new_icon.ico').

    Returns:
        str: A confirmation message or an error.
    """
    try:
        source = Path(current_path)
        if not source.is_file():
            return f"Error: Source path '{current_path}' is not a valid file."
            
        destination = source.with_name(new_name)
        final_destination = _get_unique_path(destination)
        
        os.rename(source, final_destination)
        return f"Successfully renamed '{source.name}' to '{final_destination.name}'."
    except Exception as e:
        return f"Error renaming file: {e}"

# --- SPECIALIST TOOLS ---

def handle_invoice(file_path: str, company: str, date: str, amount: str = None) -> str:
    """Handles files classified as invoices. Renames and moves them to a structured folder."""
    home_dir = Path.home()
    invoices_dir = home_dir / "Documents" / "Invoices"
    company_dir = invoices_dir / (company.strip() if company else "Unspecified")
    company_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = date.strip() if date else datetime.date.today().strftime('%Y-%m-%d')
    new_filename = f"{date_str}_{company}_Invoice.pdf"
    
    destination_path = _get_unique_path(company_dir / new_filename)
    shutil.move(file_path, destination_path)
    return f"Filed invoice from {company} to '{destination_path.relative_to(home_dir)}'."

def handle_screenshot(file_path: str, subject: str) -> str:
    """Handles screenshots. Renames them based on a subject and moves them."""
    home_dir = Path.home()
    screenshots_dir = home_dir / "Pictures" / "Screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y%m%d_%H%M%S')
    subject_str = re.sub(r'[^\w\-_\. ]', '_', subject.strip()) # Sanitize subject
    new_filename = f"Screenshot_{timestamp}_{subject_str}.png"
    
    destination_path = _get_unique_path(screenshots_dir / new_filename)
    shutil.move(file_path, destination_path)
    return f"Saved screenshot about '{subject}' to '{destination_path.relative_to(home_dir)}'."

def handle_project_asset(file_path: str, project_name: str, asset_type: str) -> str:
    """Handles project-related assets like images, docs, or code."""
    home_dir = Path.home()
    projects_dir = home_dir / "Documents" / "Projects"
    project_dir = projects_dir / (project_name.strip() if project_name else "General Project")
    
    asset_dir = project_dir / (asset_type.strip().capitalize() if asset_type else "Assets")
    asset_dir.mkdir(parents=True, exist_ok=True)

    destination_path = _get_unique_path(asset_dir / os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    return f"Moved project asset for '{project_name}' to '{destination_path.relative_to(home_dir)}'."

def handle_generic_document(file_path: str) -> str:
    """Default handler for generic documents."""
    home_dir = Path.home()
    docs_dir = home_dir / "Documents"
    destination_path = _get_unique_path(docs_dir / os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    return f"Moved document to '{destination_path.relative_to(home_dir)}'."

def handle_image(file_path: str) -> str:
    """Default handler for generic images."""
    home_dir = Path.home()
    pics_dir = home_dir / "Pictures"
    destination_path = _get_unique_path(pics_dir / os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    return f"Moved image to '{destination_path.relative_to(home_dir)}'."

def delete_junk_file(file_path: str, reason: str) -> str:
    """Deletes a file that is classified as temporary or junk."""
    try:
        os.remove(file_path)
        return f"Deleted junk file '{os.path.basename(file_path)}'. Reason: {reason}"
    except Exception as e:
        return f"Error deleting junk file '{os.path.basename(file_path)}': {e}"