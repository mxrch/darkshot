import threading
import datetime
from termcolor import colored
from pathlib import Path

def log(text, timecode, cfg, level, hidden, debug):
    levels = {
        "INFO": {"degree": 10, "color": "white"},
        "INTERESTING": {"degree": 15, "color": "cyan"},
        "COOL": {"degree": 16, "color": "green"},
        "LILWARN": {"degree": 18, "color": "yellow"},
        "VALUABLE": {"degree": 20, "color": "cyan"},
        "GOOD": {"degree": 30, "color": "green"},
        "WARNING": {"degree": 40, "color": "yellow"},
        "ERROR": {"degree": 70, "color": "red"},
        "CRITICAL": {"degree": 90, "color": "magenta"}
        }

    if debug or (not debug and levels[level]["degree"] >= 20):
        th_name = threading.current_thread().name
        date = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")

        text = f"[{date}][{level}][{th_name}] {text}"

        # Save the log if it's above INFO level
        if levels[level]["degree"] >= 20 :
            path = Path(cfg["logs_dir"]) / (timecode + ".txt")
            with open(path, 'a') as f:
                f.write(text + "\n")

        # If debug mode, we print all apart "hidden" logs
        if debug and not hidden:
            text = colored(text, levels[level]["color"])
            print(text)