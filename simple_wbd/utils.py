"""Utility functions for world bank APIs."""
import hashlib
import logging
import os
import tempfile
import time

import requests

logger = logging.getLogger(__name__)

CACHE_TIME = 60 * 60 * 24  # one day in seconds
CACHE_DIR_NAME = "simple_wbd_cache"


def _get_cache_dir():
    """Get the temporary cache directory.

    Get a directory for temporary cache. If one does not exist create a new one
    and return that.

    Returns:
        str: path to the current cache directory
    """
    cache_dir = os.path.join(tempfile.gettempdir(), CACHE_DIR_NAME)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logger.debug("Created cache directory: %s", cache_dir)

    return cache_dir


def fetch(url, use_cache=True):
    """Return response from a URL, and cache results for CACHE_TIME.

    Retrieve url response data form the web or cache files if they exist.

    Args:
        url (str): Url that we want to fetch from the web.
        use_cache (bool): Flag to enable or disable use of cache files.

    Returs:
        str: Response from the web. Response can be read from a file if the url
            has already been fetched and cached less than CACHE_TIME ago.
    """
    logger.debug("Fetch '%s' use cache %s", url, use_cache)
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    cache_path = os.path.join(_get_cache_dir(), url_hash)

    if use_cache and os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < CACHE_TIME:
            with open(cache_path, "rb") as cache_file:
                return cache_file.read().decode("utf-8")
        else:
            logger.info("Removing expired cache file for %s", url)
            os.remove(cache_path)

    logger.debug("Retrieving data from web.")
    response = requests.get(url).text

    with open(cache_path, "wb") as cache_file:
        cache_file.write(response.encode("utf-8"))

    return response
