# commands/dynamic_tool_manager.py
import logging
import inspect # <--- NEW IMPORT
from typing import Dict, Any, Callable
from pydantic import create_model, Field

logger = logging.getLogger(__name__)

DYNAMIC_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register_dynamic_tool(
    tool_name: str,
    tool_function: Callable,
    description: str
    # We will now generate the schema from the function itself
):
    """
    Creates a Pydantic model from a function's type hints and registers the new tool.
    
    Args:
        tool_name (str): The name for the new tool.
        tool_function (Callable): The compiled Python function for the tool.
        description (str): A description of what the tool does.
    """
    try:
        # --- THIS IS THE NEW, ROBUST LOGIC ---
        sig = inspect.signature(tool_function)
        fields = {}
        for param in sig.parameters.values():
            # If the parameter has a type annotation and a default value
            if param.annotation != inspect.Parameter.empty and param.default != inspect.Parameter.empty:
                fields[param.name] = (param.annotation, param.default)
            # If it has a type annotation but no default (it's required)
            elif param.annotation != inspect.Parameter.empty:
                fields[param.name] = (param.annotation, ...) # Ellipsis (...) means required
            # Fallback for untyped parameters (less ideal)
            else:
                fields[param.name] = (str, ...) # Assume string if no type hint
        # --- END OF NEW LOGIC ---

        # Use Pydantic's create_model to build the arguments model dynamically
        DynamicArgsModel = create_model(
            f"{tool_name.capitalize()}Args",
            __doc__=description,
            **fields
        )
        
        DYNAMIC_TOOL_REGISTRY[tool_name] = {
            "function": tool_function,
            "args_model": DynamicArgsModel,
            "category": "Dynamic"
        }
        logger.info(f"Successfully registered dynamic tool: '{tool_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to register dynamic tool '{tool_name}': {e}", exc_info=True)
        return False