"""Windows: un solo .exe. macOS: una .app con tutte le risorse incluse."""
import sys
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
project_version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
icons = root / "src" / "questionnaire_tool" / "resources" / "icons"
analysis = Analysis(
    [str(root / "app.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=collect_data_files("questionnaire_tool"),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
archive = PYZ(analysis.pure)

if sys.platform == "darwin":
    executable = EXE(
        archive, analysis.scripts, [], exclude_binaries=True,
        name="AppDraft", console=False, debug=False, strip=False, upx=False,
    )
    collected = COLLECT(
        executable, analysis.binaries, analysis.datas,
        name="AppDraft", strip=False, upx=False,
    )
    app = BUNDLE(
        collected, name="AppDraft.app", bundle_identifier="app.appdraft.desktop",
        icon=str(icons / "appdraft.icns"),
        info_plist={"CFBundleDisplayName": "AppDraft", "CFBundleShortVersionString": project_version,
                    "NSHighResolutionCapable": True},
    )
else:
    executable = EXE(
        archive, analysis.scripts, analysis.binaries, analysis.datas, [],
        name="AppDraft", console=False, debug=False, strip=False, upx=False,
        icon=str(icons / "appdraft.ico"),
    )
