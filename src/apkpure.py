import json
import logging
import re
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


def _resolve_latest(package: str) -> tuple[str, str] | None:
    """Return (download url, version) from APKPure's download host, or None.

    apkpure.net answers datacenter IPs with a Cloudflare challenge; this host
    does not, but it only ever serves the current release.
    """
    for kind in ("APK", "XAPK"):
        url = f"https://d.apkpure.com/b/{kind}/{package}?version=latest"
        try:
            response = session.get(url, timeout=25, allow_redirects=False)
        except Exception as e:
            logging.debug(f"APKPure download host failed for {package}: {e}")
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


def get_latest_version(app_name: str, config: str) -> str:
    resolved = _resolve_latest(config['package'])
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

def get_download_link(version: str, app_name: str, config: str) -> str:
    resolved = _resolve_latest(config['package'])
    if resolved:
        download_url, latest = resolved
        if latest == version:
            return download_url
        logging.info(
            f"APKPure serves only {latest} for {app_name}; {version} needs another source"
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
