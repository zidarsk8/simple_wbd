"""Unit tests for wbd climate api."""

import tests
import simple_wbd


class TestClimateDataset(tests.TestCase):
    """Tests for functions in simple_wbd.IndicatorDataset class."""

    def setUp(self):
        self.dataset = simple_wbd.ClimateDataset(self.dummy_response)

    def test_as_dict(self):
        """Test generating nested dict from api responses."""
        as_dict = self.dataset.as_dict()

        self.assertEqual({"SVN", "USA"}, set(as_dict.keys()))
        self.assertEqual({"pr", "tas"}, set(as_dict["USA"].keys()))
        self.assertEqual({"pr", "tas"}, set(as_dict["SVN"].keys()))
        self.assertEqual(
            {"month", "year", "decade"},
            set(as_dict["SVN"]["tas"].keys())
        )
        tas = as_dict["SVN"]["tas"]
        self.assertEqual({0, 1}, set(tas["month"].keys()))
        self.assertIn(2009, tas["year"])
        self.assertIn(1990, tas["decade"])
        self.assertNotIn("url", tas["year"])

    def test_as_list_arguments(self):
        """Test arguments for as_list method."""
        self.dataset.as_list()
        self.assertEqual(self.dataset.columns, ["type", "interval", "data"])
        self.assertEqual(self.dataset.rows, ["country"])

        self.dataset.as_list(columns=[])
        self.assertEqual(self.dataset.columns, ["type", "interval", "data"])
        self.assertEqual(self.dataset.rows, ["country"])

        self.dataset.as_list(columns=["type"])
        self.assertEqual(self.dataset.columns, ["type"])
        self.assertEqual(self.dataset.rows, ["country", "interval", "data"])

        self.dataset.as_list(columns=["country", "data"])
        self.assertEqual(self.dataset.columns, ["country", "data"])
        self.assertEqual(self.dataset.rows, ["type", "interval"])

        with self.assertRaises(TypeError):
            self.dataset.as_list(columns=["AAAA"])

    def test_gather_keys_by_level(self):
        """Test gather keys function."""
        # pylint: disable=protected-access
        # we must access protected members for testing
        keys = self.dataset._gather_key_by_level(self.dummy_response)
        self.assertEqual(keys[0], {"SVN", "USA"})
        self.assertEqual(keys[1], {"pr", "tas"})
        self.assertEqual(keys[2], {"month", "year", "decade"})
        self.assertEqual(keys[3], {"response", "url"})

    # dummy response for:
    # api.get_instrumental(["SVN", "US"], intervals=api.INSTRUMENTAL_INTERVALS)
    dummy_response = {
        "SVN": {
            "pr": {
                "month": {
                    "response": [
                        {"data": 68.93643, "month": 0},
                        {"data": 64.23069, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/month/SVN"
                },
                "year": {
                    "response": [
                        {"data": 10.643, "year": 2008},
                        {"data": 10.658667, "year": 2009},
                        {"data": 9.153704, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/SVN"
                },
                "decade": {
                    "response": [
                        {"data": 58.03062, "year": 1970},
                        {"data": 64.00271, "year": 1980},
                        {"data": 57.579975, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/decade/SVN"
                },
            },
            "tas": {
                "month": {
                    "response": [
                        {"data": 15.49659, "month": 0},
                        {"data": 8.980858, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/month/SVN"
                },
                "year": {
                    "response": [
                        {"data": 7.935361, "year": 2008},
                        {"data": 8.1020646, "year": 2009},
                        {"data": 9.4091196, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/SVN"
                },
                "decade": {
                    "response": [
                        {"data": 7.6022215, "year": 1970},
                        {"data": 9.057728, "year": 1980},
                        {"data": 7.2622313, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/decade/SVN"
                },
            },
        },
        "USA": {
            "pr": {
                "month": {
                    "response": [
                        {"data": 61.76187, "month": 0},
                        {"data": 51.977913, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/month/USA"
                },
                "year": {
                    "response": [
                        {"data": 58.170464, "year": 2008},
                        {"data": 56.836555, "year": 2009},
                        {"data": 58.305126, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/year/USA"
                },
                "decade": {
                    "response": [
                        {"data": 56.03062, "year": 1970},
                        {"data": 56.00271, "year": 1980},
                        {"data": 57.579975, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/decade/USA"
                },
            },
            "tas": {
                "month": {
                    "response": [
                        {"data": 14.49659, "month": 0},
                        {"data": 7.980858, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/month/USA"
                },
                "year": {
                    "response": [
                        {"data": 6.935361, "year": 2008},
                        {"data": 7.1020646, "year": 2009},
                        {"data": 7.4091196, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/USA"
                },
                "decade": {
                    "response": [
                        {"data": 6.6022215, "year": 1970},
                        {"data": 7.057728, "year": 1980},
                        {"data": 7.2622313, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/decade/SVN"
                },
            },
        },
    }
