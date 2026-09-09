import requests
import os
import json
def auto_update():
    """Check for updates and apply if available"""
    try:
        # Load config
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/updater/config.json", "r") as f:
            config = json.load(f)
        
        # Determine which version URL to use. If this installation is marked
        # as a dev build (`dev_mode` true) and a `dev_version_url` is supplied,
        # prefer that so dev instances compare against the dev channel.
        dev_mode = bool(config.get("dev_mode", False))
        version_url = None
        if dev_mode and config.get("dev_version_url"):
            version_url = config.get("dev_version_url")
        else:
            version_url = config.get("version_url")

        if not version_url:
            return "No version URL configured"
        
        # Get current version (ignore comment lines and blank lines)
        current_version = None
        local_version_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/updater/version.txt"
        if os.path.exists(local_version_path):
            with open(local_version_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s:
                        continue
                    if s.startswith("#"):
                        continue
                    current_version = s
                    break
        
        # Fetch latest version from the selected channel
        try:
            response = requests.get(version_url, timeout=10)
        except Exception as exc:
            return f"Failed to check for updates: {exc}"

        if response.status_code != 200:
            return f"Failed to check for updates: {response.status_code}"

        # Parse fetched content and ignore comment lines (server may append a
        # timestamp/comment after the build id). Use the first non-empty,
        # non-comment line as the canonical version string.
        latest_version = None
        for line in response.text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                continue
            latest_version = s
            break
        if latest_version is None:
            latest_version = response.text.strip()
        print(f"Current version: {current_version}, Latest version: {latest_version}")
        if current_version == latest_version:
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/version.json", "w") as f:
                json.dump({"requires_update": False, "latest_version": latest_version, "current_version": latest_version}, f)
            return "Already up to date"
        
        # Download and apply update (this is a placeholder - implement actual update logic)
        # For example, you could download a zip file, extract it, and replace files
        # Make sure to handle this carefully to avoid breaking the installation
        
        # After successful update, write the new version to version.txt
        # with open("version.txt", "w") as f:
        #     f.write(latest_version)

        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/version.json", "w") as f:
            json.dump({"requires_update": True, "latest_version": latest_version, "current_version": current_version}, f)
        
        return f"Done"
    
    except Exception as e:
        return f"Error during update: {str(e)}"