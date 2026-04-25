import os
import json
import time


class MediaManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.upload_dir = os.path.join(base_path, "data", "uploads")
        self.usage_file = os.path.join(base_path, "data", "media_usage.json")

        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        if not os.path.exists(os.path.dirname(self.usage_file)):
            os.makedirs(os.path.dirname(self.usage_file))

        if not os.path.exists(self.usage_file):
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    # ---------------------------------------------------------
    # INTERN
    # ---------------------------------------------------------

    def _load_usage(self):
        try:
            with open(self.usage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_usage(self, data):
        with open(self.usage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ---------------------------------------------------------
    # DATEILISTE + USAGE
    # ---------------------------------------------------------

    def get_usage_summary(self):
        usage = self._load_usage()
        files = []

        for filename in os.listdir(self.upload_dir):
            path = os.path.join(self.upload_dir, filename)

            if not os.path.isfile(path):
                continue

            size = os.path.getsize(path)
            ext = filename.split(".")[-1].lower() if "." in filename else ""

            files.append({
                "filename": filename,
                "path": path,
                "size": size,
                "usage_count": usage.get(filename, {}).get("count", 0),
                "is_image": ext in ["png", "jpg", "jpeg", "gif", "webp"],
                "is_video": ext in ["mp4", "mov", "webm"],
                "is_document": ext in ["pdf", "docx", "txt"]
            })

        return files

    # ---------------------------------------------------------
    # EINZELDATEI
    # ---------------------------------------------------------

    def get_file_info(self, filename):
        path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(path):
            return None

        usage = self._load_usage()
        size = os.path.getsize(path)
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        return {
            "filename": filename,
            "path": path,
            "size": size,
            "usage_count": usage.get(filename, {}).get("count", 0),
            "usage": usage.get(filename, {}).get("items", []),
            "is_image": ext in ["png", "jpg", "jpeg", "gif", "webp"],
            "is_video": ext in ["mp4", "mov", "webm"],
            "is_document": ext in ["pdf", "docx", "txt"]
        }

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_file(self, filename):
        path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(path):
            return False, "Datei existiert nicht"

        try:
            os.remove(path)
        except Exception as e:
            return False, f"Fehler beim Löschen: {e}"

        usage = self._load_usage()
        if filename in usage:
            usage.pop(filename)
            self._save_usage(usage)

        return True, "Datei gelöscht"

    # ---------------------------------------------------------
    # RENAME
    # ---------------------------------------------------------

    def rename_file(self, old_name, new_name):
        old_path = os.path.join(self.upload_dir, old_name)

        # Dateiendungen extrahieren
        old_ext = os.path.splitext(old_name)[1]  # z.B. ".png"
        new_ext = os.path.splitext(new_name)[1]  # z.B. ""

        # Wenn neue Endung fehlt oder anders ist → alte Endung anhängen
        if new_ext.lower() != old_ext.lower():
            new_name = new_name + old_ext

        new_path = os.path.join(self.upload_dir, new_name)

        if not os.path.exists(old_path):
            return False, "Datei existiert nicht"

        if os.path.exists(new_path):
            return False, "Eine Datei mit diesem Namen existiert bereits"

        try:
            os.rename(old_path, new_path)
        except Exception as e:
            return False, f"Fehler beim Umbenennen: {e}"

        self._update_usage_after_rename(old_name, new_name)

        return True, "Datei erfolgreich umbenannt"

    def _update_usage_after_rename(self, old, new):
        usage = self._load_usage()

        if old in usage:
            usage[new] = usage.pop(old)

        self._save_usage(usage)
