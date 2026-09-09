#!/usr/bin/env python3
"""Publish the generated build id to a remote update server.

Usage: set environment variable UPDATE_SERVER_URL and UPDATE_API_KEY or
pass them as arguments. The script reads `updater/version.txt` and POSTs
it to the server endpoint /api/update-version with header X-API-Key.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests


def read_build_id(root: Path) -> str:
    p = root / "updater" / "version.txt"
    if not p.exists():
        raise SystemExit("updater/version.txt not found; run generate_build_id.py first")
    return p.read_text(encoding="utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default=os.environ.get("UPDATE_SERVER_URL"))
    parser.add_argument("--api-key", default=os.environ.get("UPDATE_API_KEY"))
    args = parser.parse_args()

    if not args.server_url or not args.api_key:
        print("Provide --server-url and --api-key or set UPDATE_SERVER_URL/UPDATE_API_KEY")
        return 2

    root = Path(__file__).resolve().parents[1]
    build_id = read_build_id(root)

    url = args.server_url.rstrip("/") + "/api/update-version"
    headers = {"X-API-Key": args.api_key}
    payload = {"build": build_id}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"Server responded: {r.status_code}: {r.text}")
        return 3
    print("Published build", build_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
