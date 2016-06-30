"""World Bank Data Indicator API helper.

This is a simple indicator API helper focused on ease of use and getting data
for use with Orange data mining software. For a more comprehensive APIs see
wbpy or wbdata packages.
"""
import urllib
import json
import re
import logging

from simple_wbd import utils

logger = logging.getLogger(__name__)


class IndicatorDataset(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, api_responses):
        self.api_responses = api_responses


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

        if filter_.lower() == "featured":
            url = "http://data.worldbank.org/indicator"
        else:
            url = "http://data.worldbank.org/indicator/all"

        filter_page = utils.fetch(url)
        codes = re.compile(r"(?<=http://data.worldbank.org/indicator/)"
                           r"[A-Za-z0-9\.-_]+(?=\">)")
        code_matches = set(code.lower() for code in codes.findall(filter_page))

        return [i for i in indicators if i.get("id").lower() in code_matches]

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
        indicators = self.get_indicators(filter_=filter_)
        indicator_list = [["Id", "Name", "Source", "Topics"]]
        for indicator in indicators:
            indicator_list.append([
                indicator.get("id", "").strip(),
                indicator.get("name", "").strip(),
                indicator.get("source", {}).get("value", "").strip(),
                ", ".join(
                    topic.get("value", "").strip()
                    for topic in indicator.get("topics", [])
                )
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

        return IndicatorDataset(responses)
