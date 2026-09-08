import base64
import logging
import re
from typing import Dict, Optional
from src import session, utils

BASE_URL = "https://ws75.aptoide.com/api/7/"


def _safe_get_json(url: str) -> Optional[dict]:
    """Fetch JSON from Aptoide, returning None (with a warning) on any failure
    instead of raising."""
    try:
        res = session.get(url, timeout=20)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.debug(f"Aptoide request failed ({url}): {e}")
        return None


def get_latest_version(app_name: str, config: Dict) -> Optional[str]:
    package = config.get('package', '')
    if not package:
        return None
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)

    # 1. Try listAppVersions first (direct exact package lookup)
    url_versions = f"{BASE_URL}listAppVersions?package_name={package}&limit=1{q}"
    data = _safe_get_json(url_versions) or {}
    items = data.get("list") or (((data.get("datalist") or {}).get("list")) or [])
    for it in items:
        if it.get("package") == package and it.get("file", {}).get("vername"):
            return it["file"]["vername"]

    # 2. Fallback to apps/search filtered by package
    url = f"{BASE_URL}apps/search?query={package}&limit=10&trusted=true{q}"
    data = _safe_get_json(url) or {}
    items = (((data.get("datalist") or {}).get("list")) or data.get("list") or [])
    for app in items:
        if app.get("package") == package and app.get("file", {}).get("vername"):
            return app["file"]["vername"]

    logging.warning(f"No Aptoide result for {package}")
    return None


def get_download_link(version: str, app_name: str, config: Dict) -> Optional[str]:
    package = config.get('package', '')
    if not package:
        return None
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)

    # Find vercode for specific version (search up to 100 versions)
    url_versions = f"{BASE_URL}listAppVersions?package_name={package}&limit=100{q}"
    data = _safe_get_json(url_versions) or {}
    items = data.get("list") or (((data.get("datalist") or {}).get("list")) or [])
    items = [it for it in items if it.get("package") == package]
    
    vercode = None
    
    if version and version.lower() != "latest":
        clean_target = re.sub(r'[\(\[].*?[\)\]]', '', version).strip()
        target_norm = utils.normalize_version(version)

        for app in items:
            try:
                vname = app["file"]["vername"].strip()
                clean_entry = re.sub(r'[\(\[].*?[\)\]]', '', vname).strip()
                entry_norm = utils.normalize_version(vname)
                if (
                    vname == version
                    or clean_entry == clean_target
                    or clean_entry == version
                    or vname == clean_target
                    or (entry_norm and target_norm and entry_norm == target_norm)
                ):
                    vercode = app["file"]["vercode"]
                    break
            except (KeyError, TypeError):
                continue

    # Fallback to latest trusted version of THIS package if specific version not found
    pinned = (config.get("version") or "").strip()
    if not vercode and not pinned and items:
        try:
            vercode = items[0]["file"]["vercode"]
            logging.info(f"Using nearest Aptoide version {items[0]['file']['vername']} for {package}")
        except (KeyError, TypeError):
            pass

    if not vercode:
        logging.warning(f"Version {version} not found on Aptoide for {package}")
        return None

    # Get meta with download path
    url_meta = f"{BASE_URL}getAppMeta?package_name={package}&vercode={vercode}{q}"
    data = _safe_get_json(url_meta) or {}
    try:
        return data["data"]["file"]["path"]
    except (KeyError, TypeError):
        logging.warning(f"Aptoide meta missing download path for {package}@{vercode}")
        return None


def _get_q_param(arch: str) -> str:
    if arch == 'universal':
        return ''
    cpu_map = {
        'arm64-v8a': 'arm64-v8a,armeabi-v7a,armeabi',
        'armeabi-v7a': 'armeabi-v7a,armeabi',
        # Add others as needed
    }
    cpu = cpu_map.get(arch, '')
    if cpu:
        q_str = f"myCPU={cpu}&leanback=0"
        return f"&q={base64.b64encode(q_str.encode('utf-8')).decode('utf-8')}"
    return ''
