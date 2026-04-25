CODE_FOLDERS = ["lib", "plugins", "static", "templates", "updater"]

def apply_update():
    # Backup nur der Code-Ordner
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR)

    for folder in CODE_FOLDERS:
        src = os.path.join(APP_DIR, folder)
        dst = os.path.join(BACKUP_DIR, folder)
        if os.path.exists(src):
            shutil.move(src, dst)

    # Neue Version einspielen
    for folder in CODE_FOLDERS:
        src = os.path.join(UPDATE_DIR, folder)
        dst = os.path.join(APP_DIR, folder)
        if os.path.exists(src):
            shutil.move(src, dst)

    # app.py ersetzen
    if os.path.exists(os.path.join(UPDATE_DIR, "app.py")):
        shutil.move(os.path.join(UPDATE_DIR, "app.py"), os.path.join(APP_DIR, "app.py"))
