"""Portable release helper: Python 3.11+, Git, no third-party dependencies."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path


LEVELS = ("major", "minor", "patch", "premajor", "preminor", "prepatch", "prerelease")


def run(args: list[str], root: Path, *, capture: bool = True) -> str:
    result = subprocess.run(args, cwd=root, text=True, encoding="utf-8",
                            errors="replace", capture_output=capture, check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip() if capture else ""
        raise RuntimeError(f"Command failed ({result.returncode}): {args!r}\n{detail}")
    return (result.stdout or "").strip()


def bump(version: str, level: str, python: bool, preid: str) -> str:
    pattern = (r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:(a|b|rc)(0|[1-9]\d*))?"
               if python else
               r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(alpha|beta|rc)\.(0|[1-9]\d*))?")
    match = re.fullmatch(pattern, version)
    if not match:
        raise ValueError(f"Unsupported version {version!r}: use X.Y.Z, "
                         + ("X.Y.Zrc1 / a1 / b1." if python else "X.Y.Z-rc.1 / alpha.1 / beta.1."))
    major, minor, patch = map(int, match.group(1, 2, 3))
    old_id, old_number = match.group(4, 5)
    identifier = {"alpha": "a", "beta": "b", "rc": "rc"}[preid] if python else preid
    number = 1 if python else 0
    if level in ("major", "premajor"):
        # Promoting 2.0.0rc1 to a stable major must produce 2.0.0.
        major += int(level == "premajor" or not old_id or minor != 0 or patch != 0)
        minor = patch = 0
    elif level in ("minor", "preminor"):
        minor += int(level == "preminor" or not old_id or patch != 0)
        patch = 0
    elif level in ("patch", "prepatch"):
        patch += int(level == "prepatch" or not old_id)
    elif level == "prerelease":
        if old_id == identifier:
            number = int(old_number) + 1
        elif not old_id:
            patch += 1
    result = f"{major}.{minor}.{patch}"
    if level.startswith("pre"):
        result += f"{identifier}{number}" if python else f"-{identifier}.{number}"
    return result


def json_bytes(original: bytes, data: dict) -> bytes:
    text = original.decode("utf-8")
    indent_match = re.search(r"\n([ \t]+)\"", text)
    indent = indent_match.group(1) if indent_match else None
    updated = json.dumps(data, ensure_ascii=False, indent=indent)
    if text.endswith("\n"):
        updated += "\n"
    if "\r\n" in text:
        updated = updated.replace("\n", "\r\n")
    return updated.encode("utf-8")


def prepare(path: Path, level: str, preid: str) -> tuple[str, str, dict[Path, bytes], dict]:
    original = path.read_bytes()
    text = original.decode("utf-8")
    config = {}
    if path.name == "pyproject.toml":
        data = tomllib.loads(text)
        version = data.get("project", {}).get("version")
        if not isinstance(version, str) or "version" in data["project"].get("dynamic", []):
            raise ValueError("A static [project].version is required in pyproject.toml.")
        new = bump(version, level, True, preid)
        section = re.search(r"(?m)^\[project\][ \t]*(?:#[^\r\n]*)?\r?\n([\s\S]*?)(?=^\[|\Z)", text)
        if not section:
            raise ValueError("Cannot locate [project] section.")
        body, count = re.subn(r"(?m)^(version[ \t]*=[ \t]*)([\"'])([^\r\n]*?)\2([ \t]*(?:#[^\r\n]*)?)(\r?)$",
                              lambda m: m[1] + m[2] + new + m[2] + m[4] + m[5], section[1])
        if count != 1:
            raise ValueError("Expected one single-line version assignment in [project].")
        updates = {path: (text[:section.start(1)] + body + text[section.end(1):]).encode("utf-8")}
        config = data.get("tool", {}).get("release", {})
    elif path.name == "package.json":
        data = json.loads(text)
        version = data["version"]
        new = bump(version, level, False, preid)
        data["version"] = new
        updates = {path: json_bytes(original, data)}
        for name in ("package-lock.json", "npm-shrinkwrap.json"):
            lock = path.with_name(name)
            if lock.exists():
                raw = lock.read_bytes()
                content = json.loads(raw)
                if content.get("version") != version:
                    raise ValueError(f"Version in {name} does not match package.json.")
                content["version"] = new
                if "packages" in content:
                    root_package = content["packages"].get("")
                    if not isinstance(root_package, dict) or root_package.get("version") != version:
                        raise ValueError(f"Root package version in {name} is missing or inconsistent.")
                    root_package["version"] = new
                updates[lock] = json_bytes(raw, content)
    else:
        version = text.strip()
        new = bump(version, level, False, preid)
        updates = {path: text.replace(version, new, 1).encode("utf-8")}
    return version, new, updates, config


def command(value: object) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise ValueError("Commands must be nonempty arrays of strings, e.g. [\"{python}\", \"-m\", \"pytest\", \"-q\"].")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", choices=LEVELS)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project directory; default: current directory")
    parser.add_argument("--version-file", type=Path, help="Relative to root; auto-detect pyproject.toml, package.json or VERSION")
    parser.add_argument("--preid", choices=("alpha", "beta", "rc"), default="rc")
    parser.add_argument("--branch", help="Require this Git branch")
    parser.add_argument("--tag-prefix", default="v")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--push", action="store_true", help="Publish the branch and this tag with an atomic push")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without changes or commands")
    parser.add_argument("--check", action="append", default=[], help="Additional check as a JSON array; repeatable")
    parser.add_argument("--build", action="store_true", help="Run [tool.release].build")
    parser.add_argument("--build-command", help="Build command as a JSON array")
    args = parser.parse_args(argv)
    committed = False
    originals: dict[Path, bytes] = {}
    initial_head = None
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("--root must be a directory.")
        git_root = Path(run(["git", "rev-parse", "--show-toplevel"], root)).resolve()
        root.relative_to(git_root)
        if run(["git", "status", "--porcelain", "--untracked-files=all"], git_root):
            raise ValueError("Git working tree is not clean. Commit or stash changes first.")
        initial_head = run(["git", "rev-parse", "HEAD"], git_root)
        branch = run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], git_root)
        if args.branch and branch != args.branch:
            raise ValueError(f"Expected branch {args.branch!r}, found {branch!r}.")
        if args.version_file:
            path = (root / args.version_file).resolve(strict=True)
        else:
            candidates = [root / name for name in ("pyproject.toml", "package.json", "VERSION") if (root / name).is_file()]
            # A private package.json may provide task shortcuts for a Python project,
            # without being another source of the application version.
            candidates = [file for file in candidates if file.name != "package.json"
                          or "version" in json.loads(file.read_text(encoding="utf-8"))]
            if len(candidates) != 1:
                raise ValueError("Expected exactly one version file; choose it with --version-file.")
            path = candidates[0]
        path.relative_to(root)
        version, new, updates, config = prepare(path, args.level, args.preid)
        tag = args.tag_prefix + new
        run(["git", "check-ref-format", "refs/tags/" + tag], git_root)
        if run(["git", "tag", "--list", tag], git_root):
            raise ValueError(f"Tag {tag!r} already exists locally.")
        names = []
        for file in updates:
            file.resolve(strict=True).relative_to(root)
            if file.is_symlink():
                raise ValueError(f"Version files cannot be symbolic links: {file}")
            name = file.relative_to(git_root).as_posix()
            run(["git", "ls-files", "--error-unmatch", "--", name], git_root)
            names.append(name)
        run(["git", "var", "GIT_AUTHOR_IDENT"], git_root)
        run(["git", "var", "GIT_COMMITTER_IDENT"], git_root)
        checks = config.get("checks", [])
        if not isinstance(checks, list):
            raise ValueError("[tool.release].checks must be an array of command arrays.")
        commands = [command(item) for item in checks] + [command(json.loads(item)) for item in args.check]
        if args.build_command:
            commands.append(command(json.loads(args.build_command)))
        elif args.build:
            commands.append(command(config.get("build")))
        commands = [[part.replace("{python}", sys.executable).replace("{version}", new) for part in item]
                    for item in commands]
        if args.push:
            run(["git", "remote", "get-url", args.remote], git_root)
            if run(["git", "ls-remote", "--tags", args.remote, "refs/tags/" + tag], git_root):
                raise ValueError(f"Tag {tag!r} already exists on {args.remote!r}.")
            remote_branch = run(["git", "ls-remote", "--heads", args.remote, "refs/heads/" + branch], git_root)
            if remote_branch:
                # Require the remote tip locally; never fetch or merge behind the user's back.
                run(["git", "merge-base", "--is-ancestor", remote_branch.split()[0], initial_head], git_root)
        print(f"Release: {version} -> {new}; branch: {branch}; tag: {tag}", flush=True)
        print("Version files: " + ", ".join(names), flush=True)
        for item in commands:
            print("Check/build: " + repr(item), flush=True)
        print("Publish: " + (args.remote + " (atomic)" if args.push else "local commit and tag only"), flush=True)
        if args.dry_run:
            return 0
        originals = {file: file.read_bytes() for file in updates}
        for file, content in updates.items():
            file.write_bytes(content)
        for item in commands:
            run(item, root, capture=False)
        # Checks may create ignored build artifacts, but must not change release sources.
        changed = run(["git", "diff", "--name-only", "HEAD"], git_root).splitlines()
        untracked = run(["git", "ls-files", "--others", "--exclude-standard"], git_root)
        if set(changed) != set(names) or untracked or any(file.read_bytes() != content for file, content in updates.items()):
            raise ValueError("Checks/build changed unexpected files. Review those changes before releasing.")
        if run(["git", "rev-parse", "HEAD"], git_root) != initial_head:
            raise ValueError("HEAD changed during checks/build; release aborted.")
        run(["git", "add", "--", *names], git_root)
        run(["git", "commit", "-m", f"bump: release {tag}", "--", *names], git_root, capture=False)
        committed = True
        if run(["git", "status", "--porcelain", "--untracked-files=all"], git_root):
            raise ValueError("Working tree changed during commit. Review it before tagging.")
        if any(file.read_bytes() != content for file, content in updates.items()):
            raise ValueError("A commit hook changed the version files. Review the commit before tagging.")
        run(["git", "tag", "-a", tag, "-m", f"Release {tag}"], git_root)
        if args.push:
            run(["git", "push", "--atomic", args.remote,
                 f"HEAD:refs/heads/{branch}", f"refs/tags/{tag}:refs/tags/{tag}"], git_root, capture=False)
        print(f"Release {tag} complete" + (" and published." if args.push else " locally."), flush=True)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Release failed: {exc}", file=sys.stderr)
        if originals:
            try:
                if not committed and run(["git", "rev-parse", "HEAD"], git_root) == initial_head:
                    run(["git", "restore", "--staged", "--", *names], git_root)
                    for file, content in originals.items():
                        file.write_bytes(content)
                    print("Original version files restored; other changes and build artifacts retained.", file=sys.stderr)
                else:
                    print("Commit retained. Inspect git status and tags; do not rerun a version bump to retry publication.", file=sys.stderr)
                    if args.push and committed:
                        print(f"After verifying the tag, retry: git push --atomic {args.remote} "
                              f"HEAD:refs/heads/{branch} refs/tags/{tag}:refs/tags/{tag}", file=sys.stderr)
            except (OSError, RuntimeError) as recovery_error:
                print(f"Recovery failed; inspect git status: {recovery_error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
