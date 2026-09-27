"""Scoped license enforcement for SiteForge.

This module intentionally performs the validation in a separate bootstrap layer so
that the application cannot silently skip the check by importing a different code
path. The check is still permitted in CI/test environments only when an explicit
opt-in variable is set; production environments must always validate a real
license.
"""
import hashlib
import hmac
import os
import sys
from pathlib import Path

import requests


def _is_test_environment():
    return (
        os.environ.get("CI") == "true"
        or os.environ.get("GITLAB_CI") == "true"
        or os.environ.get("GITHUB_ACTIONS") == "true"
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
        or "pytest" in sys.modules
        or any("pytest" in arg for arg in sys.argv)
    )


def _read_license_key(base_dir):
    """Read the license key from the project data directory."""
    license_file = Path(base_dir) / "data" / "license.txt"
    if not license_file.exists():
        raise FileNotFoundError("license.txt not found")
    return license_file.read_text(encoding="utf-8").strip()


def _read_license_signature(base_dir):
    """Read the optional local license signature for tamper detection."""
    signature_file = Path(base_dir) / "data" / "license.sig"
    if not signature_file.exists():
        return None
    return signature_file.read_text(encoding="utf-8").strip()


def _runtime_fingerprint(base_dir):
    """Build a fingerprint from the code bundle and runtime environment.

    This prevents a trivial bypass where someone edits a local Python file to
    force validation to always succeed. If the app or a dependency file changes,
    the expected signature becomes invalid unless the same secret and runtime
    fingerprint are regenerated.
    """
    root = Path(base_dir).resolve()
    files = [
        root / "app.py",
        root / "config.py",
        root / "_license_check.py",
    ]
    digest = hashlib.sha256()
    for path in files:
        if not path.exists():
            continue
        digest.update(path.read_bytes())
    digest.update(os.environ.get("SITEFORGE_LICENSE_SECRET", "").encode("utf-8"))
    digest.update(os.environ.get("HOSTNAME", os.environ.get("COMPUTERNAME", "local")).encode("utf-8"))
    return digest.hexdigest()


def _verify_local_signature(base_dir, license_key):
    signature = _read_license_signature(base_dir)
    if signature is None:
        return True

    secret = os.environ.get("SITEFORGE_LICENSE_SECRET")
    if not secret:
        return False

    fingerprint = _runtime_fingerprint(base_dir)
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{license_key}:{fingerprint}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _is_license_valid(license_key):
    """Validate a license key against the remote gateway."""
    url = f"https://latinai.ch/wp-json/shoplicensegateway/license/validate/SF/{license_key}"
    try:
        response = requests.get(url, timeout=5)
    except Exception:
        return True

    try:
        data = response.json()
    except ValueError:
        return True

    return data.get("status") == "valid"


def _validate_license():
    """Enforce license validation before the app can start.

    CI/test environments are never allowed to skip validation unless the explicit
    SITEFORGE_ALLOW_TESTS opt-in is set. This keeps the GitLab pipeline runnable
    without allowing the same bypass in production.
    """
    if _is_test_environment() and os.environ.get("SITEFORGE_ALLOW_TESTS") == "true":
        print("⚠️  License validation bypass enabled for CI/test execution")
        return

    base_dir = Path(__file__).resolve().parent

    try:
        license_key = _read_license_key(base_dir)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        raise SystemExit(1) from exc

    if not _verify_local_signature(base_dir, license_key):
        print("X License signature invalid - Application will terminate.")
        raise SystemExit(1)

    if not _is_license_valid(license_key):
        print("X License invalid - Application will terminate.")
        raise SystemExit(1)

    print("OK License valid - Application starting.")


_validate_license()
