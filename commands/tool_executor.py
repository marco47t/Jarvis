# commands/tool_executor.py
import json
from typing import Dict, Callable, Any
from pydantic import BaseModel, ValidationError

def execute_tool(
    tool_func: Callable[..., Any], 
    args_model: BaseModel, 
    raw_args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    A robust tool executor that validates arguments and standardizes output.

    1. Validates `raw_args` against the provided Pydantic `args_model`.
    2. If valid, executes the `tool_func` with the validated arguments.
    3. If invalid, returns a structured validation error.
    4. Wraps the result (success or failure) in a standardized dictionary.
    """
    try:
        # Step 1: Validate arguments using the Pydantic model
        validated_args = args_model(**raw_args)

        # Step 2: Execute the tool with the validated, typed arguments
        result_data = tool_func(**validated_args.model_dump())

        # Step 3: Wrap successful output in the standard format
        return {
            "status": "ok",
            "data": result_data
        }

    except ValidationError as e:
        # Handle Pydantic validation errors (e.g., missing required arg, wrong type)
        return {
            "status": "error",
            "error_code": "validation_error",
            "message": "Tool arguments are invalid.",
            "details": json.loads(e.json()) # Pydantic provides detailed error JSON
        }
        
    except Exception as e:
        # Handle any other exceptions that occur during the tool's execution
        return {
            "status": "error",
            "error_code": type(e).__name__,
            "message": f"An unexpected error occurred during tool execution: {str(e)}",
            "details": None
        }