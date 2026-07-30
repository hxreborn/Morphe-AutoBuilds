#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cleanup_old_apks import assets_to_delete, identity_prefix


def test_identity_does_not_stop_at_arch_v_token():
    assert (
        identity_prefix("youtube-arm64-v8a-morphe-v2.5.0.apk")
        == "youtube-arm64-v8a-morphe"
    )


def test_default_cleanup_only_removes_superseded_versions():
    assets = [
        {"name": "forus-arm64-v8a-hxreborn-v3.0.13.apk"},
        {"name": "forus-arm64-v8a-hxreborn-v3.0.14.apk"},
        {"name": "torrent-search-revolution-universal-rush-v2.3.3.apk"},
    ]
    keep = {"forus-arm64-v8a-hxreborn-v3.0.14.apk"}
    deleted = assets_to_delete(assets, keep)
    assert [asset["name"] for asset in deleted] == [
        "forus-arm64-v8a-hxreborn-v3.0.13.apk"
    ]


def test_prune_removes_retired_apps_and_arches():
    assets = [
        {"name": "forus-universal-hxreborn-v3.0.14.apk"},
        {"name": "forus-arm64-v8a-hxreborn-v3.0.14.apk"},
        {"name": "torrent-search-revolution-universal-rush-v2.3.3.apk"},
    ]
    keep = {"forus-arm64-v8a-hxreborn-v3.0.14.apk"}
    deleted = assets_to_delete(assets, keep, prune=True)
    assert [asset["name"] for asset in deleted] == [
        "forus-universal-hxreborn-v3.0.14.apk",
        "torrent-search-revolution-universal-rush-v2.3.3.apk",
    ]


def main():
    test_identity_does_not_stop_at_arch_v_token()
    test_default_cleanup_only_removes_superseded_versions()
    test_prune_removes_retired_apps_and_arches()
    print("ok")


if __name__ == "__main__":
    main()
