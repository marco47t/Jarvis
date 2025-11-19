# commands/agent_historian.py
import json
import os
from collections import deque
from config import DATA_DIR, HISTORY_RECORDS_TO_CONSIDER

LOG_FILE_PATH = os.path.join(DATA_DIR, 'transaction_log.jsonl')

def get_historical_confidence(tool_name: str) -> float:
    """
    Calculates the recent success rate of a given tool from the transaction log.
    Returns a confidence score between 0.0 and 1.0.
    """
    if not os.path.exists(LOG_FILE_PATH):
        return 0.8 # Default confidence for a tool that has never been run

    relevant_records = []
    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            # Efficiently read the last N lines for performance
            # For simplicity here, we read all and filter, but a deque is more robust.
            lines = f.readlines()
            for line in reversed(lines):
                if len(relevant_records) >= HISTORY_RECORDS_TO_CONSIDER:
                    break
                try:
                    record = json.loads(line)
                    if record.get('tool_name') == tool_name:
                        relevant_records.append(record)
                except json.JSONDecodeError:
                    continue # Skip corrupted lines
    except IOError:
        return 0.7 # Return neutral confidence if log is unreadable

    if not relevant_records:
        return 0.8 # Default confidence if this specific tool has no history

    successes = sum(1 for r in relevant_records if r.get('success', False))
    total = len(relevant_records)
    
    success_rate = successes / total if total > 0 else 0.8
    
    # Apply a curve to be more conservative. A 50% success rate should not be 0.5 confidence.
    # We can use a simple power function to make the score lower for mediocre rates.
    conservative_score = success_rate ** 1.5 

    return conservative_score