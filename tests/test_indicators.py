"""Unit tests for world bank data indicator API."""

import mock
import pycountry
from requests.exceptions import RequestException

import tests
import simple_wbd


class TestIndicators(tests.TestCase):
    """Tests for functions in simple_wbd.utils module."""

    NUM_OF_COUNTRIES = 304

    def setUp(self):
        super().setUp()
        self.api = simple_wbd.IndicatorAPI()

    def test_init(self):
        """Test Indicator api init function.

        Test if the default response class gets set correctly if the given
        class is a subclass of IndicatorDataset.
        """
        # pylint: disable=protected-access

        class Dummy(object):
            # pylint: disable=too-few-public-methods
            pass

        class DummySubclass(simple_wbd.IndicatorDataset):
            # pylint: disable=too-few-public-methods
            pass

        api = simple_wbd.IndicatorAPI()
        self.assertEqual(api._dataset_class, simple_wbd.IndicatorDataset)

        api = simple_wbd.IndicatorAPI(Dummy)
        self.assertEqual(api._dataset_class, simple_wbd.IndicatorDataset)

        api = simple_wbd.IndicatorAPI("bad data")
        self.assertEqual(api._dataset_class, simple_wbd.IndicatorDataset)

        api = simple_wbd.IndicatorAPI(DummySubclass)
        self.assertEqual(api._dataset_class, DummySubclass)

    def test_bad_request(self):
        """Test failed data fetch requests."""
        # pylint: disable=protected-access
        self.api._get_indicator_data = mock.Mock()
        self.api._get_indicator_data.side_effect = RequestException("Bam!")
        self.api.get_countries = mock.Mock()
        self.api.get_countries.return_value = []
        res = self.api.get_dataset("SL.MNF.0714.FE.ZS")
        self.assertEqual(res.api_responses, {})

    @tests.MY_VCR.use_cassette("country_list.json")
    def test_get_country_list(self):
        """Test fetching a 2D list of country and region codes."""
        country_list = self.api.get_country_list()
        # number of countries + one line for header
        self.assertEqual(self.NUM_OF_COUNTRIES + 1, len(country_list))

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

    def test_all_filter_indicators(self):
        """Test common, featured and bad indicator filters."""
        # pylint: disable=protected-access
        indicators = [
            {"id": "A7ivi"},  # none
            {"id": "ag.srf.totl.k2dt.dod.mdri.cd"},  # common
            {"id": "ag.LND.FRst.zs"},  # featured and common
        ]
        self.assertEqual(
            len(self.api._filter_indicators(indicators, "common")), 2)
        self.assertEqual(
            len(self.api._filter_indicators(indicators, "featured")), 1)
        self.assertEqual(
            len(self.api._filter_indicators(indicators, None)), 3)
        self.assertEqual(
            len(self.api._filter_indicators(indicators, "bad")), 3)

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
        self.assertIn("BAD Indicator".lower(), res.api_responses)
        self.assertEqual(res.api_responses["BAD Indicator".lower()], [])

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
