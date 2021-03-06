"""Unit tests for wbd utility functions."""

import os
import time
from datetime import date

import mock
import pycountry

import tests
from simple_wbd import utils


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestUtils(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    @mock.patch("tempfile.gettempdir")
    def test_remove_cache_dir(self, gettempdir):
        """Test removing temp folder."""
        # pylint: disable=protected-access
        gettempdir.return_value = self.TEST_TEMP_DIR
        cache_dir = utils._get_cache_dir()
        self.assertTrue(os.path.exists(cache_dir))
        utils.remove_cache_dir()
        self.assertFalse(os.path.exists(cache_dir))

    @mock.patch("tempfile.gettempdir")
    def test_get_cache_dir(self, gettempdir):
        """Test creating and retrieving temp folder."""
        # pylint: disable=protected-access
        gettempdir.return_value = self.TEST_TEMP_DIR
        self.remove_temp_dir()
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

    def test_parse_wb_date(self):
        """Test parse_wb_date function."""
        self.assertEqual(utils.parse_wb_date("2002"), date(2002, 1, 1))
        self.assertEqual(utils.parse_wb_date("2000M5"), date(2000, 5, 1))
        self.assertEqual(utils.parse_wb_date("2000Q1"), date(2000, 1, 1))
        self.assertEqual(utils.parse_wb_date("2000Q3"), date(2000, 7, 1))
        self.assertIs(utils.parse_wb_date("2000Q6"), None)
        self.assertIs(utils.parse_wb_date("200- 0Q6"), None)
        self.assertIs(utils.parse_wb_date(""), None)
