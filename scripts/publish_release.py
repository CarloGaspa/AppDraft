"""Publish the three CI assets for an existing AppDraft tag, never bump versions."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path


ASSET_NAMES = (
    "AppDraft-Windows-x64.exe",
    "AppDraft-macOS-arm64.zip",
    "AppDraft-macOS-x64.zip",
)


def publish(root: Path, tag: str, repository: str) -> None:
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if tag != "v" + version or not re.fullmatch(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", version):
        raise ValueError("Release tag does not match a supported project version.")
    assets = [root / "release-assets" / name for name in ASSET_NAMES]
    if any(not asset.is_file() or asset.stat().st_size == 0 for asset in assets):
        raise ValueError("All three nonempty Windows/macOS assets are required before publication.")

    def gh(*args: str) -> str:
        return subprocess.run(["gh", *args, "--repo", repository], cwd=root, check=True,
                              capture_output=True, text=True).stdout.strip()

    # List first: authentication/network errors must not be mistaken for absence.
    releases = json.loads(gh("release", "list", "--limit", "1000", "--json", "tagName,isDraft"))
    existing = next((item for item in releases if item["tagName"] == tag), None)
    if existing and not existing["isDraft"]:
        raise ValueError("Release is already published; existing downloads will not be replaced.")
    prerelease = bool(re.search(r"(?:a|b|rc)\d+$", version))
    if not existing:
        options = ["--prerelease"] if prerelease else []
        gh("release", "create", tag, "--verify-tag", "--generate-notes", "--title", tag, "--draft", *options)
    # Reruns can replace artifacts on this unpublished draft after a partial upload.
    gh("release", "upload", tag, *map(str, assets), "--clobber")
    gh("release", "edit", tag, "--draft=false", f"--prerelease={str(prerelease).lower()}",
       "--latest=false" if prerelease else "--latest")
    print(f"Published {tag} with Windows, macOS Apple Silicon and macOS Intel downloads.")


if __name__ == "__main__":
    if os.environ.get("GITHUB_REF_TYPE") != "tag":
        raise SystemExit("Run this workflow on an existing version tag, not a branch.")
    publish(Path.cwd(), os.environ["GITHUB_REF_NAME"], os.environ["GITHUB_REPOSITORY"])
