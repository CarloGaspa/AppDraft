"""CI publication tests simulate gh; no network or project release is used."""
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location("publish_release", Path(__file__).parents[1] / "scripts" / "publish_release.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


@pytest.fixture
def publication(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')
    directory = tmp_path / "release-assets"
    directory.mkdir()
    for name in publisher.ASSET_NAMES:
        (directory / name).write_bytes(b"build")
    calls = []
    state = {"existing": [], "fail": None}

    def run(args, **kwargs):
        calls.append(args)
        if args[2] == state["fail"]:
            raise subprocess.CalledProcessError(1, args)
        return SimpleNamespace(stdout=json.dumps(state["existing"]) if args[2] == "list" else "")

    monkeypatch.setattr(publisher.subprocess, "run", run)
    return tmp_path, calls, state


@pytest.mark.parametrize("version,prerelease", [("1.2.3", False), ("1.2.3rc1", True)])
def test_publish_after_all_uploads(publication, version, prerelease):
    root, calls, _ = publication
    (root / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
    publisher.publish(root, "v" + version, "owner/repo")
    assert [args[2] for args in calls] == ["list", "create", "upload", "edit"]
    assert "--draft" in calls[1] and "--verify-tag" in calls[1]
    assert ("--prerelease" in calls[1]) == prerelease
    assert all(str(root / "release-assets" / name) in calls[2] for name in publisher.ASSET_NAMES)
    assert "--draft=false" in calls[3]
    assert ("--latest=false" if prerelease else "--latest") in calls[3]


def test_missing_asset_and_wrong_tag_prevent_any_github_calls(publication):
    root, calls, _ = publication
    with pytest.raises(ValueError):
        publisher.publish(root, "v9.9.9", "owner/repo")
    (root / "release-assets" / publisher.ASSET_NAMES[1]).unlink()
    with pytest.raises(ValueError):
        publisher.publish(root, "v1.2.3", "owner/repo")
    assert not calls


@pytest.mark.parametrize("failure", ["list", "upload"])
def test_failure_never_publishes(publication, failure):
    root, calls, state = publication
    state["fail"] = failure
    with pytest.raises(subprocess.CalledProcessError):
        publisher.publish(root, "v1.2.3", "owner/repo")
    assert not any(args[2] == "edit" for args in calls)


def test_retry_unpublished_draft(publication):
    root, calls, state = publication
    state["existing"] = [{"tagName": "v1.2.3", "isDraft": True}]
    publisher.publish(root, "v1.2.3", "owner/repo")
    assert [args[2] for args in calls] == ["list", "upload", "edit"]


def test_published_release_is_preserved(publication):
    root, calls, state = publication
    state["existing"] = [{"tagName": "v1.2.3", "isDraft": False}]
    with pytest.raises(ValueError):
        publisher.publish(root, "v1.2.3", "owner/repo")
    assert [args[2] for args in calls] == ["list"]
