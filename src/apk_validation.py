import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ANDROID_NS = "http://schemas.android.com/apk/res/android"
REQUIRED_SPLIT_TYPES = f"{{{ANDROID_NS}}}requiredSplitTypes"
SPLIT_TYPES = f"{{{ANDROID_NS}}}splitTypes"
_LIBRARY_PATH = re.compile(r"^lib/([^/]+)/[^/]+\.so$")


class ApkValidationError(RuntimeError):
    pass


def native_abis(apk_path: Path) -> set[str]:
    with zipfile.ZipFile(apk_path) as apk:
        return {
            match.group(1)
            for entry in apk.namelist()
            if (match := _LIBRARY_PATH.match(entry))
        }


def require_target_abi(
    apk_path: Path,
    target_arch: str,
    *,
    native_required: bool = False,
    target_only: bool = False,
) -> set[str]:
    abis = native_abis(apk_path)
    if target_arch == "universal":
        return abis

    if native_required and not abis:
        raise ApkValidationError(
            f"{apk_path.name} lost all native libraries while targeting {target_arch}"
        )
    if abis and target_arch not in abis:
        available = ", ".join(sorted(abis))
        raise ApkValidationError(
            f"{apk_path.name} cannot run on {target_arch}; native libraries: {available}"
        )
    if target_only and abis - {target_arch}:
        extras = ", ".join(sorted(abis - {target_arch}))
        raise ApkValidationError(
            f"{apk_path.name} still contains non-target native libraries: {extras}"
        )
    return abis


def dump_manifest(apk_path: Path, aapt: Path) -> str:
    result = subprocess.run(
        [str(aapt), "dump", "xmltree", str(apk_path), "AndroidManifest.xml"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ApkValidationError(
            f"Could not inspect AndroidManifest.xml in {apk_path.name}: {detail}"
        )
    return result.stdout


def root_manifest_attributes(manifest_dump: str) -> list[str]:
    attributes: list[str] = []
    in_manifest = False
    for line in manifest_dump.splitlines():
        if line.startswith("  E: manifest"):
            in_manifest = True
            continue
        if not in_manifest:
            continue
        if line.startswith("    E:"):
            break
        if line.startswith("    A:"):
            attributes.append(line.strip())
    return attributes


def requires_splits(manifest_dump: str) -> bool:
    return any("android:requiredSplitTypes" in attr for attr in root_manifest_attributes(manifest_dump))


def is_split_apk(manifest_dump: str) -> bool:
    return any(
        attr.startswith("A: split=") or attr.startswith("A: android:split=")
        for attr in root_manifest_attributes(manifest_dump)
    )


def validate_standalone_manifest(apk_path: Path, aapt: Path) -> None:
    manifest = dump_manifest(apk_path, aapt)
    if is_split_apk(manifest):
        raise ApkValidationError(f"{apk_path.name} is a split APK, not a standalone APK")
    if requires_splits(manifest):
        raise ApkValidationError(
            f"{apk_path.name} still requires missing configuration splits"
        )


def remove_required_split_metadata(
    apk_path: Path,
    apk_editor: Path,
    aapt: Path,
) -> bool:
    if not requires_splits(dump_manifest(apk_path, aapt)):
        return False

    ET.register_namespace("android", ANDROID_NS)
    with tempfile.TemporaryDirectory(prefix="morphe-manifest-") as temp:
        temp_path = Path(temp)
        decoded = temp_path / "decoded"
        rebuilt = temp_path / "rebuilt.apk"

        subprocess.run(
            [
                "java",
                "-jar",
                str(apk_editor),
                "d",
                "-t",
                "xml",
                "-dex",
                "-i",
                str(apk_path),
                "-o",
                str(decoded),
            ],
            check=True,
        )

        manifest_path = decoded / "AndroidManifest.xml"
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        removed = False
        for attribute in (REQUIRED_SPLIT_TYPES, SPLIT_TYPES):
            if attribute in root.attrib:
                del root.attrib[attribute]
                removed = True
        if not removed:
            raise ApkValidationError(
                f"APKEditor decoded {apk_path.name}, but split metadata was not found"
            )
        tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

        subprocess.run(
            [
                "java",
                "-jar",
                str(apk_editor),
                "b",
                "-t",
                "xml",
                "-i",
                str(decoded),
                "-o",
                str(rebuilt),
            ],
            check=True,
        )
        if not rebuilt.is_file() or rebuilt.stat().st_size == 0:
            raise ApkValidationError(
                f"APKEditor did not rebuild {apk_path.name} after manifest repair"
            )
        rebuilt.replace(apk_path)

    validate_standalone_manifest(apk_path, aapt)
    return True
