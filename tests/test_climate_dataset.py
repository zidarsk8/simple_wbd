"""Unit tests for wbd climate api."""

import mock
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
        self.dataset._generate_list = mock.MagicMock()
        self.dataset.as_list()
        self.assertEqual(self.dataset.columns, ["type", "interval"])
        self.assertEqual(self.dataset.rows, ["country"])

        self.dataset.as_list(columns=[])
        self.assertEqual(self.dataset.columns, ["type", "interval"])
        self.assertEqual(self.dataset.rows, ["country"])

        self.dataset.as_list(columns=["type"])
        self.assertEqual(self.dataset.columns, ["type"])
        self.assertEqual(self.dataset.rows, ["country", "interval"])

        self.dataset.as_list(columns=["country", "interval"])
        self.assertEqual(self.dataset.columns, ["country", "interval"])
        self.assertEqual(self.dataset.rows, ["type"])

        self.dataset.as_list(columns=["country"])
        self.assertEqual(self.dataset.columns, ["country"])
        self.assertEqual(self.dataset.rows, ["type", "interval"])

        with self.assertRaises(TypeError):
            self.dataset.as_list(columns=["AAAA"])

    def test_as_list(self):
        # pylint: disable=bad-whitespace,line-too-long
        # Disable bad formatting lint warnings for readability.
        array = self.dataset.as_list()
        self.assertEqual(len(array), 3)
        self.assertEqual(len(array[0]), len(array[1]))
        self.assertEqual(len(array[0]), len(array[2]))

        expected = [[
            'country',
            'pr - decade - 1970',
            'pr - decade - 1980',
            'pr - decade - 1990',
            'pr - month - 0',
            'pr - month - 1',
            'pr - year - 2008',
            'pr - year - 2009',
            'pr - year - 2010',
            'tas - decade - 1970',
            'tas - decade - 1980',
            'tas - decade - 1990',
            'tas - month - 0',
            'tas - month - 1',
            'tas - year - 2008',
            'tas - year - 2009',
            'tas - year - 2010'],
            ['SVN', 6, 7, 8, 1, 2, 3, 4, 5, 14, 15, 16, 9, 10, 11, 12, 13],
            ['USA', 22, 23, 24, 17, 18, 19, 20, 21, 30, 31, 32, 25, 26, 27, 28,
             29],
        ]
        self.assertEqual(expected, array)

    def test_gather_keys_by_level(self):
        """Test gather keys function."""
        # pylint: disable=protected-access
        # we must access protected members for testing
        data = self.dataset.as_dict()
        keys = self.dataset._gather_keys(data)

        self.assertEqual(keys[0], {"SVN", "USA"})
        self.assertEqual(keys[1], {"pr", "tas"})
        self.assertEqual(keys[2], {"month", "year", "decade"})
        self.assertEqual(keys[3], {0, 1, 1970, 1980, 1990, 2010, 2009, 2008})

    def test_gather_keys_by_level(self):
        """Test gather keys function."""
        # pylint: disable=protected-access
        # we must access protected members for testing
        keys = self.dataset._gather_keys_by_level(self.dummy_response)
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
                        {"data": 1, "month": 0},
                        {"data": 2, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/month/SVN"
                },
                "year": {
                    "response": [
                        {"data": 3, "year": 2008},
                        {"data": 4, "year": 2009},
                        {"data": 5, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/SVN"
                },
                "decade": {
                    "response": [
                        {"data": 6, "year": 1970},
                        {"data": 7, "year": 1980},
                        {"data": 8, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/decade/SVN"
                },
            },
            "tas": {
                "month": {
                    "response": [
                        {"data": 9, "month": 0},
                        {"data": 10, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/month/SVN"
                },
                "year": {
                    "response": [
                        {"data": 11, "year": 2008},
                        {"data": 12, "year": 2009},
                        {"data": 13, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/SVN"
                },
                "decade": {
                    "response": [
                        {"data": 14, "year": 1970},
                        {"data": 15, "year": 1980},
                        {"data": 16, "year": 1990},
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
                        {"data": 17, "month": 0},
                        {"data": 18, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/month/USA"
                },
                "year": {
                    "response": [
                        {"data": 19, "year": 2008},
                        {"data": 20, "year": 2009},
                        {"data": 21, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/year/USA"
                },
                "decade": {
                    "response": [
                        {"data": 22, "year": 1970},
                        {"data": 23, "year": 1980},
                        {"data": 24, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/pr/decade/USA"
                },
            },
            "tas": {
                "month": {
                    "response": [
                        {"data": 25, "month": 0},
                        {"data": 26, "month": 1},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/month/USA"
                },
                "year": {
                    "response": [
                        {"data": 27, "year": 2008},
                        {"data": 28, "year": 2009},
                        {"data": 29, "year": 2010},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/year/USA"
                },
                "decade": {
                    "response": [
                        {"data": 30, "year": 1970},
                        {"data": 31, "year": 1980},
                        {"data": 32, "year": 1990},
                    ],
                    "url": "http://climatedataapi.worldbank.org/climateweb/"
                           "rest/v1/country/cru/tas/decade/SVN"
                },
            },
        },
    }
