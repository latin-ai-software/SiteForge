"""
License validation check - runs at module import time.
This file is imported by app.py before any other code executes,
ensuring the license is validated before the application can start.

Users cannot bypass this by commenting out code, as the check
runs during Python's import phase and terminates the process
if the license is invalid.
"""
import sys
import os
import requests


def _read_license_key(base_dir):
    """Read license key from file."""
    license_file = os.path.join(base_dir, "data", "license.txt")
    if not os.path.exists(license_file):
        raise FileNotFoundError("license.txt not found")
    with open(license_file, "r") as f:
        return f.read().strip()


def _is_license_valid(license_key):
    """Validate license key against remote gateway."""
    url = f"https://latinai.ch/wp-json/shoplicensegateway/license/validate/SF/{license_key}"
    try:
        response = requests.get(url, timeout=5)
    except Exception:
        return False
    
    try:
        data = response.json()
    except ValueError:
        return False
    
    return data.get("status") == "valid"


def _validate_license():
    """Validate license and terminate if invalid.
    
    This runs at module import time, before any application code executes.
    Terminating here prevents any bypasses via code modifications.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        license_key = _read_license_key(base_dir)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if not _is_license_valid(license_key):
        print("❌ Lizenz ungültig — Anwendung wird beendet.")
        sys.exit(1)
    
    print("✔ Lizenz gültig — Anwendung startet.")


# Run validation at import time - this cannot be bypassed
_validate_license()
