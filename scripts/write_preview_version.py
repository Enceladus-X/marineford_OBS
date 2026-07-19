from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "docs" / "preview" / "version.json"


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def main() -> None:
    full_commit = (
        os.environ.get("PREVIEW_VERSION_SOURCE_SHA")
        or os.environ.get("GITHUB_SHA")
        or git_value("rev-parse", "HEAD")
        or "local"
    )
    short_commit = full_commit[:7] if full_commit != "local" else "local"
    branch = (
        os.environ.get("PREVIEW_VERSION_BRANCH")
        or os.environ.get("GITHUB_REF_NAME")
        or git_value("branch", "--show-current")
        or "local"
    )
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    cache_key = "-".join(part for part in (short_commit, run_number) if part) or updated_at

    data = {
        "schema": 1,
        "name": "Marineford OBS Preview",
        "branch": branch,
        "commit": short_commit,
        "fullCommit": full_commit,
        "cacheKey": cache_key,
        "updatedAt": updated_at,
        "source": "github-actions" if os.environ.get("GITHUB_ACTIONS") else "local",
        "overlayPath": "overlay.html",
        "embedPath": "embed.js",
    }

    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {VERSION_FILE}")


if __name__ == "__main__":
    main()
