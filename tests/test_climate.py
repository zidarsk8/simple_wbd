"""Unit tests for wbd climate api."""

import unittest
import os

import vcr

import simple_wbd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VCR_CASSETTES = os.path.join(CURRENT_DIR, "vcr_cassettes")

MY_VCR = vcr.VCR(
    serializer="json",
    cassette_library_dir=VCR_CASSETTES,
    record_mode="all",  # none - used for testing, all - used for updating
)


class TestUtils(unittest.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    def setUp(self):
        self.api = simple_wbd.ClimateAPI()

    @MY_VCR.use_cassette("climate.json")
    def test_get_instrumental(self):
        pass

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
