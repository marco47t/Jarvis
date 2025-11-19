# commands/file_organizer.py
import os
import shutil
import re
import time
from pathlib import Path
import datetime
import docx
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

def move_file(source_path: str, destination_folder: str, dry_run: bool = False) -> str:
    """
    Moves a file from a source path to a destination folder.
    This tool is for moving to specific, user-defined locations.

    Args:
        source_path (str): The full path of the file to move.
        destination_folder (str): The full path of the folder to move the file into.
        dry_run (bool): If True, describes the action without executing it.
    
    Returns:
        str: A confirmation message or an error.
    """
    if dry_run:
        return f"[DRY RUN] Would move file '{os.path.basename(source_path)}' to folder '{destination_folder}'."
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

def rename_file(current_path: str, new_name: str, dry_run: bool = False) -> str:
    """
    Renames a file. The new name should include the extension.

    Args:
        current_path (str): The full path of the file to rename.
        new_name (str): The new name for the file (e.g., 'new_icon.ico').
        dry_run (bool): If True, describes the action without executing it.

    Returns:
        str: A confirmation message or an error.
    """
    if dry_run:
        return f"[DRY RUN] Would rename file '{os.path.basename(current_path)}' to '{new_name}'."
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

def handle_invoice(file_path: str, company: str, date: str, amount: str = None, dry_run: bool = False) -> str:
    """Handles files classified as invoices. Renames and moves them to a structured folder."""
    home_dir = Path.home()
    invoices_dir = home_dir / "Documents" / "Invoices"
    company_dir = invoices_dir / (company.strip() if company else "Unspecified")
    
    date_str = date.strip() if date else datetime.date.today().strftime('%Y-%m-%d')
    new_filename = f"{date_str}_{company}_Invoice.pdf"
    destination_path = company_dir / new_filename
    
    if dry_run:
        return f"[DRY RUN] Would file invoice from {company} to '{destination_path.relative_to(home_dir)}'."

    company_dir.mkdir(parents=True, exist_ok=True)
    final_destination_path = _get_unique_path(destination_path)
    shutil.move(file_path, final_destination_path)
    return f"Filed invoice from {company} to '{final_destination_path.relative_to(home_dir)}'."

def handle_screenshot(file_path: str, subject: str, dry_run: bool = False) -> str:
    """
    Handles screenshots. Renames them based on a subject and moves them.
    Category: File Ops
    """
    home_dir = Path.home()
    screenshots_dir = home_dir / "Pictures" / "Screenshots"
    
    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y%m%d_%H%M%S')
    subject_str = re.sub(r'[^\w\-_\. ]', '_', subject.strip()) # Sanitize subject
    new_filename = f"Screenshot_{timestamp}_{subject_str}.png"
    destination_path = screenshots_dir / new_filename
    
    if dry_run:
        return f"[DRY RUN] Would save screenshot about '{subject}' to '{destination_path.relative_to(home_dir)}'."

    screenshots_dir.mkdir(parents=True, exist_ok=True)
    final_destination_path = _get_unique_path(destination_path)
    shutil.move(file_path, final_destination_path)
    return f"Saved screenshot about '{subject}' to '{final_destination_path.relative_to(home_dir)}'."

def handle_project_asset(file_path: str, project_name: str, asset_type: str, dry_run: bool = False) -> str:
    """
    Handles project-related assets like images, docs, or code.
    Category: File Ops
    """
    home_dir = Path.home()
    projects_dir = home_dir / "Documents" / "Projects"
    project_dir = projects_dir / (project_name.strip() if project_name else "General Project")
    asset_dir = project_dir / (asset_type.strip().capitalize() if asset_type else "Assets")
    
    destination_path = asset_dir / os.path.basename(file_path)
    
    if dry_run:
        return f"[DRY RUN] Would move project asset for '{project_name}' to '{destination_path.relative_to(home_dir)}'."

    asset_dir.mkdir(parents=True, exist_ok=True)
    final_destination_path = _get_unique_path(destination_path)
    shutil.move(file_path, final_destination_path)
    return f"Moved project asset for '{project_name}' to '{final_destination_path.relative_to(home_dir)}'."

def handle_generic_document(file_path: str, dry_run: bool = False) -> str:
    """
    Default handler for generic documents.
    Category: File Ops
    """
    home_dir = Path.home()
    docs_dir = home_dir / "Documents"
    destination_path = docs_dir / os.path.basename(file_path)

    if dry_run:
        return f"[DRY RUN] Would move document to '{destination_path.relative_to(home_dir)}'."
        
    final_destination_path = _get_unique_path(destination_path)
    shutil.move(file_path, final_destination_path)
    return f"Moved document to '{final_destination_path.relative_to(home_dir)}'."

def handle_image(file_path: str, dry_run: bool = False) -> str:
    """
    Default handler for generic images.
    Category: File Ops
    """
    home_dir = Path.home()
    pics_dir = home_dir / "Pictures"
    destination_path = pics_dir / os.path.basename(file_path)

    if dry_run:
        return f"[DRY RUN] Would move image to '{destination_path.relative_to(home_dir)}'."

    final_destination_path = _get_unique_path(destination_path)
    shutil.move(file_path, final_destination_path)
    return f"Moved image to '{final_destination_path.relative_to(home_dir)}'."

def delete_junk_file(file_path: str, reason: str, dry_run: bool = False) -> str:
    """
    Deletes a file that is classified as temporary or junk.
    Category: File Ops
    """
    if dry_run:
        return f"[DRY RUN] Would delete junk file '{os.path.basename(file_path)}'. Reason: {reason}"
    try:
        os.remove(file_path)
        return f"Deleted junk file '{os.path.basename(file_path)}'. Reason: {reason}"
    except Exception as e:
        return f"Error deleting junk file '{os.path.basename(file_path)}': {e}"
    

def create_document(filename: str, content: str, folder_path: str = "Desktop") -> str:
    """
    Creates a new .docx document with specified content in a given folder.

    Args:
        filename (str): The name of the file to create (e.g., 'My Report.docx'). Must end in .docx.
        content (str): The text content to write into the document.
        folder_path (str): The folder to save the document in. Can be a full path or a relative name like 'Desktop' or 'Documents'.
    
    Returns:
        str: Confirmation message with the full path of the created document.
    """
    try:
        # Resolve common folder names to full paths
        home_dir = Path.home()
        if folder_path.lower() == "desktop":
            target_dir = home_dir / "Desktop"
        elif folder_path.lower() == "documents":
            target_dir = home_dir / "Documents"
        else:
            target_dir = Path(folder_path)

        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename.lower().endswith('.docx'):
            filename += '.docx'

        final_path = _get_unique_path(target_dir / filename)
        
        doc = docx.Document()
        doc.add_paragraph(content)
        doc.save(final_path)
        
        return f"Successfully created document at '{final_path}'."
    except Exception as e:
        return f"Error creating document: {e}"