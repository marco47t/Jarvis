# commands/system_info_tools.py

import platform
import psutil # You will need to run: pip install psutil
import json
import time

def get_system_information() -> str:
    """
    Retrieves key system hardware and OS information.
    
    Returns:
        str: A JSON string containing system information.
    """
    try:
        uname = platform.uname()
        cpu_freq = psutil.cpu_freq()
        svmem = psutil.virtual_memory()

        info = {
            "System": f"{uname.system} {uname.release}",
            "Node Name": uname.node,
            "Processor": uname.processor,
            "CPU Cores": f"{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical",
            "Max CPU Frequency": f"{cpu_freq.max:.2f} Mhz" if cpu_freq else "N/A",
            "Total RAM": f"{svmem.total / (1024**3):.2f} GB",
            "Available RAM": f"{svmem.available / (1024**3):.2f} GB",
            "RAM Usage": f"{svmem.percent}%"
        }
        return json.dumps(info, indent=4)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=4)

def get_process_list(limit: int = 15) -> str:
    """
    Retrieves a list of the top running processes sorted by memory usage.
    This function is cross-platform and uses psutil instead of shell commands.

    Args:
        limit (int): The number of top processes to return.

    Returns:
        str: A JSON string containing the list of processes.
    """
    try:
        processes = []
        # Get all running processes with desired attributes
        procs = [p for p in psutil.process_iter(['pid', 'name', 'username', 'memory_percent'])]
        
        # To get a meaningful CPU %, we need to measure over a short interval
        for p in procs:
            try:
                p.cpu_percent(interval=0.01)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        time.sleep(0.1) # Wait a bit for the interval to pass

        for p in procs:
            try:
                pinfo = p.info
                # Get the CPU percent over the interval since the first call
                pinfo['cpu_percent'] = p.cpu_percent()
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by memory usage in descending order
        processes = sorted(processes, key=lambda p: p.get('memory_percent', 0), reverse=True)
        
        # Format the top processes for clear output
        top_processes = [
            {
                "pid": p['pid'],
                "name": p['name'],
                "user": p.get('username', 'N/A'),
                "cpu_percent": f"{p.get('cpu_percent', 0.0):.2f}%",
                "memory_percent": f"{p.get('memory_percent', 0.0):.2f}%"
            }
            for p in processes[:limit]
        ]

        return json.dumps(top_processes, indent=4)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=4)