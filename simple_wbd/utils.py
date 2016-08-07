"""Utility functions for world bank APIs."""
import hashlib
import logging
import os
import tempfile
import time
import shutil
import datetime

import requests
from pycountry import countries

logger = logging.getLogger(__name__)

CACHE_TIME = 60 * 60 * 24  # one day in seconds
CACHE_DIR_NAME = "simple_wbd_cache"


class ApiBase(object):
    """Base class for indicator and climate APIs."""
    # pylint: disable=too-few-public-methods
    # This is just a base class and does not need public methods

    def __init__(self, class_=None):
        self._reset_progress()
        try:
            dataset_class = getattr(self, "_dataset_class", object)
            if class_ and issubclass(class_, dataset_class):
                self._dataset_class = class_
        except TypeError:
            logger.error("Could not use extended climate dataset class.")

    def _reset_progress(self):
        progress = getattr(self, "progress", {})
        for key in progress:
            progress[key] = 0

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


def remove_cache_dir():
    """Get the temporary cache directory.

    Get a directory for temporary cache. If one does not exist create a new one
    and return that.

    Returns:
        str: path to the current cache directory
    """
    cache_dir = os.path.join(tempfile.gettempdir(), CACHE_DIR_NAME)
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        logger.debug("Removed cache directory: %s", cache_dir)

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


def to_alpha3(country, code_map={}):
    """Get ISO alpha3 country code from alpha2 or country name.

    Args:
        country (str): ISO alpah3 or alpha2 country code or country name.
        code_map (dict): Key value store where keys are expected country names
            or ids and the values contain the propper alpha3 code. Defaults to
            map generated from pycountry using alpha2, alpha3 and country
            names.

    Returns:
        str: ISO alpha3 code for the given country.
    """
    # pylint: disable=dangerous-default-value
    # Code_map is mutable default value that is used as a cache.
    if not code_map:
        code_map.update({i.name.lower(): i.alpha3 for i in countries})
        code_map.update({i.alpha2.lower(): i.alpha3 for i in countries})
        code_map.update({i.alpha3.lower(): i.alpha3 for i in countries})

    alpha3 = code_map.get(country.lower())
    if not alpha3:
        raise ValueError("`country` is not a valid country name or alpha-2 or "
                         "alpha-3 code")
    return alpha3


def parse_wb_date(date_string):
    """Parse world bank date format.

    Change strings of type 2001Q1 or 2007M5 or 2005 into their closest date.

    Args:
        date_string: String representation of world bank date.
    Returns:
        parsed date value if the input is a valid date representation.
    """
    # pylint: disable=bare-except
    # We do not care why the parsing failed.
    try:
        date_string = date_string.upper()
        year = int(date_string[:4])
        if len(date_string) == 4:
            month = 1
        elif date_string[4] == "Q":
            month = int(date_string[5]) * 3 - 2
        elif date_string[4] == "M":
            month = int(date_string[5:7])
        return datetime.date(year, month, 1)
    except:
        logger.warning("Error parsing wb date: %s", date_string)
        return None


def flaten(data):
    list_ = [[d] if isinstance(d, (str, int)) else flaten(d) for d in data]
    return sum(list_, [])
