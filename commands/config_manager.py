# commands/config_manager.py
import re
import json
import os
from config import DATA_DIR

# --- Constants ---
CONFIG_FILE_PATH = 'config.py'
PROFILE_FILE_PATH = os.path.join(DATA_DIR, 'profile.json')

# --- Profile Management ---

def load_profile() -> dict:
    """
    Loads the user's profile data (name, photo) from a JSON file.
    Returns default values if the file doesn't exist.
    """
    if os.path.exists(PROFILE_FILE_PATH):
        try:
            with open(PROFILE_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupt or unreadable, return default
            pass 
    
    # Default profile data
    return {
        "name": "User",
        "photo_base64": None # We will store the image as a Base64 string
    }

def save_profile(profile_data: dict) -> bool:
    """
    Saves the user's profile data to a JSON file.
    If 'photo_base64' is not in the data, it leaves the existing one untouched.

    Args:
        profile_data (dict): A dictionary which can contain 'name' and/or 'photo_base64'.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        # Load existing data first to preserve fields that are not being updated
        current_profile = load_profile()
        
        # Update fields from the new data
        current_profile.update(profile_data)

        # If the new photo data is explicitly null, remove the key to avoid deleting it
        if 'photo_base64' in current_profile and current_profile['photo_base64'] is None:
            del current_profile['photo_base64']

        os.makedirs(os.path.dirname(PROFILE_FILE_PATH), exist_ok=True)
        with open(PROFILE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_profile, f, indent=2)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving profile: {e}")
        return False

# --- Configuration File Management ---

def get_config_values(keys: list) -> dict:
    """
    Reads the config.py file and extracts the current values for the given keys.

    Args:
        keys (list): A list of variable names to look for (e.g., ['GEMINI_API_KEY', 'AI_TEMPERATURE']).

    Returns:
        dict: A dictionary with the found keys and their values.
    """
    values = {}
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for key in keys:
            # This regex looks for a line starting with the key, followed by '=',
            # and captures the value, which can be in single/double quotes or be a number/boolean.
            # It correctly ignores commented-out lines.
            pattern = re.compile(rf"^{key}\s*=\s*['\"]?([^'\"\n#]+)['\"]?", re.MULTILINE)
            match = pattern.search(content)
            if match:
                values[key] = match.group(1).strip()
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE_PATH} not found.")
    except Exception as e:
        print(f"Error reading config values: {e}")
        
    return values

def update_config_value(key: str, value: any) -> bool:
    """
    Updates a single key-value pair in the config.py file.
    It preserves comments and formatting.

    Args:
        key (str): The variable name to update.
        value (any): The new value (can be str, int, float, bool).

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Determine how to format the value
        if isinstance(value, str):
            formatted_value = f'"{value}"'
        else: # For numbers, booleans etc.
            formatted_value = str(value)

        # Regex to find the variable assignment, ignoring comments
        pattern = re.compile(rf"^{key}\s*=")
        
        updated = False
        for i, line in enumerate(lines):
            if pattern.match(line):
                # Split the line at the comment, if any
                parts = line.split('#', 1)
                assignment_part = parts[0]
                comment_part = f" # {parts[1].strip()}" if len(parts) > 1 else ""
                
                # Reconstruct the line
                lines[i] = f"{key} = {formatted_value}{comment_part}\n"
                updated = True
                break
        
        if not updated:
            print(f"Warning: Key '{key}' not found in {CONFIG_FILE_PATH}. Cannot update.")
            return False

        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return True

    except Exception as e:
        print(f"Error updating config file: {e}")
        return False