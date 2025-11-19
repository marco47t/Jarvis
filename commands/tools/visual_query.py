# commands/visual_query.py

import tkinter as tk
from mss import mss
from PIL import Image
import base64
import io
import threading
import eel
import multiprocessing

def _run_selector_in_process(queue):
    """
    This function runs in a completely separate process.
    It creates the tkinter overlay and puts the result in the shared queue.
    """
    try:
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-alpha", 0.3)
        root.wait_visibility(root)
        root.wm_attributes('-topmost', 1)
        root.configure(bg='black')

        canvas = tk.Canvas(root, cursor="cross", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        selection_box = {}
        rect = None

        def on_mouse_press(event):
            nonlocal rect
            selection_box['start_x'] = canvas.winfo_pointerx()
            selection_box['start_y'] = canvas.winfo_pointery()
            rect = canvas.create_rectangle(0, 0, 0, 0, outline='cyan', width=2, fill=None)

        def on_mouse_drag(event):
            if rect:
                cur_x = canvas.winfo_pointerx()
                cur_y = canvas.winfo_pointery()
                canvas.coords(rect, selection_box['start_x'], selection_box['start_y'], cur_x, cur_y)

        def on_mouse_release(event):
            end_x = canvas.winfo_pointerx()
            end_y = canvas.winfo_pointery()
            
            left = min(selection_box['start_x'], end_x)
            top = min(selection_box['start_y'], end_y)
            right = max(selection_box['start_x'], end_x)
            bottom = max(selection_box['start_y'], end_y)

            if right - left > 10 and bottom - top > 10:
                final_selection = {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}
                queue.put(final_selection) # Put the successful selection in the queue
            
            root.quit()

        canvas.bind("<ButtonPress-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)
        root.bind("<Escape>", lambda e: root.quit())

        root.mainloop()
        root.destroy()
    except Exception as e:
        # If there's an error, we can log it or put an error message in the queue
        queue.put({"error": str(e)})


def capture_and_prompt():
    """
    Handles the entire process: run selector in a process, get result from queue,
    capture image, and call JS to show a centered prompt.
    """
    # Use a queue to get data back from the separate process
    queue = multiprocessing.Queue()
    
    # Create and start the process
    selector_process = multiprocessing.Process(target=_run_selector_in_process, args=(queue,))
    selector_process.start()
    selector_process.join() # Wait for the user to make a selection

    # Get the selection from the queue
    selection = queue.get()

    if selection and "error" not in selection:
        try:
            with mss() as sct:
                img = sct.grab(selection)
            
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            buffered = io.BytesIO()
            pil_img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # We no longer pass coordinates, JS will handle centering
            eel.showVisualQueryPrompt(img_base64)
            
        except Exception as e:
            print(f"Error during capture or encoding: {e}")

def trigger_visual_query():
    """
    Starts the visual query process in a non-blocking thread
    which in turn manages the blocking selector process.
    """
    # Necessary to run the process management in a thread to not freeze the main Eel UI
    query_thread = threading.Thread(target=capture_and_prompt)
    query_thread.start()