"""Tests for indicator dataset class."""

import tests
import simple_wbd
from simple_wbd import utils


class TestIndicatorDataset(tests.TestCase):
    """Tests for IndicatorDataset class and its functions."""

    # pylint: disable=protected-access
    # Protected access lint warning is disabled so we can test the protected
    # methods.

    def setUp(self):
        self.dataset = simple_wbd.IndicatorDataset(
            self.dummy_response, self.dummy_countries)

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

    def test_as_list_multiple_transpose(self):
        """Test as_list function for multiple indicators."""
        # pylint: disable=bad-whitespace,line-too-long
        # Disable bad formatting lint warnings for readability.
        expected_list = [
            ['Date',                        'ind 1 - Belgium', 'ind 1 - Brazil', 'ind 2 - Low & middle income'],  # noqa
            [utils.parse_wb_date('1970'),   0.0,               0.0,              None],  # noqa
            [utils.parse_wb_date('1971'),   0.0,               0.0,              12.3],  # noqa
            [utils.parse_wb_date('1972'),   0.0,               0.0,              1.23],  # noqa
            [utils.parse_wb_date('1998Q2'), 0.0,               131.0,            0.0],  # noqa
            [utils.parse_wb_date('2000Q1'), 0.0,               97.0,             0.0],  # noqa
            [utils.parse_wb_date('2015Q2'), 126.0,             0.0,              0.0],  # noqa
            [utils.parse_wb_date('2015Q3'), 87.0,              0.0,              0.0],  # noqa
        ]

        self.assertEqual(
            expected_list,
            self.dataset.as_list(time_series=True)
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

    def test_as_list_single_transpose(self):
        """Test as_list function for a single indicator."""
        # pylint: disable=bad-whitespace
        # Disable bad formatting lint warnings for readability.

        self.dataset.api_responses = {"ind 1": self.dummy_response["ind 1"]}
        expected_list = [
            ['Date',                        'Belgium', 'Brazil'],
            [utils.parse_wb_date('1998Q2'),  0.0,       131.0],
            [utils.parse_wb_date('2000Q1'),  0.0,       97.0],
            [utils.parse_wb_date('2015Q2'),  126.0,     0.0],
            [utils.parse_wb_date('2015Q3'),  87.0,      0.0],
        ]

        self.assertEqual(
            expected_list,
            self.dataset.as_list(time_series=True)
        )

    def test_as_list_empty(self):
        """Test as_list function for empty dataset."""
        self.dataset.api_responses = {}
        self.assertEqual([], self.dataset.as_list())

    def test_bad_as_list_request(self):
        """Test invalid as_list request.

        Requesting data list as time series with metadata does not make sense
        since there is no country to append the metadata to.
        """
        self.assertEqual(
            (self.dataset.as_list(time_series=True, add_metadata=True)),
            []
        )

    def test_with_metadata(self):
        """Test fetching a list with metadata.

        Metadata adds a few more columns with extra country data. We just check
        if any extra columns have been set.
        """
        self.assertEqual(
            len(self.dataset.as_list(add_metadata=True)),
            4
        )
        self.assertEqual(
            len(self.dataset.as_list(add_metadata=True)[0]),
            14
        )

    dummy_countries = [{
        'adminregion': {'id': '', 'value': ''},
        'adminregion_text': ' ()',
        'capitalCity': '',
        'id': 'WLD',
        'incomeLevel': {'id': 'NA', 'value': 'Aggregates'},
        'incomeLevel_text': 'Aggregates (NA)',
        'iso2Code': '1W',
        'latitude': '',
        'lendingType': {'id': '', 'value': 'Aggregates'},
        'lendingType_text': 'Aggregates ()',
        'longitude': '',
        'name': 'World',
        'region': {'id': 'NA', 'value': 'Aggregates'},
        'region_text': 'Aggregates (NA)'
    }, {
        'adminregion': {'id': 'MNA', 'value': 'Middle '},
        'adminregion_text': 'Middle (MNA)',
        'capitalCity': "Sana'a",
        'id': 'YEM',
        'incomeLevel': {'id': 'LMC', 'value': 'income'},
        'incomeLevel_text': 'Lower middle income (LMC)',
        'iso2Code': 'YE',
        'latitude': '15.352',
        'lendingType': {'id': 'IDX', 'value': 'IDA'},
        'lendingType_text': 'IDA (IDX)',
        'longitude': '44.2075',
        'name': 'Yemen, Rep.',
        'region': {'id': 'MEA', 'value': 'Middle Africa'},
        'region_text': 'Middle East & North Africa (MEA)'
    }, {
        'adminregion': {'id': 'SSA', 'value': 'Sub-income)'},
        'adminregion_text': 'Sub-Saharan Africa (SSA)',
        'capitalCity': 'Lusaka',
        'id': 'ZMB',
        'incomeLevel': {'id': 'LMC', 'value': 'middle income'},
        'incomeLevel_text': 'Lower (LMC)',
        'iso2Code': 'ZM',
        'latitude': '-15.3982',
        'lendingType': {'id': 'IDX', 'value': 'IDA'},
        'lendingType_text': 'IDA (IDX)',
        'longitude': '28.2937',
        'name': 'Zambia',
        'region': {'id': 'SSF', 'value': 'Sub-Saharan Africa '},
        'region_text': 'Sub-Saharan Africa  (SSF)'
    }, {
        'adminregion': {'id': 'SSA', 'value': 'income)'},
        'adminregion_text': 'Sub-high income) (SSA)',
        'capitalCity': 'Harare',
        'id': 'ZWE',
        'incomeLevel': {'id': 'LIC', 'value': 'Low income'},
        'incomeLevel_text': 'Low income (LIC)',
        'iso2Code': 'ZW',
        'latitude': '-17.8312',
        'lendingType': {'id': 'IDB', 'value': 'Blend'},
        'lendingType_text': 'Blend (IDB)',
        'longitude': '31.0672',
        'name': 'Zimbabwe',
        'region': {'id': 'SSF', 'value': 'Sub-Saharan Africa '},
        'region_text': 'Sub-Saharan Africa  (SSF)'
    }]

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
