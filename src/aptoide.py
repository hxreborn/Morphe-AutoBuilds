import base64
import logging
from typing import Dict, Optional
from src import session

BASE_URL = "https://ws75.aptoide.com/api/7/"


def _safe_get_json(url: str) -> Optional[dict]:
    """Fetch JSON from Aptoide, returning None (with a warning) on any failure
    instead of raising. This keeps the download chain resilient: a transient
    API hiccup or an unexpected response shape degrades to 'try next platform'
    rather than aborting the whole build."""
    try:
        res = session.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.debug(f"Aptoide request failed ({url}): {e}")
        return None


def get_latest_version(app_name: str, config: Dict) -> Optional[str]:
    package = config['package']
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)
    url = f"{BASE_URL}apps/search?query={package}&limit=1&trusted=true{q}"

    data = _safe_get_json(url) or {}
    items = (((data.get("datalist") or {}).get("list")) or [])
    if not items:
        logging.warning(f"No Aptoide result for {package}")
        return None
    try:
        return items[0]["file"]["vername"]
    except (KeyError, IndexError, TypeError):
        logging.warning(f"Aptoide response missing version for {package}")
        return None


def get_download_link(version: str, app_name: str, config: Dict) -> Optional[str]:
    package = config['package']
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)

    if version.lower() == "latest":
        url = f"{BASE_URL}apps/search?query={package}&limit=1&trusted=true{q}"
        data = _safe_get_json(url) or {}
        items = (((data.get("datalist") or {}).get("list")) or [])
        if not items:
            logging.warning(f"No Aptoide result for {package}")
            return None
        try:
            return items[0]["file"]["path"]
        except (KeyError, IndexError, TypeError):
            return None

    # Find vercode for specific version
    url_versions = f"{BASE_URL}listAppVersions?package_name={package}&limit=50{q}"
    data = _safe_get_json(url_versions) or {}
    # listAppVersions returns a top-level list, unlike apps/search
    items = data.get("list") or ((data.get("datalist") or {}).get("list")) or []
    vercode = None
    for app in items:
        try:
            if app["file"]["vername"] == version:
                vercode = app["file"]["vercode"]
                break
        except (KeyError, TypeError):
            continue
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
