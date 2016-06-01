"""Unit tests for world bank data indicator API."""

import mock
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

    @mock.patch("requests.get")
    def test_filter_indicators(self, get):
        """Test _filter_indicators function."""
        # pylint: disable=protected-access
        get().text = """
            <html>dummy html
                <a href="http://data.worldbank.org/indicator/AG.YLD.CREL.KG">
                    Cereal yield (kg per hectare)</a>
                <a href="http://data.worldbank.org/indicator/2.0.hoi.Cel">
                    Coverage: Water</a>
                <a href="http://data.worldbank.org/indicator/4.4_BASIC.EDU">
                    Cereal cropland (% of land area)</a>
                <a href="http://data.worldbank.org/indicator/A7iv">
                    14.Export Value per Entrant: First Quartile</a>
            </html>"""

        bad_indicators = [
            {"id": "bad indicator"},
            {"id": "A7"},
            {"id": "A7ivi"},
            {"id": "BASIC"},
            {"id": "."},
            {"id": "2.0.hoi."},
        ]
        good_indicators = [
            {"id": "a7iv"},
            {"id": "2.0.hoi.Cel"},
            {"id": "2.0.HOI.cEL"},
            {"id": "AG.YLD.CREL.KG"},
        ]

        all_indicators = bad_indicators + good_indicators
        filtered = self.api._filter_indicators(all_indicators, "common")

        self.assertEqual(
            set(i.get("id").lower() for i in good_indicators),
            set(i.get("id").lower() for i in filtered),
        )

    def test_get_indicators(self):
        """Test fetching indicators with and without filters."""
        all_indicators = self.api.get_indicators(filter_=None)
        common_indicators = self.api.get_indicators()
        featured_indicators = self.api.get_indicators(filter_="featured")

        all_codes = set(i.get("id").lower() for i in all_indicators)
        featured_codes = set(i.get("id").lower() for i in featured_indicators)
        common_codes = set(i.get("id").lower() for i in common_indicators)

        self.assertLess(featured_codes, common_codes, "Wrong featured subset.")
        self.assertLess(common_codes, all_codes, "Wrong common subset.")
        self.assertIn("AG.LND.ARBL.HA.PC".lower(), featured_codes)
        self.assertNotIn("EG.ELC.ACCS.RU.ZS".lower(), featured_codes)
        self.assertIn("EG.ELC.ACCS.RU.ZS".lower(), common_codes)
