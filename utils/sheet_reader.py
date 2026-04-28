"""
utils/sheet_reader.py
=====================
Helpers for resolving an input-sheet source — either a local file path or a
Google Sheets URL — to a local .xlsx path that openpyxl / the rest of the
loader can consume directly.
"""

import os
import re
import tempfile
import urllib.error
import urllib.request


def is_url(path: str) -> bool:
    """Return True if *path* looks like an http/https URL."""
    return path.startswith("http://") or path.startswith("https://")


def resolve_input_sheet(source: str) -> str:
    """
    Resolve *source* to an absolute local .xlsx path.

    - Local path  → verified to exist; returned as-is.
    - Google Sheets URL → sheet ID extracted (if not already an export URL),
      exported as xlsx, downloaded to a NamedTemporaryFile, and that path is
      returned.  The caller is responsible for deleting the temp file when done.

    Raises:
        FileNotFoundError: local path does not exist.
        ValueError:        URL contains no extractable Google Sheets ID.
        urllib.error.URLError: network or HTTP error during download.
    """
    if not is_url(source):
        if not os.path.isfile(source):
            raise FileNotFoundError(
                f"Input file not found: {source} — check the path and try again"
            )
        return source

    # ── URL branch ────────────────────────────────────────────────────────────
    url = source
    if "export?format=xlsx" not in url:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if not match:
            raise ValueError(
                f"Could not extract a Google Sheets ID from the URL: {url}\n"
                "Expected a URL like: "
                "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
            )
        sheet_id = match.group(1)
        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        )

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    try:
        urllib.request.urlretrieve(url, tmp.name)
    except urllib.error.URLError:
        os.unlink(tmp.name)
        raise
    return tmp.name
