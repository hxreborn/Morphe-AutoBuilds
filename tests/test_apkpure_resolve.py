#!/usr/bin/env python3
"""Run directly: python tests/test_apkpure_resolve.py"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.CRITICAL)

from src import apkpure

CDN = "https://data.winudf.com/APK/blob?_p=x&filename={}&full_size=1&is_hot=false"


class FakeResponse:
    def __init__(self, location):
        self.status_code = 302
        self.headers = {"location": location} if location else {}


def test_extracts_version_from_real_filenames():
    cases = {
        "Speedtest+by+Ookla_7.0.7_APKPure.apk": "7.0.7",
        "SAI%3A+Split+APKs+Installer_2.3.1_APKPure.xapk": "2.3.1",
        "Network+Guru%3A+Speed+Indicator_1.9-beta5_APKPure.apk": "1.9-beta5",
        "Projectivy+Launcher_4.71_APKPure.xapk": "4.71",
        "ForusApp_3.0.14_APKPure.apk": "3.0.14",
    }
    for filename, expected in cases.items():
        apkpure.session.get = lambda *a, **k: FakeResponse(CDN.format(filename))
        url, version = apkpure._resolve_latest("com.example")
        assert version == expected, (filename, version)
        assert url.startswith("https://d.apkpure.com/b/APK/"), url


def test_stub_redirect_and_junk_resolve_to_none():
    for location in ["https://apkpure.com", "https://apkpure.com/", "", "https://x/?a=b"]:
        apkpure.session.get = lambda *a, **k: FakeResponse(location)
        assert apkpure._resolve_latest("com.example") is None, location


def test_pinned_version_refuses_a_mismatched_release():
    apkpure.session.get = lambda *a, **k: FakeResponse(
        CDN.format("SAI%3A+Split+APKs+Installer_2.3.1_APKPure.xapk")
    )
    config = {"package": "com.mtv.sai", "name": "sai-split-apks-installer"}
    assert apkpure.get_download_link("2.3.1", "sai", config) is not None
    # A pin the host cannot serve must fall through, never hand back the wrong build
    assert apkpure.get_download_link("2.2.8", "sai", config) is None


def main():
    real_get = apkpure.session.get
    try:
        test_extracts_version_from_real_filenames()
        test_stub_redirect_and_junk_resolve_to_none()
        test_pinned_version_refuses_a_mismatched_release()
    finally:
        apkpure.session.get = real_get

    print("ok")


if __name__ == "__main__":
    main()
