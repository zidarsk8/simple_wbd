"""Unit tests for wbd climate api."""

import unittest
import os

import vcr

import simple_wbd
from simple_wbd import utils


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VCR_CASSETTES = os.path.join(CURRENT_DIR, "vcr_cassettes")

MY_VCR = vcr.VCR(
    serializer="json",
    cassette_library_dir=VCR_CASSETTES,
    record_mode="none",  # none - used for testing, all - used for updating
)


class TestUtils(unittest.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    def setUp(self):
        utils.remove_cache_dir()
        self.api = simple_wbd.ClimateAPI()

    @MY_VCR.use_cassette("climate.json")
    def test_get_instrumental_specific(self):
        """Test specific instrumental data query."""
        response = self.api.get_instrumental(
            ["SVN"], data_types=["pr"], intervals=["month"])
        self.assertIn("SVN", response.api_responses)
        self.assertIn("pr", response.api_responses["SVN"])
        self.assertIn("month", response.api_responses["SVN"]["pr"])

    @MY_VCR.use_cassette("climate.json")
    def test_get_instrumental_generic(self):
        """Test generic instrumental data query."""
        locations = ["SVN", "TUN"]
        response = self.api.get_instrumental(locations)
        self.assertEqual(set(locations), set(response.api_responses))
        self.assertEqual(set(self.api.INSTRUMENTAL_TYPES),
                         set(response.api_responses["SVN"]))
        self.assertEqual(set(self.api.INSTRUMENTAL_INTERVALS),
                         set(response.api_responses["SVN"]["pr"]))

    def test_get_location_good(self):
        """Test get location with proper locations."""
        # pylint: disable=protected-access
        self.assertEqual(("country", "SVN"), self.api._get_location("SI"))
        self.assertEqual(("country", "TON"), self.api._get_location("Tonga"))
        self.assertEqual(("country", "USA"), self.api._get_location("us"))
        self.assertEqual(("basin", "1"), self.api._get_location("1"))
        self.assertEqual(("basin", "28"), self.api._get_location("28"))

    def test_get_location_bad(self):
        """Test get location with invalid locations."""
        # pylint: disable=protected-access
        bad_locations = ["-1", "Orange3", "books", "555", "XYZ1"]
        for location in bad_locations:
            self.assertRaises(ValueError, self.api._get_location, location)
