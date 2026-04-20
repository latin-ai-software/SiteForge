import threading
import time
from updater.updater import auto_update

def start_update_loop():
    def loop():
        while True:
            print("[Updater] Checking for updates...")
            print("[Updater]", auto_update())
            time.sleep(3600)  # jede Stunde

    t = threading.Thread(target=loop, daemon=True)
    t.start()
