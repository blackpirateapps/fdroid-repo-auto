#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys
import zipfile


def looks_like_apk(apk_path: pathlib.Path) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(apk_path) as zf:
            names = set(zf.namelist())
    except zipfile.BadZipFile:
        return False, "not a zip file"

    if "AndroidManifest.xml" not in names:
        return False, "missing AndroidManifest.xml (likely not an APK)"
    if not any(name.startswith("classes") and name.endswith(".dex") for name in names):
        return False, "missing classes*.dex (likely not an installable APK)"
    return True, ""


def androguard_can_parse_resources(apk_path: pathlib.Path) -> tuple[bool, str]:
    try:
        from androguard.core.bytecodes.apk import APK  # type: ignore
    except Exception as e:  # pragma: no cover
        return False, f"androguard import failed: {e}"

    try:
        apk = APK(apk_path.as_posix())
        # Force the same code-path fdroidserver uses that often breaks first.
        apk.get_android_resources()
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quarantine APKs that make fdroidserver/androguard crash during scanning."
    )
    parser.add_argument("apk_dir", type=pathlib.Path, help="Directory containing .apk files")
    parser.add_argument(
        "--quarantine-dir",
        type=pathlib.Path,
        default=None,
        help="If set, move bad APKs here; otherwise delete them",
    )
    args = parser.parse_args()

    apk_dir: pathlib.Path = args.apk_dir
    quarantine_dir: pathlib.Path | None = args.quarantine_dir

    if not apk_dir.is_dir():
        print(f"APK dir not found: {apk_dir}", file=sys.stderr)
        return 2

    apks = sorted(apk_dir.glob("*.apk"))
    if not apks:
        print("No APKs found to scan.")
        return 0

    if quarantine_dir is not None:
        quarantine_dir.mkdir(parents=True, exist_ok=True)

    bad = 0
    for apk_path in apks:
        ok, reason = looks_like_apk(apk_path)
        if not ok:
            bad += 1
            print(f"BAD (format): {apk_path.name} -> {reason}")
            if quarantine_dir is None:
                apk_path.unlink(missing_ok=True)
            else:
                shutil.move(apk_path.as_posix(), (quarantine_dir / apk_path.name).as_posix())
            continue

        ok, reason = androguard_can_parse_resources(apk_path)
        if not ok:
            bad += 1
            print(f"BAD (androguard): {apk_path.name} -> {reason}")
            if quarantine_dir is None:
                apk_path.unlink(missing_ok=True)
            else:
                shutil.move(apk_path.as_posix(), (quarantine_dir / apk_path.name).as_posix())
            continue

        print(f"OK: {apk_path.name}")

    if bad:
        print(f"Quarantined/removed {bad} APK(s) that would break fdroid update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

