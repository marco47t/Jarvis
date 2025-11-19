# commands/backup_tools.py
import os
import shutil
import logging
from datetime import datetime
from config import ENABLE_LOGGING, LOG_FILE

# --- Logger Setup ---
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

def create_project_backup(source_path: str = None) -> str:
    """Creates a timestamped zip backup of a source folder.

    If 'source_path' is not provided, it defaults to the current project directory.
    The backup file is saved in the parent directory of the source folder.
    
    Args:
        source_path (str, optional): The path to the folder to back up. Defaults to the current project directory.

    Returns:
        str: A message indicating success or failure and the path to the backup file.
    """
    try:
        # Determine the source directory to back up
        if source_path:
            # Use the provided path, making it absolute
            source_dir = os.path.abspath(source_path)
        else:
            # Default to the current working directory (project root)
            source_dir = os.getcwd()
            logger.info(f"No source path provided. Defaulting to current project directory: {source_dir}")

        # Validate that the source directory exists
        if not os.path.isdir(source_dir):
            error_msg = f"Error: The specified source directory does not exist: '{source_dir}'"
            logger.error(error_msg)
            return error_msg

        # Determine the destination for the backup file (parent directory of the source)
        destination_dir = os.path.dirname(source_dir)
        
        # Get the name of the folder being backed up
        source_folder_name = os.path.basename(source_dir)

        # Create a timestamp for the backup file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Define the backup filename
        backup_filename_base = f"{source_folder_name}_backup_{timestamp}"
        
        # The full path for the archive to be created (without extension)
        archive_path_base = os.path.join(destination_dir, backup_filename_base)

        logger.info(f"Starting backup of '{source_dir}' to '{archive_path_base}.zip'")

        # Create the zip archive
        # shutil.make_archive returns the full path to the created archive
        final_archive_path = shutil.make_archive(
            base_name=archive_path_base,
            format='zip',
            root_dir=source_dir
        )

        success_msg = f"Successfully created backup at: '{final_archive_path}'"
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"An unexpected error occurred during backup creation: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg