"""Step 1 - Download the raw data files from the City of Toronto Open Data portal.

The portal runs CKAN, which has a JSON API. `package_show` returns every file
("resource") in a dataset together with its download URL, so we look files up
by name instead of hard-coding URLs that may change.
"""
from pathlib import Path

import requests

from . import config


def fetch_package(package_id=config.PACKAGE_ID, timeout=30):
    """Return the CKAN metadata for a dataset as a Python dict."""
    url = f"{config.CKAN_BASE_URL}/api/3/action/package_show"
    response = requests.get(url, params={"id": package_id}, timeout=timeout)
    response.raise_for_status()  # stop with an error on HTTP 4xx/5xx
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"CKAN API returned an error for {package_id!r}")
    return body["result"]


def pick_resources(package, wanted_names):
    """Map each wanted resource name to its download URL.

    Raises KeyError if a wanted file is missing, so a renamed file on the
    portal fails loudly instead of silently dropping a year of data.
    """
    by_name = {r["name"]: r["url"] for r in package["resources"]}
    missing = [name for name in wanted_names if name not in by_name]
    if missing:
        raise KeyError(f"Resources not found on the portal: {missing}")
    return {name: by_name[name] for name in wanted_names}


def local_filename(resource_name, url):
    """Build a safe local file name, keeping the file extension from the URL."""
    suffix = Path(url.split("?")[0]).suffix or ".csv"
    stem = resource_name.removesuffix(suffix).strip().lower().replace(" ", "-")
    return f"{stem}{suffix}"


def download_file(url, destination, timeout=120):
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def download_all(refresh=False):
    """Download every file the pipeline needs into data/raw/.

    Files already on disk are reused unless refresh=True.
    Returns {resource name: local path}.
    """
    wanted = list(config.DELAY_RESOURCES) + [config.CODES_RESOURCE]
    urls = pick_resources(fetch_package(), wanted)
    paths = {}
    for name, url in urls.items():
        path = config.RAW_DIR / local_filename(name, url)
        if refresh or not path.exists():
            print(f"  downloading {name} ...")
            download_file(url, path)
        paths[name] = path
    return paths
