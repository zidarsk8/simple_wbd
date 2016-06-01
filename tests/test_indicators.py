"""Unit tests for world bank data indicator API."""

import pycountry

import simple_wbd
import tests


class TestIndicators(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    def setUp(self):
        super().setUp()
        self.api = simple_wbd.IndicatorAPI()

    @tests.MY_VCR.use_cassette("indicators.json")
    def test_get_countries(self):
        """Test fetching all country and region codes."""
        all_codes = self.api.get_countries()
        self.assertEqual(264, len(all_codes))
        countries = set(c["id"] for c in all_codes if c["capitalCity"])
        alpha3_codes = set(c.alpha3 for c in pycountry.countries)
        alpha3_codes.add("KSV")  # Non standard code for Kosovo.
        self.assertLess(countries, alpha3_codes)
