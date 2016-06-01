"""World Bank Data Indicator API helper.

This is a simple indicator API helper focused on ease of use and getting data
for use with Orange data mining software. For a more comprehensive APIs see
wbpy or wbdata packages.
"""
import urllib
import json

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
        country_query = "countries?format=json&per_page=1000"
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
