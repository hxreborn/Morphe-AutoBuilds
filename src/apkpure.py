import json
import logging
import re
import time
from urllib.parse import unquote

from src import session
from bs4 import BeautifulSoup

# Define a standard browser User-Agent to avoid 403 Forbidden errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://apkpure.net/'
}

_STUB_REDIRECT = "https://apkpure.com"
_FILENAME = re.compile(r"filename=([^&]+)")
_VERSION_IN_FILENAME = re.compile(r"_([^_]+)_APKPure\.[a-z]+$", re.I)
_LATEST_RETRIES = 3


def _resolve_latest(package: str, prefer_xapk: bool = False) -> tuple[str, str] | None:
    """Return (download url, version) from APKPure's download host, or None.

    apkpure.net answers datacenter IPs with a Cloudflare challenge; this host
    does not, but it only ever serves the current release.
    """
    kinds = ("XAPK", "APK") if prefer_xapk else ("APK", "XAPK")
    for kind in kinds:
        url = f"https://d.apkpure.com/b/{kind}/{package}?version=latest"
        response = None
        for attempt in range(_LATEST_RETRIES):
            try:
                response = session.get(url, timeout=25, allow_redirects=False)
                break
            except Exception as e:
                logging.warning(
                    "APKPure %s lookup attempt %d/%d failed for %s: %s",
                    kind,
                    attempt + 1,
                    _LATEST_RETRIES,
                    package,
                    e,
                )
                if attempt + 1 < _LATEST_RETRIES:
                    time.sleep(2 ** attempt)
        if response is None:
            continue

        location = response.headers.get("location", "")
        if location.strip().rstrip("/") == _STUB_REDIRECT:
            continue

        filename = _FILENAME.search(location)
        if not filename:
            continue

        version = _VERSION_IN_FILENAME.search(unquote(filename.group(1)))
        if version:
            return url, version.group(1)

    return None


def get_latest_version(app_name: str, config: dict) -> str:
    resolved = _resolve_latest(config['package'], config.get("prefer_xapk", False))
    if resolved:
        return resolved[1]

    url = f"https://apkpure.net/{config['name']}/{config['package']}/versions"

    try:
        # Added headers to the request
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        
        content_size = len(response.content)
        logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> \"-\" [1]")
        
        soup = BeautifulSoup(response.content, "html.parser")
        version_info = soup.find('div', class_='ver-top-down')

        if version_info and 'data-dt-version' in version_info.attrs:
            return version_info['data-dt-version']
            
    except Exception as e:
        logging.error(f"Failed to fetch latest version for {app_name}: {e}")
        
    return None

def get_download_link(version: str, app_name: str, config: dict) -> str:
    resolved = _resolve_latest(config['package'], config.get("prefer_xapk", False))
    if resolved:
        download_url, latest = resolved
        if latest == version:
            return download_url
        logging.info(
            f"APKPure serves only {latest} for {app_name}; {version} needs another source"
        )

    # APKPure's exact-version pages are sometimes blocked on datacenter IPs,
    # while its download host remains available. A pinned versionCode lets us
    # use that stable endpoint directly and verify the version from its
    # Content-Disposition redirect before downloading anything.
    version_code = str(config.get("version_code") or "").strip()
    if version_code:
        kind = "XAPK" if config.get("prefer_xapk", False) else "APK"
        params = [f"versionCode={version_code}"]
        if config.get("arch"):
            params.append(f"nc={config['arch']}")
        if config.get("min_sdk"):
            params.append(f"sv={config['min_sdk']}")
        pinned_url = (
            f"https://d.apkpure.net/b/{kind}/{config['package']}?"
            + "&".join(params)
        )
        try:
            response = session.get(pinned_url, timeout=25, allow_redirects=False)
            filename = _FILENAME.search(response.headers.get("location", ""))
            resolved_version = (
                _VERSION_IN_FILENAME.search(unquote(filename.group(1)))
                if filename
                else None
            )
            if resolved_version and resolved_version.group(1) == version:
                return pinned_url
            logging.warning(
                "APKPure versionCode %s resolved to %s instead of %s for %s",
                version_code,
                resolved_version.group(1) if resolved_version else "unknown",
                version,
                app_name,
            )
        except Exception as e:
            logging.warning(
                "APKPure pinned download lookup failed for %s v%s: %s",
                app_name,
                version,
                e,
            )

    # APKPure often uses a specific structure for download pages
    url = f"https://apkpure.net/{config['name']}/{config['package']}/download/{version}"

    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        
        content_size = len(response.content)
        logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> \"-\" [1]")
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for the download link; APKPure sometimes uses 'download_link' or 'fast-download'
        download_link = soup.find('a', id='download_link')
        if download_link:
            return download_link['href']
            
    except Exception as e:
        logging.error(f"Failed to fetch download link for {app_name} v{version}: {e}")
    
    return None
