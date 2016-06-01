"""World Bank Data Indicator API helper.

This is a simple indicator API helper focused on ease of use and getting data
for use with Orange data mining software. For a more comprehensive APIs see
wbpy or wbdata packages.
"""
import urllib
import json
import re

from simple_wbd import utils


class IndicatorAPI(object):
    """Request data from the World Bank Indicator API."""
    # pylint: disable=too-few-public-methods

    BASE_URL = "http://api.worldbank.org/"

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
        country_query = "countries?format=json&per_page=100000"
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
        country_query = "indicators?format=json&per_page=100000"
        url = urllib.parse.urljoin(self.BASE_URL, country_query)
        indicators = json.loads(utils.fetch(url))[1]

        filtered = self._filter_indicators(indicators, filter_)

        return filtered
