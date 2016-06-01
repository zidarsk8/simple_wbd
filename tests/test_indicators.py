"""Unit tests for world bank data indicator API."""

import unittest
import pycountry
import os

import vcr

import simple_wbd
from simple_wbd import utils


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
        utils.remove_cache_dir()
        self.api = simple_wbd.IndicatorAPI()

    @MY_VCR.use_cassette("indicators.json")
    def test_get_countries(self):
        """Test fetching all country and region codes."""
        all_codes = self.api.get_countries()
        self.assertEqual(264, len(all_codes))
        countries = set(c["id"] for c in all_codes if c["capitalCity"])
        alpha3_codes = set(c.alpha3 for c in pycountry.countries)
        alpha3_codes.add("KSV")  # Non standard code for Kosovo.
        self.assertLess(countries, alpha3_codes)
