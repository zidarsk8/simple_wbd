"""World Bank Data Indicator API helper.

This is a simple indicator API helper focused on ease of use and getting data
for use with Orange data mining software. For a more comprehensive APIs see
wbpy or wbdata packages.
"""
import urllib
import json
import logging
from collections import defaultdict

from simple_wbd import utils
from simple_wbd import filters

logger = logging.getLogger(__name__)


class IndicatorDataset(object):
    """Wrapper for indicator dataset.

    This class provides multiple ways of accessing retrieved indicator data.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, api_responses):
        self.api_responses = api_responses

    @staticmethod
    def _get_dates(data):
        """Get all different unique dates from single indicator data.

        Args:
            data (list[dict]): list of indicator data that contains date.

        Returns:
            list[str]: sorted list of all unique date entries.
        """
        return sorted(set(datapoint.get("date") for datapoint in data))

    @staticmethod
    def _parse_value(value):
        """Parse any non empty string value into float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("Failed to parse fload value.", exc_info=True)

    def _get_data_map(self, data, data_map=None, country_prefix="",
                      date_prefix=""):
        """Get data is a nested dictionary.

        This returns data as a nested default dict, with first level containing
        country data and second level indicator data with dates.

        Note: prefix is useful when aggregating data from multiple indicators.
        usually the prefix can be the indicator itself.

        Args:
            data: Result dict retrieved from world bank data api.
            data_map: Existing data map that will be update with missing data.
                if set to none, a new data_map is created and returned. This
                used for merging data from different indicators.
            country_prefix: Prefix string for all country keys.
            date_prefix: Prefix string for all date keys.

        Returns:
            nested dict containing data grouped by country, indicator and date.
        """
        if data_map is None:
            data_map = defaultdict(lambda: defaultdict(float))
        for datapoint in data:
            country = datapoint.get("country", {}).get("value", "")
            date = datapoint.get("date", "")
            data_map[country_prefix + country][date_prefix + date] = \
                self._parse_value(datapoint.get("value"))
        return data_map

    @staticmethod
    def _get_all_dates(data_map):
        date_set = set()
        for country_data in data_map.values():
            for date in country_data:
                date_set.add(date)

        return sorted(date_set)

    @staticmethod
    def _get_all_countries(data_map):
        return sorted(data_map.keys())

    def _get_single_response_list(self, data, timeseries=False):
        """Get list data for a single indicator."""
        headers = ["Date"] if timeseries else ["Country"]
        data_map = self._get_data_map(data)

        all_dates = self._get_all_dates(data_map)
        all_countries = self._get_all_countries(data_map)

        headers.extend(all_dates)
        response = [headers]
        for country in all_countries:
            response.append([country] + [
                data_map[country][date] for date in all_dates
            ])
        if timeseries:
            # transpose 2D array
            response = list(list(i) for i in zip(*response))

        return response

    def _get_responses_list(self, response_data, timeseries=False):
        """Get list data for multiple indicators."""
        headers = ["Date"] if timeseries else ["Country"]
        data_map = None

        for indicator, indicator_data in response_data.items():
            prefix = indicator + " - "
            data_map = self._get_data_map(
                indicator_data,
                data_map=data_map,
                country_prefix=prefix if timeseries else "",
                date_prefix="" if timeseries else prefix,
            )

        all_dates = self._get_all_dates(data_map)
        all_countries = self._get_all_countries(data_map)

        headers.extend(all_dates)
        response = [headers]
        for country in all_countries:
            response.append([country] + [
                data_map[country][date] for date in all_dates
            ])

        if timeseries:
            # transpose 2D array
            response = list(list(i) for i in zip(*response))

        return response

    def as_list(self, timeseries=False):
        """Get data as 2D list.

        This function returns data as a 2D list where rows contain country and
        all data related to that country, and columns contain indicator and
        dates.

        Args:
            timeseries: Boolean indicating if the list should be a timeseries.
                That means that the first column would contain dates instead of
                countries and countries would be in columns.

        Returns:
            2D Array of response data, where first row is the data headers.
        """
        if len(self.api_responses) == 1:
            value = next(iter(self.api_responses.values()))
            return self._get_single_response_list(value, timeseries)

        if len(self.api_responses) > 1:
            return self._get_responses_list(self.api_responses, timeseries)

        return []


