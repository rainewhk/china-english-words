"""
Manage the Moby Project's corpus of English words.

Downloads all text files from Project Gutenberg's Moby Word Lists
(https://www.gutenberg.org/files/3201/files/) and merges them into a
single set of unique words. Downloaded files are cached locally to avoid
repeated downloads. Retries are built in for robustness. The file list
itself is also cached to allow completely offline use after the first run.
"""
import os
import pathlib
import re
import time
from typing import List, Set

import requests

# URL of the Apache directory listing for the word list files
_LISTING_URL = "https://www.gutenberg.org/files/3201/files/"
_BASE_URL = _LISTING_URL

# Default cache directory
_DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "moby_corpus")
# File where the list of .txt file names is cached
_FILE_LIST_CACHE = "file_list.txt"

# Maximum number of retries per file download
_MAX_RETRIES = 3
_REQUEST_TIMEOUT = 30


def _fetch_file_names(
    listing_url: str = _LISTING_URL,
    cache_dir: str = _DEFAULT_CACHE_DIR,
) -> List[str]:
    """
    Get the list of .txt file names from the Apache directory listing.

    If the network request succeeds, the list is saved to a cache file.
    If the request fails, the cached list is used as a fallback.

    Args:
        listing_url: URL of the directory listing page.
        cache_dir: Directory where the cached file list is stored.

    Returns:
        List of .txt file names.

    Raises:
        RuntimeError: If the listing cannot be fetched and no cache exists.
    """
    cache_path = os.path.join(cache_dir, _FILE_LIST_CACHE)
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

    # Try to fetch the live list
    try:
        response = requests.get(listing_url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        matches = re.findall(r'href="([^"]+\.txt)"', response.text, re.IGNORECASE)
        if not matches:
            raise RuntimeError("No .txt files found on the listing page.")
        # Update the cache file
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write("\n".join(matches))
        return matches
    except (requests.RequestException, RuntimeError) as e:
        # Network or parsing failed; fall back to cached file list
        if os.path.isfile(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                return lines
        # No fallback available
        raise RuntimeError(
            "Cannot obtain file list from network or local cache."
        ) from e


class WordListCorpusReader:
    """Reader for the Moby Project word lists with robust caching."""

    def __init__(self, cache_dir: str = _DEFAULT_CACHE_DIR):
        self._cache_dir = cache_dir
        self._file_list_cache = os.path.join(cache_dir, _FILE_LIST_CACHE)
        # Ensure the cache directory exists
        pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

    def _download_one(self, filename: str, dest_path: str) -> None:
        """Download a single file with retries and atomic write."""
        url = _BASE_URL + filename
        last_exception = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = requests.get(url, timeout=_REQUEST_TIMEOUT)
                response.raise_for_status()
                tmp_path = dest_path + ".tmp"
                with open(tmp_path, "wb") as f:
                    f.write(response.content)
                os.replace(tmp_path, dest_path)
                return
            except requests.RequestException as e:
                last_exception = e
                if attempt < _MAX_RETRIES:
                    time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed to download {url} after {_MAX_RETRIES} attempts"
        ) from last_exception

    def download(self, force: bool = False) -> None:
        """
        Ensure all known word list files are in the cache.

        The file list is obtained live (or from cache if offline).
        Missing files are downloaded; existing ones are left untouched
        unless *force* is ``True``.

        Args:
            force: If ``True``, re‑download every file even if cached.
        """
        file_names = _fetch_file_names(cache_dir=self._cache_dir)

        for fname in file_names:
            fpath = os.path.join(self._cache_dir, fname)
            if force or not os.path.isfile(fpath):
                # This will require network access
                self._download_one(fname, fpath)

    def all(self, force_download: bool = False) -> Set[str]:
        """
        Return a set of all unique words from the Moby corpus.

        Files are downloaded only if missing (or if *force_download*
        is True). The word set is built entirely from the local cache,
        so it works offline after the initial download.

        Args:
            force_download: If ``True``, re‑fetch every file before
                            building the word set.

        Returns:
            A set of unique, stripped word strings.
        """
        self.download(force=force_download)

        # Read every .txt file that currently exists in the cache directory.
        # Because download() ensures that all files from the (possibly
        # cached) file list are present, this covers the whole corpus.
        words: Set[str] = set()
        cache_path = pathlib.Path(self._cache_dir)
        for txt_file in sorted(cache_path.glob("*.txt")):
            # The file_list.txt cache itself is also a .txt file; skip it.
            if txt_file.name == _FILE_LIST_CACHE:
                continue
            with open(txt_file, "r", encoding="latin-1", errors="ignore") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped:
                        words.add(stripped)
        return words


def words(cache_dir: str = _DEFAULT_CACHE_DIR, force_download: bool = False) -> Set[str]:
    """
    Download (if needed) the Moby corpus and return all unique words.

    This is a convenience wrapper around :class:`WordListCorpusReader`.

    Args:
        cache_dir: Directory to store the cached word list files.
        force_download: If ``True``, force re‑download of all files.

    Returns:
        A set of unique words.
    """
    return WordListCorpusReader(cache_dir).all(force_download=force_download)
