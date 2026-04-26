import os

THEME_FILE = "data/settings/active_theme.txt"

def get_theme():
    if not os.path.exists(THEME_FILE):
        return "theme.css"
    with open(THEME_FILE, "r") as f:
        return f.read().strip()

def set_theme(theme_name):
    os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
    with open(THEME_FILE, "w") as f:
        f.write(theme_name)
