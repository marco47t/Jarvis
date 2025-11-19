# commands/tools/python_script_tool.py
import subprocess
import tempfile
import os
import logging
import ast
import traceback
from ..dynamic_tool_manager import register_dynamic_tool

logger = logging.getLogger(__name__)

def execute_generated_python_script(code: str, reason: str, max_retries: int = 3) -> str:
    """
    Executes AI-generated Python code with automatic debugging and retry logic.
    If the script fails, it analyzes the error and attempts to fix it automatically.
    
    Args:
        code (str): The Python code to execute
        reason (str): Explanation of what the script does
        max_retries (int): Maximum number of self-debugging attempts (default: 3)
    
    Returns:
        str: Execution result, output, or detailed error information
    """
    if not code:
        return "Error: No Python code was provided to execute."
        
    logger.info(f"Executing AI-generated Python script. Reason: {reason}")
    
    attempt = 0
    current_code = code
    error_history = []
    
    while attempt < max_retries:
        attempt += 1
        logger.info(f"Execution attempt {attempt}/{max_retries}")
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(current_code)
                script_path = tmp_file.name

            logger.info(f"Script saved to: {script_path}")

            # Execute the script
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                errors='ignore',
                timeout=30  # 30 second timeout
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()

            # Success case
            if result.returncode == 0:
                logger.info(f"Script executed successfully on attempt {attempt}")
                success_msg = f"Script executed successfully."
                if attempt > 1:
                    success_msg += f" (Fixed after {attempt-1} debugging attempts)"
                if output:
                    success_msg += f"\n\nOutput:\n{output}"
                return success_msg
            
            # Failure case - prepare for debugging
            error_history.append({
                'attempt': attempt,
                'error': error,
                'code': current_code
            })
            
            logger.error(f"Script failed on attempt {attempt}. Error: {error}")
            
            # If max retries reached, return detailed error
            if attempt >= max_retries:
                return (
                    f"Script failed after {max_retries} attempts.\n\n"
                    f"Final Error:\n{error}\n\n"
                    f"Output:\n{output}\n\n"
                    f"The script could not be automatically debugged. "
                    f"Please review the error and provide corrections."
                )
            
            # Attempt auto-fix (will be handled by agent)
            return (
                f"Script execution failed (attempt {attempt}/{max_retries}).\n\n"
                f"Error:\n{error}\n\n"
                f"Output:\n{output}\n\n"
                f"SELF_DEBUG_REQUEST: Please analyze this error and provide a corrected version of the script."
            )

        except subprocess.TimeoutExpired:
            return f"Script execution timed out after 30 seconds. The script may have an infinite loop."
        except Exception as e:
            logger.error(f"Unexpected error during script execution: {e}")
            return f"Unexpected error during script execution: {e}\n{traceback.format_exc()}"
        finally:
            if 'script_path' in locals() and os.path.exists(script_path):
                os.remove(script_path)
                logger.info(f"Cleaned up temporary script: {script_path}")


def create_new_tool(tool_name: str, python_code: str, description: str) -> str:
    """
    Creates a new dynamic tool for the current session.
    The code must be a single function with type hints.
    
    Args:
        tool_name (str): Name of the new tool
        python_code (str): Complete Python function code
        description (str): What the tool does
    
    Returns:
        str: Success/failure message
    """
    logger.info(f"Creating dynamic tool: '{tool_name}'")
    
    try:
        tree = ast.parse(python_code)
        
        if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
            return "Error: Code must contain exactly one function definition."
        
        func_def = tree.body[0]
        if func_def.name != tool_name:
            return f"Error: Function name '{func_def.name}' must match tool_name '{tool_name}'."
            
        exec_namespace = {}
        compiled_code = compile(tree, filename="<dynamic_tool>", mode="exec")
        exec(compiled_code, exec_namespace)
        
        new_tool_func = exec_namespace.get(tool_name)
        if not callable(new_tool_func):
            return "Error: Could not find callable function in code."
        
        if register_dynamic_tool(tool_name, new_tool_func, description):
            return f"Tool '{tool_name}' created successfully and available for use."
        else:
            return f"Failed to register tool '{tool_name}'."

    except SyntaxError as e:
        return f"Syntax Error in Python code: {e}"
    except Exception as e:
        logger.error(f"Error creating tool '{tool_name}': {e}", exc_info=True)
        return f"Unexpected error during tool creation: {e}"
