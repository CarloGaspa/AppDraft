"""Release tests use isolated repositories; never publish this project."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location("release", Path(__file__).parents[1] / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    if not shutil.which("git"):
        pytest.skip("Git is required for release integration tests")
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "release@example.invalid")
    git(tmp_path, "config", "user.name", "Release Test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    git(tmp_path, "config", "tag.gpgsign", "false")
    git(tmp_path, "config", "core.autocrlf", "false")
    git(tmp_path, "config", "core.hooksPath", str(tmp_path / "no-hooks"))
    (tmp_path / "pyproject.toml").write_bytes(b'[project]\r\nname = "demo"\r\nversion = "1.2.3" # retain comment\r\n')
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    return tmp_path


@pytest.mark.parametrize("version,level,python,expected", [
    ("1.2.3", "major", True, "2.0.0"),
    ("1.2.3", "minor", False, "1.3.0"),
    ("1.2.3", "patch", True, "1.2.4"),
    ("1.2.3", "premajor", True, "2.0.0rc1"),
    ("1.2.3", "preminor", False, "1.3.0-rc.0"),
    ("1.2.3", "prepatch", True, "1.2.4rc1"),
    ("1.2.3", "prerelease", False, "1.2.4-rc.0"),
    ("1.2.4rc1", "prerelease", True, "1.2.4rc2"),
    ("1.2.4-rc.0", "prerelease", False, "1.2.4-rc.1"),
    ("2.0.0rc2", "major", True, "2.0.0"),
    ("1.3.0rc2", "minor", True, "1.3.0"),
    ("1.2.4rc2", "patch", True, "1.2.4"),
])
def test_version_transitions(version, level, python, expected):
    assert release.bump(version, level, python, "rc") == expected


def test_dry_run_and_local_release_preserve_toml(repo):
    path = repo / "pyproject.toml"
    original = path.read_bytes()
    head = git(repo, "rev-parse", "HEAD")
    assert release.main(["patch", "--root", str(repo), "--dry-run"]) == 0
    assert path.read_bytes() == original
    assert git(repo, "rev-parse", "HEAD") == head
    assert release.main(["patch", "--root", str(repo)]) == 0
    assert path.read_bytes() == original.replace(b"1.2.3", b"1.2.4")
    assert git(repo, "tag", "--list") == "v1.2.4"
    assert git(repo, "rev-parse", "v1.2.4^{commit}") == git(repo, "rev-parse", "HEAD")
    assert not git(repo, "status", "--porcelain")


def test_failed_check_restores_version_and_index(repo):
    original = (repo / "pyproject.toml").read_bytes()
    head = git(repo, "rev-parse", "HEAD")
    check = json.dumps([sys.executable, "-c", "raise SystemExit(7)"])
    assert release.main(["patch", "--root", str(repo), "--check", check]) == 1
    assert (repo / "pyproject.toml").read_bytes() == original
    assert git(repo, "rev-parse", "HEAD") == head
    assert not git(repo, "status", "--porcelain")
    assert not git(repo, "tag", "--list")


def test_task_package_without_version_keeps_python_autodetection(repo):
    (repo / "package.json").write_text('{"private": true, "scripts": {}}')
    git(repo, "add", "package.json")
    git(repo, "commit", "-m", "task shortcuts")
    assert release.main(["patch", "--root", str(repo), "--dry-run"]) == 0


def test_two_version_sources_require_explicit_selection(repo):
    (repo / "package.json").write_text('{"version": "1.2.3"}')
    git(repo, "add", "package.json")
    git(repo, "commit", "-m", "npm project")
    assert release.main(["patch", "--root", str(repo), "--dry-run"]) == 1
    assert release.main(["patch", "--root", str(repo), "--version-file", "pyproject.toml", "--dry-run"]) == 0


def test_dirty_tree_and_existing_tag_stop_before_changes(repo):
    path = repo / "pyproject.toml"
    original = path.read_bytes()
    (repo / "untracked.txt").write_text("work")
    assert release.main(["patch", "--root", str(repo)]) == 1
    (repo / "untracked.txt").unlink()
    git(repo, "tag", "v1.2.4")
    assert release.main(["patch", "--root", str(repo)]) == 1
    assert path.read_bytes() == original


@pytest.mark.parametrize("lock_version", [1, 2, 3])
def test_npm_lock_updates_only_root_package(tmp_path, lock_version):
    package = tmp_path / "package.json"
    package.write_text(json.dumps({"name": "demo", "version": "1.2.3"}))
    lock = {"name": "demo", "version": "1.2.3", "lockfileVersion": lock_version,
            "dependencies": {"example": {"version": "1.2.3"}}}
    if lock_version > 1:
        lock["packages"] = {"": {"version": "1.2.3"}, "node_modules/example": {"version": "1.2.3"}}
    (tmp_path / "package-lock.json").write_text(json.dumps(lock))
    _, new, updates, _ = release.prepare(package, "patch", "rc")
    updated = json.loads(updates[tmp_path / "package-lock.json"])
    assert new == updated["version"] == "1.2.4"
    assert updated["dependencies"]["example"]["version"] == "1.2.3"
    if lock_version > 1:
        assert updated["packages"][""]["version"] == "1.2.4"
        assert updated["packages"]["node_modules/example"]["version"] == "1.2.3"


def test_atomic_push_to_local_remote(repo, tmp_path):
    remote = repo.parent / (repo.name + "-remote.git")
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    assert release.main(["patch", "--root", str(repo), "--push", "--branch", "main"]) == 0
    assert git(remote, "rev-parse", "refs/heads/main") == git(repo, "rev-parse", "HEAD")
    assert git(remote, "rev-parse", "refs/tags/v1.2.4^{commit}") == git(repo, "rev-parse", "HEAD")


def test_failed_atomic_push_keeps_local_release(repo):
    remote = repo.parent / (repo.name + "-remote.git")
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    old_head = git(remote, "rev-parse", "refs/heads/main")
    git(remote, "config", "receive.advertiseAtomic", "false")
    assert release.main(["patch", "--root", str(repo), "--push"]) == 1
    assert git(repo, "tag", "--list") == "v1.2.4"
    assert git(repo, "rev-parse", "HEAD") != old_head
    assert not git(repo, "status", "--porcelain")
    assert git(remote, "rev-parse", "refs/heads/main") == old_head
    assert not git(remote, "tag", "--list")


@pytest.mark.parametrize("url", [
    "https://github.com/owner/demo.git", "git@github.com:owner/demo.git",
    "ssh://git@github.com/owner/demo.git", "https://github.com/owner/demo/",
])
def test_github_repository_from_push_url(url):
    assert release.github_repository(url) == ("github.com", "owner/demo")


@pytest.fixture
def github_release_repo(repo, monkeypatch):
    """Real local Git push; all gh commands are simulated, never networked."""
    remote = repo.parent / (repo.name + "-remote.git")
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    with (repo / "pyproject.toml").open("a", encoding="utf-8") as file:
        file.write('\n[tool.release]\nassets = ["dist/demo.exe"]\n')
    (repo / ".gitignore").write_text("dist/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "release configuration")
    git(repo, "push", "origin", "main")
    original_run = release.run
    original_which = shutil.which
    monkeypatch.setattr(release.shutil, "which", lambda name: "gh" if name == "gh" else original_which(name))
    monkeypatch.setattr(release, "github_repository", lambda url: ("github.com", "owner/demo"))
    calls = []
    responses = {"permission": "WRITE", "existing": "", "fail": None}

    def fake_run(args, root, *, capture=True):
        if args[0] != "gh":
            return original_run(args, root, capture=capture)
        calls.append(args)
        if args[1:3] == responses["fail"]:
            raise RuntimeError("simulated gh failure")
        if args[1:3] == ["repo", "view"]:
            return json.dumps({"viewerPermission": responses["permission"], "isArchived": False})
        if args[1] == "api":
            return responses["existing"]
        return ""

    monkeypatch.setattr(release, "run", fake_run)
    build = json.dumps([sys.executable, "-c",
                        "from pathlib import Path; Path('dist').mkdir(exist_ok=True); Path('dist/demo.exe').write_bytes(b'build')"])
    return repo, remote, calls, responses, build


@pytest.mark.parametrize("level,tag", [("patch", "v1.2.4"), ("prepatch", "v1.2.4rc1")])
def test_github_release_build_push_upload_then_publish(github_release_repo, level, tag):
    repo, remote, calls, _, build = github_release_repo
    assert release.main([level, "--root", str(repo), "--release", "--build-command", build]) == 0
    writes = [args for args in calls if args[1] == "release"]
    assert [args[2] for args in writes] == ["create", "upload", "edit"]
    assert all(args[3] == tag and args[args.index("--repo") + 1] == "github.com/owner/demo" for args in writes)
    assert "--verify-tag" in writes[0] and "--draft" in writes[0] and "--generate-notes" in writes[0]
    assert ("--prerelease" in writes[0]) == level.startswith("pre")
    assert "--draft=false" in writes[2]
    assert ("--latest=false" if level.startswith("pre") else "--latest") in writes[2]
    assert str(repo / "dist" / "demo.exe") in writes[1]
    assert git(remote, "rev-parse", f"refs/tags/{tag}^{{commit}}") == git(repo, "rev-parse", "HEAD")


def test_github_dry_run_has_no_build_commit_push_or_release(github_release_repo):
    repo, remote, calls, _, build = github_release_repo
    original = (repo / "pyproject.toml").read_bytes()
    head = git(repo, "rev-parse", "HEAD")
    assert release.main(["patch", "--root", str(repo), "--release", "--build-command", build, "--dry-run"]) == 0
    assert (repo / "pyproject.toml").read_bytes() == original
    assert not (repo / "dist").exists()
    assert git(repo, "rev-parse", "HEAD") == git(remote, "rev-parse", "refs/heads/main") == head
    assert not any(args[1] == "release" for args in calls)


@pytest.mark.parametrize("failure", ["auth", "permission", "existing"])
def test_github_preflight_errors_do_not_change_version(github_release_repo, failure):
    repo, _, calls, responses, build = github_release_repo
    if failure == "auth":
        responses["fail"] = ["auth", "status"]
    elif failure == "permission":
        responses["permission"] = "READ"
    else:
        responses["existing"] = "v1.2.4"
    original = (repo / "pyproject.toml").read_bytes()
    assert release.main(["patch", "--root", str(repo), "--release", "--build-command", build]) == 1
    assert (repo / "pyproject.toml").read_bytes() == original
    assert not (repo / "dist").exists()
    assert not any(args[1] == "release" for args in calls)
    assert not git(repo, "tag", "--list")


def test_missing_asset_rolls_back_before_commit_or_push(github_release_repo):
    repo, remote, calls, _, _ = github_release_repo
    original = (repo / "pyproject.toml").read_bytes()
    head = git(repo, "rev-parse", "HEAD")
    build = json.dumps([sys.executable, "-c", "pass"])
    assert release.main(["patch", "--root", str(repo), "--release", "--build-command", build]) == 1
    assert (repo / "pyproject.toml").read_bytes() == original
    assert git(repo, "rev-parse", "HEAD") == git(remote, "rev-parse", "refs/heads/main") == head
    assert not any(args[1] == "release" for args in calls)


def test_failed_asset_upload_leaves_draft_and_retains_pushed_tag(github_release_repo, capsys):
    repo, remote, calls, responses, build = github_release_repo
    responses["fail"] = ["release", "upload"]
    assert release.main(["patch", "--root", str(repo), "--release", "--build-command", build]) == 1
    assert [args[2] for args in calls if args[1] == "release"] == ["create", "upload"]
    assert git(remote, "rev-parse", "refs/tags/v1.2.4^{commit}") == git(repo, "rev-parse", "HEAD")
    assert not git(repo, "status", "--porcelain")
    assert "gh release view v1.2.4 --repo github.com/owner/demo" in capsys.readouterr().err


def test_missing_github_cli_stops_before_build(github_release_repo, monkeypatch):
    repo, _, calls, _, build = github_release_repo
    monkeypatch.setattr(release.shutil, "which", lambda name: None)
    original = (repo / "pyproject.toml").read_bytes()
    assert release.main(["patch", "--root", str(repo), "--release", "--build-command", build]) == 1
    assert (repo / "pyproject.toml").read_bytes() == original
    assert not (repo / "dist").exists()
    assert not calls


def test_macos_app_is_archived_with_ditto(tmp_path, monkeypatch):
    app = tmp_path / "Demo.app"
    app.mkdir()
    calls = []
    monkeypatch.setattr(release, "sys", SimpleNamespace(platform="darwin"))

    def ditto(args, root):
        calls.append(args)
        Path(args[-1]).write_bytes(b"zip")
        return ""

    monkeypatch.setattr(release, "run", ditto)
    assert release.package_assets([app], tmp_path) == [tmp_path / "Demo.app.zip"]
    assert calls[0][:5] == ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent"]
