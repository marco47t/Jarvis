# commands/tools/__init__.py
import os
import importlib
import inspect
from typing import Dict, Callable, Any

# This dictionary will store all dynamically loaded tools
ACTION_REGISTRY: Dict[str, Callable[..., Any]] = {}

def _load_tools():
    """
    Dynamically loads all Python modules in the current directory and extracts
    functions to populate the ACTION_REGISTRY.
    """
    tools_dir = os.path.dirname(__file__)
    
    # Iterate through all files in the directory
    for filename in os.listdir(tools_dir):
        # We only care about Python files that are not the __init__.py file
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f"commands.tools.{filename[:-3]}"
            
            try:
                # Import the module dynamically
                module = importlib.import_module(module_name)
                
                # Iterate over members of the imported module
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    # We only register functions that are not internal (e.g., do not start with '_')
                    if not name.startswith('_'):
                        ACTION_REGISTRY[name] = func
                        
                print(f"Loaded tools from module: {module_name}")

            except Exception as e:
                # Log an error if a tool module fails to load
                print(f"ERROR: Failed to load tools from {filename}: {e}")

# Call the loading function immediately when the package is imported
_load_tools()

# Re-export the registry so it can be imported from commands.tools
__all__ = ['ACTION_REGISTRY']