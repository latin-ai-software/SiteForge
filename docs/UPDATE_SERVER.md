Update server and CI publishing

Server
------
1. Install dependencies (Flask):

```bash
python3 -m venv /opt/update-server-venv
source /opt/update-server-venv/bin/activate
pip install flask
```

2. Configure env and run (production: use gunicorn/systemd):

```bash
export UPDATE_API_KEY="<your-secret>"
export UPDATE_ROOT="/var/www/html/latinmagazine/update"
python tools/update_server.py
```

CI publishing
-------------
Set two CI variables in GitLab: `UPDATE_SERVER_URL` and `UPDATE_API_KEY`.
The pipeline job `publish_build` runs only on `main` and will generate the
build id and POST it to the server.

Git hooks (optional)
--------------------
Enable the bundled pre-commit hook so the build id is generated automatically
before each commit:

```bash
git config core.hooksPath .githooks
```

This hook runs `scripts/generate_build_id.py` and stages `updater/version.txt`
and `data/build_info.json` so the commit contains the build id.
