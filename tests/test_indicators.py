"""Unit tests for world bank data indicator API."""

import pycountry

import simple_wbd
import tests


class TestIndicatorDataset(tests.TestCase):
    """Tests for IndicatorDataset class and its functions."""

    # pylint: disable=protected-access
    # Protected access lint warning is disabled so we can test the protected
    # methods.

    def setUp(self):
        self.dataset = simple_wbd.IndicatorDataset(self.dummy_response)

    def test_parse_value(self):
        """Test parse value function."""
        bad_values = [None, "uoea", "--2-", ""]
        for value in bad_values:
            self.assertEqual(self.dataset._parse_value(value), None)

        bad_values = [0, 55, 753.420, -5]
        for value in bad_values:
            self.assertEqual(self.dataset._parse_value(str(value)), value)

    def test_get_dates(self):
        """Test getting all unique dates from single indicator dataset."""
        dates = self.dataset._get_dates(self.dummy_response["ind 1"])
        expected_dates = ['1998Q2', '2000Q1', '2015Q2', '2015Q3']
        self.assertEqual(dates, expected_dates)

    def test_get_clean_data_map(self):
        """Test basic get_data_map calls."""
        data = self.dummy_response["ind 1"]
        data_map = self.dataset._get_data_map(data)
        self.assertEqual({"Brazil", "Belgium"}, set(data_map.keys()))
        self.assertEqual({"1998Q2", "2000Q1"}, set(data_map["Brazil"].keys()))

    def test_get_updated_data_map(self):
        """Advanced tests for _get_data_map function.

        - Test if prefixes get prepended to country and date keys.
        - Test updating existing data_map.
        """
        data_map = self.dataset._get_data_map(
            self.dummy_response["ind 1"])
        self.dataset._get_data_map(
            self.dummy_response["ind 2"],
            data_map=data_map,
            country_prefix="2 - ",
            date_prefix="2 - ",
        )
        self.assertEqual(
            {"Brazil", "Belgium", "2 - Low & middle income"},
            set(data_map.keys())
        )
        self.assertEqual(
            {"2 - 1970", "2 - 1971", "2 - 1972"},
            set(data_map["2 - Low & middle income"].keys())
        )

    def test_get_all_dates(self):
        """Test collecting all dates from data_map

        - Test if prefixes get prepended to country and date keys.
        - Test updating existing data_map.
        """
        data_map = self.dataset._get_data_map(
            self.dummy_response["ind 1"],
            date_prefix="1 - ",
        )
        self.dataset._get_data_map(
            self.dummy_response["ind 2"],
            data_map=data_map,
            date_prefix="2 - ",
        )
        self.assertEqual(
            [
                "1 - 1998Q2",
                "1 - 2000Q1",
                "1 - 2015Q2",
                "1 - 2015Q3",
                "2 - 1970",
                "2 - 1971",
                "2 - 1972"
            ],
            self.dataset._get_all_dates(data_map)
        )

    def test_get_all_countries(self):
        """Test fetching all country keys with prefixes."""
        data_map = self.dataset._get_data_map(
            self.dummy_response["ind 1"],
            country_prefix="1 - ",
        )
        self.dataset._get_data_map(
            self.dummy_response["ind 2"],
            data_map=data_map,
            country_prefix="2 - ",
        )
        self.assertEqual(
            [
                "1 - Belgium",
                "1 - Brazil",
                "2 - Low & middle income",
            ],
            self.dataset._get_all_countries(data_map)
        )

    def test_as_list_multiple(self):
        """Test as_list function for multiple indicators."""
        # pylint: disable=bad-whitespace,line-too-long
        # Disable bad formatting lint warnings for readability.
        expected_list = [
            ['Country',            'ind 1 - 1998Q2', 'ind 1 - 2000Q1', 'ind 1 - 2015Q2', 'ind 1 - 2015Q3', 'ind 2 - 1970', 'ind 2 - 1971', 'ind 2 - 1972'],  # noqa
            ['Belgium',             0.0,              0.0,              126.0,            87.0,             0.0,            0.0,            0.0],  # noqa
            ['Brazil',              131.0,            97.0,             0.0,              0.0,              0.0,            0.0,            0.0],  # noqa
            ['Low & middle income', 0.0,              0.0,              0.0,              0.0,              None,           12.3,           1.23],  # noqa
        ]
        self.assertEqual(
            expected_list,
            self.dataset.as_list()
        )

    def test_as_list_single(self):
        """Test as_list function for a single indicator."""
        # pylint: disable=bad-whitespace
        # Disable bad formatting lint warnings for readability.

        self.dataset.api_responses = {"ind 1": self.dummy_response["ind 1"]}
        expected_list = [
            ['Country', '1998Q2', '2000Q1', '2015Q2', '2015Q3'],
            ['Belgium',  0.0,      0.0,      126.0,    87.0],
            ['Brazil',   131.0,    97.0,     0.0,      0.0],
        ]
        self.assertEqual(
            expected_list,
            self.dataset.as_list()
        )

    def test_as_list_empty(self):
        """Test as_list function for empty dataset."""
        self.dataset.api_responses = {}
        self.assertEqual([], self.dataset.as_list())

    dummy_response = {
        "ind 1": [{
            'country': {'id': 'BR', 'value': 'Brazil'},
            'date': '1998Q2',
            'decimal': '0',
            'indicator': {'id': 'ind 1', 'value': 'description'},
            'value': "131"
        }, {
            'country': {'id': 'BR', 'value': 'Brazil'},
            'date': '2000Q1',
            'decimal': '0',
            'indicator': {'id': 'ind 1', 'value': 'description'},
            'value': "97"
        }, {
            'country': {'id': 'BE', 'value': 'Belgium'},
            'date': '2015Q3',
            'decimal': '0',
            'indicator': {'id': 'ind 1', 'value': 'description'},
            'value': "87"
        }, {
            'country': {'id': 'BE', 'value': 'Belgium'},
            'date': '2015Q2',
            'decimal': '0',
            'indicator': {'id': 'ind 1', 'value': 'description'},
            'value': "126"
        }],
        "ind 2": [{
            'country': {'id': 'XO', 'value': 'Low & middle income'},
            'date': '1972',
            'decimal': '1',
            'indicator': {'id': 'ind 2', 'value': 'employment'},
            'value': "1.23"
        }, {
            'country': {'id': 'XO', 'value': 'Low & middle income'},
            'date': '1971',
            'decimal': '1',
            'indicator': {'id': 'ind 2', 'value': 'employment'},
            'value': "12.3"
        }, {
            'country': {'id': 'XO', 'value': 'Low & middle income'},
            'date': '1970',
            'decimal': '1',
            'indicator': {'id': 'ind 2', 'value': 'employment'},
            'value': None
        }],
    }


