#!/usr/bin/env python3
"""Run directly: python tests/test_downloader_arch.py"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.CRITICAL)

from src import downloader


class FakeProvider:
    def __init__(self):
        self.config = None

    def get_download_link(self, version, app_name, config):
        self.config = config
        return None


def test_apkmirror_keeps_configured_universal_bundle_selector():
    provider = FakeProvider()
    original = downloader.apkmirror
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        config_dir = root / "apps" / "apkmirror"
        config_dir.mkdir(parents=True)
        (config_dir / "vpn.json").write_text(
            json.dumps(
                {
                    "package": "example.vpn",
                    "version": "1.0",
                    "type": "BUNDLE",
                    "arch": "universal",
                }
            ),
            encoding="utf-8",
        )
        old_cwd = Path.cwd()
        try:
            downloader.apkmirror = provider
            os.chdir(root)
            downloader.download_platform(
                "vpn", "apkmirror", "cli.jar", "patches.mpp", "arm64-v8a"
            )
        finally:
            os.chdir(old_cwd)
            downloader.apkmirror = original

    assert provider.config["arch"] == "universal"


if __name__ == "__main__":
    test_apkmirror_keeps_configured_universal_bundle_selector()
    print("ok")
