import os
import sys
import threading
import time
from updater.updater import auto_update


def _is_pytest_running():
    return os.environ.get("PYTEST_CURRENT_TEST") is not None or "pytest" in sys.modules or os.environ.get("CI", "").lower() == "true"


def start_update_loop():
    if _is_pytest_running():
        return

    def loop():
        while True:
            print("[Updater] Checking for updates...")
            print("[Updater]", auto_update())
            time.sleep(3600)  # jede Stunde

    t = threading.Thread(target=loop, daemon=True)
    t.start()