class IndicatorAPI(object):
    """Request data from the World Bank Indicator API."""

    BASE_URL = "http://api.worldbank.org/"
    GET_PARAMS = "?format=json&per_page=100000"
    DEFAULT_COUNTRY_FIELDS = [
        "id",
        "name",
        "incomeLevel_text",
    ]

    _country_field_map = {
        "id": "Id",
        "name": "Name",
        "incomeLevel_text": "Income Level",
    }

    def __init__(self, dataset_class=None):
        """Initialize indicator api.

        Args:
            dataset_class: A subclass of IdicatorDataset. This is used for
                easier extending the functionality of the indicator dataset.
        """
        self._dataset_class = IndicatorDataset
        try:
            if dataset_class and issubclass(dataset_class, IndicatorDataset):
                self._dataset_class = dataset_class
        except TypeError:
            logger.error("Could not use extended dataset class.")

    def get_countries(self):
        """Get a list of countries and regions.

        This is a full list of countries and regions that can be used in the
        indicator queries. In the list there are some non ISO codes such as WLD
        for the whole world and other aggregate regions.

        Note that this list does not include all countries (e.g. Israel),
        but only countries that can be queried with the indicator API.

        Returns:
            list[dict]: A list of countries and aggregate regions.
        """
        country_query = "countries" + self.GET_PARAMS
        url = urllib.parse.urljoin(self.BASE_URL, country_query)
        country_result = utils.fetch(url)
        countries = json.loads(country_result)[1]

        dict_to_text = ["region", "adminregion", "incomeLevel", "lendingType"]
        for country in countries:
            for key in dict_to_text:
                country[key + "_text"] = "{value} ({id_})".format(
                    value=country.get(key, {}).get("value"),
                    id_=country.get(key, {}).get("id"),
                )

        return countries

    def get_country_list(self, fields=None, field_map=None):
        """Get list of all available countries."""
        if not field_map:
            field_map = self._country_field_map
        if not fields:
            fields = self.DEFAULT_COUNTRY_FIELDS

        countries = self.get_countries()
        country_list = [[field_map[field] for field in fields]]
        for country in countries:
            country_list.append([country[field] for field in fields])
        return country_list

    @classmethod
    def _filter_indicators(cls, indicators, filter_):
        """Filter indicators to common or featured.

        The common and featured lists are fetched from world bank data site.

        Args:
            indicators: list of dicts containing all indicator data.
            filter_: either "common" or "featured" string.

        Returns:
            list of filtered indicators if the filter is valid or the entire
            indicator list.
        """
        if hasattr(filter_, "lower") and filter_.lower() in filters.FILTER:
            return [i for i in indicators if i.get("id").lower() in
                    filters.FILTER.get(filter_.lower())]

        return indicators

    def get_indicators(self, filter_="Common"):
        """Get a list of indicators.

        Args:
            filter_ (str): Common or Featured. Leave empty for all indicators.

        Returns:
            list[dict]: A list of queryable indicators.
        """
        country_query = "indicators" + self.GET_PARAMS
        url = urllib.parse.urljoin(self.BASE_URL, country_query)
        indicators = json.loads(utils.fetch(url))[1]

        if filter_:
            return self._filter_indicators(indicators, filter_)

        return indicators

    def get_indicator_list(self, filter_="Common"):
        """Get a list of all possible indicators."""
        indicators = self.get_indicators(filter_=filter_)
        indicator_list = [["Id", "Name", "Topics", "Source"]]
        for indicator in indicators:
            indicator_list.append([
                indicator.get("id", "").strip(),
                indicator.get("name", "").strip(),
                ", ".join(
                    topic.get("value", "").strip()
                    for topic in indicator.get("topics", [])
                ),
                indicator.get("source", {}).get("value", "").strip(),
            ])
        return indicator_list

    def _get_countries_map(self):
        """Get a map from country name or code to alpha3 code.

        Returns:
            dict: map of names, alpha2, alpha3 codes to alpha3.
        """
        all_countries = self.get_countries()
        country_map = {c.get("iso2Code"): c.get("id") for c in all_countries}
        country_map.update({c.get("id"): c.get("id") for c in all_countries})
        country_map.update({c.get("name"): c.get("id") for c in all_countries})

        return {k.lower(): v.lower() for k, v in country_map.items() if k}

    def _countries_to_alpha3(self, countries):
        """Filter out invalid countries and return a set of alpha3 codes.

        Args:
            countries (list or str): List of country codes or names, or a
                single country code/name

        Returns:
            set[str]: List of alpha3 country codes for all valid countries.
        """

        if not countries:
            return set()

        if isinstance(countries, str):
            countries = [countries]

        countries = [c.lower() for c in countries if c]

        countries_map = self._get_countries_map()
        alpha3_codes = set()
        for country in countries:
            if country in countries_map:
                alpha3_codes.add(countries_map[country])
            else:
                logger.warning("Ignoring invalid country: %s", country)
        return alpha3_codes

    def _get_indicator_data(self, alpha3_text, indicator):

        query = "countries/{countries}/indicators/{indicator}{params}".format(
            countries=alpha3_text,
            indicator=indicator,
            params="?format=json&per_page=10000",  # lower limit
        )

        url = urllib.parse.urljoin(self.BASE_URL, query)
        header, indicator_data = json.loads(utils.fetch(url))

        # loop through the rest of the pages if they exist
        for page in range(2, header.get("pages", 1) + 1):
            page_url = "{url}&page={page}".format(url=url, page=page)
            indicator_data += json.loads(utils.fetch(page_url))[1]

        return indicator_data

    def get_dataset(self, indicators, countries=None):
        """Get indicator dataset.

        Args:
            indicators (str or list[str]): A single indicator id, or a list of
                requested indicator ids.
            countries (str or list[str]): country id or list of country ids. If
                None, all countries will be used.

        Returns:
            IndicatorDataset: all datasets for the requested indicators.
        """
        if isinstance(indicators, str):
            indicators = [indicators]

        alpha3_codes = self._countries_to_alpha3(countries)
        if alpha3_codes:
            alpha3_text = ";".join(alpha3_codes).upper()
        else:
            alpha3_text = "all"

        indicators_set = set(i.lower() for i in indicators)

        responses = {}
        # pylint: disable=broad-except
        for indicator in indicators_set:
            try:
                responses[indicator] = self._get_indicator_data(
                    alpha3_text, indicator)
            except Exception:
                # We should avoid any errors that can occur due to api
                # responses or invalid data.
                logger.warning(
                    "Failed to fetch indicator: %s", indicator, exc_info=True)

        return self._dataset_class(responses)

    # Set of featured indicators as of 2016-06-30.
