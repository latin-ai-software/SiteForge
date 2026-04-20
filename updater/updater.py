import requests
import zipfile
import os
import shutil
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_DIR = BASE_DIR
UPDATE_DIR = os.path.join(BASE_DIR, "update_test")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")

CONFIG_FILE = os.path.join(BASE_DIR, "updater/config.json")
VERSION_FILE = os.path.join(BASE_DIR, "updater/version.txt")


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_current_version():
    if not os.path.exists(VERSION_FILE):
        return "0.0.0"
    return open(VERSION_FILE).read().strip()


def check_for_update():
    cfg = load_config()
    remote = requests.get(cfg["version_url"]).json()
    current = get_current_version()

    if remote["version"] > current:
        return remote
    return None


def download_update(url):
    zip_path = os.path.join(BASE_DIR, "update.zip")
    with requests.get(url, stream=True) as r:
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return zip_path


def extract_update(zip_path):
    if os.path.exists(UPDATE_DIR):
        shutil.rmtree(UPDATE_DIR)
    os.makedirs(UPDATE_DIR)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(UPDATE_DIR)


def run_healthcheck():
    try:
        result = subprocess.check_output(
            ["python3", os.path.join(UPDATE_DIR, "updater/healthcheck.py")],
            stderr=subprocess.STDOUT,
            timeout=5
        )
        return result.decode().strip() == "OK"
    except:
        return False


def apply_update():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)

    shutil.move(APP_DIR, BACKUP_DIR)
    shutil.move(UPDATE_DIR, APP_DIR)


def rollback():
    if os.path.exists(BACKUP_DIR):
        if os.path.exists(APP_DIR):
            shutil.rmtree(APP_DIR)
        shutil.move(BACKUP_DIR, APP_DIR)


def auto_update():
    update = check_for_update()
    if not update:
        return "No update available"

    zip_path = download_update(update["download"])
    extract_update(zip_path)

    if run_healthcheck():
        apply_update()
        return "Update successful"
    else:
        rollback()
        return "Update failed — rollback applied"
