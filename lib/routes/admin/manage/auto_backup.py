from lib.routes.admin.manage.backup import create_backup_file, cleanup_old_backups

if __name__ == "__main__":
    filename, path = create_backup_file()
    cleanup_old_backups(limit=10)
    print("Automatisches Backup erstellt:", filename)
