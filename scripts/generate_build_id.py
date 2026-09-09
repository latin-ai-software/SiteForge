#!/usr/bin/env python3
"""Generate a deterministic build id for this workspace.

Combines repository file contents, Python version, optional build flags,
and installed package list (pip freeze) into a SHA256 hash. Writes the
result to `updater/version.txt` and `data/build_info.json` and returns it.

Intended to be run as a git pre-commit hook or in CI before packaging.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict


def repo_files_hash() -> str:
    # List tracked files and hash their contents in path order to produce a
    # working-tree-sensitive fingerprint (this will include unstaged changes).
    p = subprocess.run(["git", "ls-files"], stdout=subprocess.PIPE, check=True)
    files = p.stdout.decode("utf-8").splitlines()
    h = hashlib.sha256()
    for fn in sorted(files):
        try:
            with open(fn, "rb") as f:
                data = f.read()
        except OSError:
            # skip missing files
            continue
        # include filename to avoid collisions
        h.update(fn.encode("utf-8") + b"\x00" + data + b"\x00")
    return h.hexdigest()


def pip_freeze() -> str:
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=subprocess.PIPE, check=True)
        return out.stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        return ""


def python_version() -> str:
    return sys.version.replace("\n", " ")


def build_payload(flags: str | None = None) -> Dict:
    payload = {
        "timestamp": int(time.time()),
        "python_version": python_version(),
        "build_flags": flags or "",
        "files_hash": repo_files_hash(),
        "pip_freeze": pip_freeze(),
    }
    # Optional: include current git HEAD (may be None in fresh repos)
    try:
        head = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], stdout=subprocess.PIPE, check=True)
        payload["git_head"] = head.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        payload["git_head"] = None
    return payload


def compute_build_id(payload: Dict) -> str:
    j = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(j).hexdigest()


def write_outputs(build_id: str, payload: Dict) -> None:
    # ensure directories
    root = Path(__file__).resolve().parents[1]
    updater_dir = root / "updater"
    data_dir = root / "data"
    updater_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # write the short build id to updater/version.txt
    (updater_dir / "version.txt").write_text(build_id + "\n", encoding="utf-8")

    # write detailed build info for display in settings
    info = {
        "build_id": build_id,
        "generated": payload["timestamp"],
        "python_version": payload["python_version"],
        "git_head": payload.get("git_head"),
    }
    (data_dir / "build_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    flags = None
    if argv:
        flags = " ".join(argv)
    payload = build_payload(flags)
    build_id = compute_build_id(payload)
    write_outputs(build_id, payload)
    print(build_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
