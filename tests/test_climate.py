"""Unit tests for wbd climate api."""

import simple_wbd
import tests


class TestUtils(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    def setUp(self):
        super().setUp()
        self.api = simple_wbd.ClimateAPI()

    def test_init(self):
        """Test Climate api init function.

        Test if the default response class gets set correctly if the given
        class is a subclass of ClimateDataset.
        """
        # pylint: disable=protected-access

        class Dummy(object):
            # pylint: disable=too-few-public-methods
            pass

        class DummyClimateSubclass(simple_wbd.ClimateDataset):
            # pylint: disable=too-few-public-methods
            pass

        api = simple_wbd.ClimateAPI()
        self.assertEqual(api._dataset_class, simple_wbd.ClimateDataset)

        api = simple_wbd.ClimateAPI(Dummy)
        self.assertEqual(api._dataset_class, simple_wbd.ClimateDataset)

        api = simple_wbd.ClimateAPI("bad data")
        self.assertEqual(api._dataset_class, simple_wbd.ClimateDataset)

        api = simple_wbd.ClimateAPI(DummyClimateSubclass)
        self.assertEqual(api._dataset_class, DummyClimateSubclass)

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
