# commands/agent_verifier.py
import os
import shlex

def _verify_file_op(args: dict) -> tuple[float, str]:
    """Verifies arguments for file operations."""
    path = args.get('source_path') or args.get('current_path') or args.get('file_path')
    if not path:
        return (0.1, "Path argument is missing.")
    if not os.path.exists(path):
        return (0.3, f"The source file or directory '{path}' does not exist.")
    return (1.0, "Source path exists.")

def _verify_shell_command(args: dict) -> tuple[float, str]:
    """Verifies shell commands for obvious risks."""
    command = args.get('command', '').lower()
    # Simple check for potentially destructive commands
    dangerous_keywords = ['rm -rf', 'format', 'del /s', '> /dev/sda']
    if any(keyword in command for keyword in dangerous_keywords):
        return (0.1, "Command is potentially highly destructive.")
    try:
        shlex.split(command)
    except ValueError:
        return (0.2, "Command has unbalanced quotes or is malformed.")
    return (1.0, "Command seems syntactically valid.")

# The main verification dispatcher
def verify_action(tool_name: str, tool_args: dict) -> tuple[float, str]:
    """
    Dispatches to the correct verifier based on the tool name and returns a score and rationale.
    Score ranges from 0.0 (fail) to 1.0 (pass).
    """
    verification_map = {
        'move_file': _verify_file_op,
        'rename_file': _verify_file_op,
        'delete_junk_file': _verify_file_op,
        'read_pdf_content': _verify_file_op,
        'read_docx_content': _verify_file_op,
        'analyze_image_content': _verify_file_op,
        'execute_shell_command': _verify_shell_command,
    }

    verifier_func = verification_map.get(tool_name)

    if verifier_func:
        return verifier_func(tool_args)
    else:
        # Default for tools without specific verification
        return (0.9, "No specific verifier for this tool; assuming arguments are valid.")