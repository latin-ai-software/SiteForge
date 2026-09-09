#!/usr/bin/env python3
"""Simple update server that accepts authenticated POSTs to update version.txt

Config via env:
- UPDATE_API_KEY: required API key
- UPDATE_ROOT: filesystem path to write version.txt (default: /var/www/html/latinmagazine/update)

Run behind a production WSGI server (gunicorn) or systemd.
"""
from __future__ import annotations

import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("UPDATE_API_KEY")
ROOT = os.environ.get("UPDATE_ROOT", "/var/www/html/latinmagazine/update")


def auth_ok(req) -> bool:
    key = req.headers.get("X-API-Key")
    return API_KEY and key == API_KEY


@app.route("/api/update-version", methods=["POST"])
def update_version():
    if not auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True)
    if not data or "build" not in data:
        return jsonify({"error": "missing build field"}), 400
    build = str(data["build"]).strip()
    os.makedirs(ROOT, exist_ok=True)
    target = os.path.join(ROOT, "version.txt")
    with open(target, "w", encoding="utf-8") as f:
        f.write(build + "\n")
        f.write("# updated: " + datetime.utcnow().isoformat() + "Z\n")
    return jsonify({"status": "ok", "written": target}), 200


if __name__ == "__main__":
    bind = os.environ.get("UPDATE_BIND", "0.0.0.0:8000")
    host, port = bind.split(":")
    app.run(host=host, port=int(port))
