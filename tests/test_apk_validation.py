#!/usr/bin/env python3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.apk_validation import (
    ApkValidationError,
    is_split_apk,
    native_abis,
    require_target_abi,
    requires_splits,
    root_manifest_attributes,
)


def make_apk(path: Path, entries: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as apk:
        for entry in entries:
            apk.writestr(entry, b"x")


def test_native_abi_gate_rejects_v7a_only_for_arm64():
    with tempfile.TemporaryDirectory() as temp:
        apk = Path(temp) / "v7a.apk"
        make_apk(apk, ["classes.dex", "lib/armeabi-v7a/libtorrent.so"])
        assert native_abis(apk) == {"armeabi-v7a"}
        try:
            require_target_abi(apk, "arm64-v8a")
        except ApkValidationError as error:
            assert "cannot run on arm64-v8a" in str(error)
        else:
            raise AssertionError("v7a-only APK passed the arm64 gate")


def test_native_abi_gate_allows_pure_java_and_arm64():
    with tempfile.TemporaryDirectory() as temp:
        pure = Path(temp) / "pure.apk"
        arm64 = Path(temp) / "arm64.apk"
        make_apk(pure, ["classes.dex"])
        make_apk(arm64, ["classes.dex", "lib/arm64-v8a/libapp.so"])
        assert require_target_abi(pure, "arm64-v8a") == set()
        assert require_target_abi(arm64, "arm64-v8a") == {"arm64-v8a"}


def test_manifest_checks_only_root_attributes():
    manifest = """\
N: android=http://schemas.android.com/apk/res/android
  E: manifest (line=2)
    A: android:requiredSplitTypes(0x0101064e)="base__abi,base__density"
    A: android:splitTypes(0x0101064f)=""
    A: package="com.example"
    E: application (line=10)
      A: android:name="example"
"""
    assert len(root_manifest_attributes(manifest)) == 3
    assert requires_splits(manifest)
    assert not is_split_apk(manifest)

    split_manifest = manifest.replace(
        'A: package="com.example"',
        'A: split="config.arm64_v8a"\n    A: package="com.example"',
    )
    assert is_split_apk(split_manifest)


def main():
    test_native_abi_gate_rejects_v7a_only_for_arm64()
    test_native_abi_gate_allows_pure_java_and_arm64()
    test_manifest_checks_only_root_attributes()
    print("ok")


if __name__ == "__main__":
    main()
