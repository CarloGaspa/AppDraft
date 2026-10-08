"""Windows: un solo .exe. macOS: una .app con tutte le risorse incluse."""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
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
        info_plist={"CFBundleDisplayName": "AppDraft", "CFBundleShortVersionString": "0.1.0",
                    "NSHighResolutionCapable": True},
    )
else:
    executable = EXE(
        archive, analysis.scripts, analysis.binaries, analysis.datas, [],
        name="AppDraft", console=False, debug=False, strip=False, upx=False,
    )
