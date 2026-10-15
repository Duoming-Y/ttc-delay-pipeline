"""Tests for picking files from the CKAN API response (no network needed)."""
import pytest

from ttc_pipeline import download

FAKE_PACKAGE = {"resources": [
    {"name": "ttc-subway-delay-data-2024", "url": "https://example.com/files/ttc-subway-delay-2024.xlsx"},
    {"name": "Code Descriptions.csv", "url": "https://example.com/files/code-descriptions.csv"},
]}


def test_pick_resources_returns_urls():
    urls = download.pick_resources(FAKE_PACKAGE, ["ttc-subway-delay-data-2024"])
    assert urls == {"ttc-subway-delay-data-2024": "https://example.com/files/ttc-subway-delay-2024.xlsx"}


def test_pick_resources_fails_loudly_when_a_file_is_missing():
    with pytest.raises(KeyError, match="ttc-subway-delay-data-2030"):
        download.pick_resources(FAKE_PACKAGE, ["ttc-subway-delay-data-2030"])


@pytest.mark.parametrize("name, url, expected", [
    ("ttc-subway-delay-data-2024", "https://x/ttc-subway-delay-2024.xlsx", "ttc-subway-delay-data-2024.xlsx"),
    ("Code Descriptions.csv", "https://x/code-descriptions.csv", "code-descriptions.csv"),
    ("TTC Subway Delay Data since 2025.csv", "https://x/a.csv?v=2", "ttc-subway-delay-data-since-2025.csv"),
])
def test_local_filename(name, url, expected):
    assert download.local_filename(name, url) == expected
