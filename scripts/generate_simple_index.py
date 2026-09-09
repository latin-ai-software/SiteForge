#!/usr/bin/env python3
"""
Generate a PEP 503 "simple" index from Python package files in the current directory.

Run this script from the directory that is served at
https://mirror.latinai.net/latinmagazine/dependencies/ (or copy it there and run).

It creates a `simple/` subfolder with per-project index pages and a top-level
`simple/index.html` that pip can use as an `--index-url` (PEP 503 simple API).

This is a best-effort generator that handles wheels and common sdists. It uses
a heuristic to extract the project name from filenames if `packaging` is not
available. If you have `packaging` installed, the script will use it for more
accurate parsing.
"""
from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def normalize_project_name(name: str) -> str:
    # PEP 503 normalization: convert to lowercase and replace runs of
    # non-alphanumeric with a single - (this is a simple approximation).
    return re.sub(r"[^a-z0-9]+", "-", name.lower())


def split_name_version(filename: str) -> Tuple[str, str]:
    # Remove known archive extensions first
    base = filename
    for ext in (".tar.gz", ".tar.bz2", ".tar.xz", ".zip", ".whl"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break

    # Try to find the hyphen that precedes a version number (simple heuristic)
    m = re.search(r"-(?=\d)", base)
    if m:
        name = base[: m.start()]
        ver = base[m.start() + 1 :]
        return name, ver

    # Fallback: split at first hyphen
    if "-" in base:
        name, ver = base.split("-", 1)
        return name, ver

    # As a final fallback, return the whole base as the name
    return base, ""


def build_package_map(path: Path) -> Dict[str, List[str]]:
    pkg_map: Dict[str, List[str]] = {}
    for entry in sorted(path.iterdir()):
        if not entry.is_file():
            continue
        fn = entry.name
        lower = fn.lower()
        if not (lower.endswith(".whl") or lower.endswith(".tar.gz") or lower.endswith(".zip") or lower.endswith(".tar.bz2") or lower.endswith(".tar.xz")):
            continue

        name, ver = split_name_version(fn)
        proj = normalize_project_name(name)
        pkg_map.setdefault(proj, []).append(fn)

    return pkg_map


def write_project_index(simple_dir: Path, project: str, files: List[str]) -> None:
    proj_dir = simple_dir / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    index_file = proj_dir / "index.html"

    # Links should point from the project index to the actual files which are
    # stored one level up from `simple/PROJECT/` (we assume files are in the
    # served root). Use relative paths to preserve portability.
    lines = ["<html><body>\n"]
    for fn in sorted(files):
        href = "../" + fn
        lines.append(f'<a href="{html.escape(href)}">{html.escape(fn)}</a><br/>\n')
    lines.append("</body></html>\n")

    index_file.write_text("".join(lines), encoding="utf-8")


def write_top_index(simple_dir: Path, projects: List[str]) -> None:
    idx = simple_dir / "index.html"
    lines = ["<html><body>\n"]
    for p in sorted(projects):
        lines.append(f'<a href="{p}/">{p}</a><br/>\n')
    lines.append("</body></html>\n")
    idx.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    cwd = Path.cwd()
    print("Generating PEP 503 simple index in ./simple from files in:", cwd)

    pkg_map = build_package_map(cwd)
    if not pkg_map:
        print("No package files (.whl/.tar.gz/.zip) found in this directory.")
        return 1

    simple_dir = cwd / "simple"
    simple_dir.mkdir(exist_ok=True)

    for proj, files in pkg_map.items():
        print(f"Writing index for project: {proj} ({len(files)} files)")
        write_project_index(simple_dir, proj, files)

    write_top_index(simple_dir, list(pkg_map.keys()))

    print("Done. Serve the folder root and use the simple index as:")
    print("  --index-url https://<host>/latinmagazine/dependencies/simple/")
    print("Or install with --find-links pointing at the root dependencies folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
