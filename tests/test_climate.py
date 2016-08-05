"""Unit tests for wbd climate api."""

import simple_wbd
import tests


class TestUtils(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    def setUp(self):
        super().setUp()
        self.api = simple_wbd.ClimateAPI()

    @tests.MY_VCR.use_cassette("climate.json")
    def test_get_instrumental_specific(self):
        """Test specific instrumental data query."""
        response = self.api.get_instrumental(
            ["SVN"], data_types=["pr"], intervals=["month"])
        self.assertIn("SVN", response.api_responses)
        self.assertIn("pr", response.api_responses["SVN"])
        self.assertIn("month", response.api_responses["SVN"]["pr"])

    @tests.MY_VCR.use_cassette("climate.json")
    def test_get_instrumental_generic(self):
        """Test generic instrumental data query."""
        # pylint: disable=protected-access
        # We need access to api protected members for testing
        locations = ["SVN", "TUN"]
        response = self.api.get_instrumental(locations)
        self.assertEqual(set(locations), set(response.api_responses))
        self.assertEqual(set(self.api.INSTRUMENTAL_TYPES),
                         set(response.api_responses["SVN"]))
        self.assertEqual(set(self.api._default_intervals),
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
