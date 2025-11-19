import json 
import os 
from datetime import datetime
from config import DATA_DIR

LOG_FILE_PATH = os.path.join(DATA_DIR, 'transaction_log.jsonl')

# --- MODIFIED FUNCTION SIGNATURE ---
def log_tool_execution(
    tool_name: str, 
    args: dict, 
    success: bool, 
    result: str, 
    error_trace: str = None,
    confidence_data: dict = None # <-- NEW
):
    """Appends a tool execution record to the transaction log."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'tool_name': tool_name,
        'parameters': args,
        'confidence': confidence_data or {}, # <-- NEW
        'success': success,
        'result': result,
        'error_feedback': error_trace
    }

    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"CRITICAL: Failed to write to transaction log: {e}")