class TestIndicators(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    NUM_OF_COUNTRIES = 264

    def setUp(self):
        super().setUp()
        self.api = simple_wbd.IndicatorAPI()

    @tests.MY_VCR.use_cassette("country_list.json")
    def test_get_country_list(self):
        """Test fetching a 2D list of country and region codes."""
        country_list = self.api.get_country_list()
        # number of countries + one line for header
        self.assertEqual(self.NUM_OF_COUNTRIES+1, len(country_list))

    @tests.MY_VCR.use_cassette("countries.json")
    def test_get_countries(self):
        """Test fetching all country and region codes."""
        all_codes = self.api.get_countries()
        self.assertEqual(self.NUM_OF_COUNTRIES, len(all_codes))
        countries = set(c["id"] for c in all_codes if c["capitalCity"])
        alpha3_codes = set(c.alpha3 for c in pycountry.countries)
        alpha3_codes.add("KSV")  # Non standard code for Kosovo.
        self.assertLess(countries, alpha3_codes)

    def test_filter_indicators(self):
        """Test _filter_indicators function."""
        # pylint: disable=protected-access

        bad_indicators = [
            {"id": "bad indicator"},
            {"id": "A7"},
            {"id": "A7ivi"},
            {"id": "BASIC"},
            {"id": "."},
            {"id": "2.0.hoi."},
        ]
        good_indicators = [
            {"id": "ag.lnd.frst.k2"},
            {"id": "ag.LND.FRst.zs"},
            {"id": "AG.LND.FRST.ZS"},
            {"id": "ag.lnd.irig.ag.zs"},
            {"id": "ag.lnd.totl.k2"},
        ]

        all_indicators = bad_indicators + good_indicators
        filtered = self.api._filter_indicators(all_indicators, "common")

        self.assertEqual(
            set(i.get("id").lower() for i in good_indicators),
            set(i.get("id").lower() for i in filtered),
        )

    @tests.MY_VCR.use_cassette("indicators_list.json")
    def test_get_indicator_list(self):
        """Test fetching indicators with and without filters."""
        all_indicators = self.api.get_indicator_list(filter_=None)
        common_indicators = self.api.get_indicator_list()
        featured_indicators = self.api.get_indicator_list(filter_="featured")

        self.assertEqual(all_indicators[0], common_indicators[0])
        self.assertEqual(all_indicators[0], featured_indicators[0])
        self.assertLess(len(featured_indicators), len(common_indicators))
        self.assertLess(len(common_indicators), len(all_indicators))

    @tests.MY_VCR.use_cassette("indicators.json")
    def test_get_indicators(self):
        """Test fetching indicators with and without filters."""
        all_indicators = self.api.get_indicators(filter_=None)
        common_indicators = self.api.get_indicators()
        featured_indicators = self.api.get_indicators(filter_="featured")

        all_codes = set(i.get("id").lower() for i in all_indicators)
        featured_codes = set(i.get("id").lower() for i in featured_indicators)
        common_codes = set(i.get("id").lower() for i in common_indicators)

        self.assertLess(featured_codes, all_codes, "Wrong featured subset.")
        self.assertLess(common_codes, all_codes, "Wrong common subset.")
        self.assertIn("AG.LND.ARBL.HA.PC".lower(), featured_codes)
        self.assertNotIn("ag.agr.trac.no".lower(), featured_codes)
        self.assertIn("ag.agr.trac.no".lower(), common_codes)

    @tests.MY_VCR.use_cassette("datasets.json")
    def test_get_dataset(self):
        """Test fetching datasests."""
        res = self.api.get_dataset("SL.MNF.0714.FE.ZS")
        self.assertIn("SL.MNF.0714.FE.ZS".lower(), res.api_responses)

        res = self.api.get_dataset(
            ["dp.dod.decx.cr.bc.z1", "SL.MNF.0714.FE.ZS", "2.0.HOI.cEL"],
            countries=["Svn", "us", "World"]
        )
        self.assertIn("SL.MNF.0714.FE.ZS".lower(), res.api_responses)
        self.assertIn("dp.dod.decx.cr.bc.z1".lower(), res.api_responses)
        self.assertIn("2.0.HOI.cEL".lower(), res.api_responses)

        ind_data = res.api_responses["SL.MNF.0714.FE.ZS".lower()]
        response_countries = set(i["country"]["value"] for i in ind_data)
        self.assertEqual(
            set(["United States", "Slovenia", "World"]),
            response_countries
        )

    @tests.MY_VCR.use_cassette("datasets2.json")
    def test_get_dataset_with_errors(self):
        """Test fetching datasests with bad parameters."""
        res = self.api.get_dataset(
            ["SL.MNF.0714.FE.ZS", "BAD Indicator"],
            countries=["Svn", "us", "bad country"]
        )
        self.assertIn("SL.MNF.0714.FE.ZS".lower(), res.api_responses)
        self.assertNotIn("BAD Indicator".lower(), res.api_responses)

        ind_data = res.api_responses["SL.MNF.0714.FE.ZS".lower()]
        response_countries = set(i["country"]["value"] for i in ind_data)
        self.assertEqual(
            set(["United States", "Slovenia"]),
            response_countries
        )

        # If there is no good country parameter, we default to all
        res = self.api.get_dataset("SL.MNF.0714.FE.ZS", countries="badd")
        ind_data = res.api_responses["SL.MNF.0714.FE.ZS".lower()]
        response_countries = set(i["country"]["value"] for i in ind_data)
        self.assertLess(
            set(["United States", "Slovenia"]),
            response_countries
        )
