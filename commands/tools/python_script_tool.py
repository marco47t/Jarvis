# commands/tools/python_script_tool.py
import subprocess
import tempfile
import os
import logging
import ast
from ..dynamic_tool_manager import register_dynamic_tool

logger = logging.getLogger(__name__)

def execute_generated_python_script(code: str, reason: str) -> str:
    """
    Executes a string of Python code provided by the AI.
    The code is saved to a temporary file and run in a separate process.
    The 'reason' argument is crucial for the user to understand the script's purpose.

    Args:
        code (str): The Python code to be executed.
        reason (str): A short, clear explanation of what the script is intended to do.

    Returns:
        str: The standard output and standard error from the script's execution.
    """
    if not code:
        return "Error: No Python code was provided to execute."
        
    logger.info(f"Attempting to execute AI-generated Python script. Reason: {reason}")
    
    # Use a temporary file to store and execute the code
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(code)
            script_path = tmp_file.name

        logger.info(f"Generated script saved to temporary file: {script_path}")

        # Execute the script using a subprocess to isolate it
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='ignore'
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode == 0:
            logger.info(f"Generated script executed successfully.")
            response = f"Script executed successfully.\nOutput:\n{output}" if output else "Script executed successfully with no output."
        else:
            logger.error(f"Generated script failed with exit code {result.returncode}.\nError: {error}")
            response = f"Script failed with exit code {result.returncode}.\nError:\n{error}\nOutput:\n{output}"
        
        return response

    except Exception as e:
        logger.error(f"An unexpected error occurred while executing the generated script: {e}")
        return f"An unexpected error occurred during script execution: {e}"
    finally:
        # Clean up the temporary file
        if 'script_path' in locals() and os.path.exists(script_path):
            os.remove(script_path)
            logger.info(f"Cleaned up temporary script file: {script_path}")




def create_new_tool(tool_name: str, python_code: str, description: str) -> str:
    """
    Creates a new tool available for the agent to use in the current session.
    The code must be a single function with type hints for all arguments.
    ...
    """
    logger.info(f"Attempting to create a new dynamic tool: '{tool_name}'")
    try:
        # ... (AST parsing and code compilation logic remains the same) ...
        tree = ast.parse(python_code)
        
        if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
            return "Error: The provided code must contain exactly one function definition."
        
        func_def = tree.body[0]
        if func_def.name != tool_name:
            return f"Error: The function name in the code ('{func_def.name}') must match the tool_name ('{tool_name}')."
            
        exec_namespace = {}
        compiled_code = compile(tree, filename="<dynamic_tool>", mode="exec")
        exec(compiled_code, exec_namespace)
        
        new_tool_func = exec_namespace.get(tool_name)
        if not callable(new_tool_func):
            return "Error: Could not find a callable function in the executed code."
        
        # --- THIS IS THE CHANGE ---
        # The function call no longer needs the 'arg_schema'
        if register_dynamic_tool(tool_name, new_tool_func, description):
            return f"Tool '{tool_name}' was created successfully and is now available for use in this session."
        else:
            return f"Failed to register the new tool '{tool_name}' due to an internal error."

    except SyntaxError as e:
        return f"Syntax Error in provided Python code: {e}"
    except Exception as e:
        logger.error(f"Critical error creating dynamic tool '{tool_name}': {e}", exc_info=True)
        return f"An unexpected error occurred during tool creation: {e}"