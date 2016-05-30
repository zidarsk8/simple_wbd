"""Unit tests for wbd utility functions."""

import unittest
import os
import shutil
import time

import mock
import pycountry

from simple_wbd import utils


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestUtils(unittest.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    TEST_TEMP_DIR = os.path.join(CURRENT_DIR, "test_temp_folder")

    def setUp(self):
        self.clear_cache_dir()

    def tearDown(self):
        self.remove_cache_dir()

    def remove_cache_dir(self):
        if os.path.exists(self.TEST_TEMP_DIR):
            shutil.rmtree(self.TEST_TEMP_DIR)

    def clear_cache_dir(self):
        self.remove_cache_dir()
        os.makedirs(self.TEST_TEMP_DIR)

    @mock.patch("tempfile.gettempdir")
    def test_get_cache_dir(self, gettempdir):
        """Test creating and retrieving temp folder."""
        # pylint: disable=protected-access
        gettempdir.return_value = self.TEST_TEMP_DIR
        self.remove_cache_dir()
        self.assertFalse(os.path.exists(self.TEST_TEMP_DIR))
        cache_dir = utils._get_cache_dir()
        self.assertTrue(os.path.exists(cache_dir))

    @mock.patch("requests.get")
    @mock.patch("simple_wbd.utils._get_cache_dir")
    def test_fetch_single(self, gettempdir, get):
        """Test single fetch request"""
        gettempdir.return_value = self.TEST_TEMP_DIR
        get().text = "dummy result"

        result = utils.fetch("http://api.worldbank.org/indicators?format=json")
        self.assertEqual("dummy result", result)


    @mock.patch("requests.get")
    @mock.patch("os.path.getmtime")
    @mock.patch("simple_wbd.utils._get_cache_dir")
    def test_fetch(self, gettempdir, getmtime, get):
        """Test fetching from cache."""
        gettempdir.return_value = self.TEST_TEMP_DIR
        getmtime.return_value = int(time.time())

        get().text = "dummy result"
        res_1 = utils.fetch("http://api.worldbank.org/indicators?format=json")
        self.assertEqual("dummy result", res_1)

        get().text = "Updated dummy Result!"
        res_2 = utils.fetch("http://google.com")
        self.assertEqual("Updated dummy Result!", res_2)

        res_1 = utils.fetch("http://api.worldbank.org/indicators?format=json")
        self.assertEqual("dummy result", res_1)

        getmtime.return_value = int(time.time()) - utils.CACHE_TIME - 10
        res_1 = utils.fetch("http://api.worldbank.org/indicators?format=json")
        self.assertEqual("Updated dummy Result!", res_1)

        get().text = "Third dummy result."
        res_2 = utils.fetch("http://google.com", use_cache=False)
        self.assertEqual("Third dummy result.", res_2)

    def test_to_alpha3(self):
        """Test getting countries ISO alpha3 code."""
        self.assertEqual("SVN", utils.to_alpha3("Slovenia"))
        self.assertEqual("SVN", utils.to_alpha3("SLOVENIA"))
        self.assertEqual("USA", utils.to_alpha3("US"))

        for country in pycountry.countries:
            self.assertEqual(country.alpha3, utils.to_alpha3(country.name))
            self.assertEqual(country.alpha3, utils.to_alpha3(country.alpha3))
            self.assertEqual(country.alpha3, utils.to_alpha3(country.alpha2))

        self.assertRaises(ValueError, lambda: utils.to_alpha3("NOT EXISTING"))
