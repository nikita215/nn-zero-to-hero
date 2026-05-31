#!/usr/bin/env python3
"""Lightweight repository validation for environments without Android SDK/Gradle plugin cache."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "settings.gradle.kts",
    "shared/src/main/kotlin/com/example/tabletcoderemote/shared/Models.kt",
    "shared/src/main/kotlin/com/example/tabletcoderemote/shared/BootstrapScript.kt",
    "app/src/main/AndroidManifest.xml",
    "app/src/main/java/com/example/tabletcoderemote/MainActivity.kt",
    "app/src/main/java/com/example/tabletcoderemote/ssh/RemoteIdeTunnelService.kt",
    "app/src/main/java/com/example/tabletcoderemote/web/WebIdeView.kt",
]

for relative in REQUIRED:
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"missing required file: {relative}")

bootstrap = (ROOT / "shared/src/main/kotlin/com/example/tabletcoderemote/shared/BootstrapScript.kt").read_text()
for snippet in ["--host 127.0.0.1", "TABLET_CODE_REMOTE_PORT", "connection-token", "code-server"]:
    if snippet not in bootstrap:
        raise SystemExit(f"bootstrap script missing snippet: {snippet}")

manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text()
for permission in ["android.permission.INTERNET", "android.permission.FOREGROUND_SERVICE"]:
    if permission not in manifest:
        raise SystemExit(f"manifest missing permission: {permission}")

print("tablet-code-remote scaffold validation passed")
