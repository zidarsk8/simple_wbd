"""World Bank Data climate API helper.

This is a simple climate API helper focused on ease of use and getting data for
use with Orange data mining software. For a more comprehensive APIs see wbpy or
wbdata packages.
"""
import itertools
import json

from collections import defaultdict

from simple_wbd import utils


class ClimateDataset(object):
    """Clime API response object.

    This object is just a holder for functions to transform climate API
    response into a more user friendly structure.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, api_responses):
        self.api_responses = api_responses


class ClimateAPI(object):
    """Request data from the World Bank Climate API."""
    # pylint: disable=too-few-public-methods

    INSTRUMENTAL_TYPES = {
        "pr": ("Precipitation (rainfall and assumed water equivalent), in "
               "millimeters"),
        "tas": "Temperature, in degrees Celsius",
    }

    INSTRUMENTAL_INTERVALS = [
        "year",
        "month",
        "decade",
    ]

    BASE_URL = "http://climatedataapi.worldbank.org/climateweb/rest/"
    INSTRUMENTAL_QUERY = "v1/{loc_type}/cru/{data_type}/{interval}/{location}"
    MAX_BASSIN_ID = 468

    def _get_location(self, location):
        if location.isdigit():
            if 1 <= int(location) <= self.MAX_BASSIN_ID:
                loc_type = "basin"
            else:
                raise ValueError("basin id must be between 1 and 468.")
        else:
            location = utils.to_alpha3(location)
            loc_type = "country"
        return loc_type, location

    def get_instrumental(self, locations, data_types=None, intervals=None):
        """Get historical data for temperature or precipitation.

        data_type (str): ``pr`` for precipitation, or ``tas`` for temperature.
            If None is specified, both values will be returned.
        interval (str): Either ``year``, ``month`` or ``decade``.
        locations (list[str]): A list of API location codes - basin id numbers,
            or ISO alpha-2 or alpha-3
        flat_results (bool): If false, the result will be returned as a nested
            dict, otherwise the result will be a single level dict with a
            tuple key and normal value.

        Returns:
            dict: Nested dict with location on the first level, data type on
                the second, interval on the third and the appropriate data.
        """
        if not data_types:
            data_types = self.INSTRUMENTAL_TYPES
        if not intervals:
            intervals = self.INSTRUMENTAL_INTERVALS

        api_responses = defaultdict(lambda: defaultdict(dict))
        parameters = itertools.product(locations, data_types, intervals)
        for location, data_type, interval in parameters:
            loc_type, location = self._get_location(location)
            query = self.INSTRUMENTAL_QUERY.format(
                loc_type=loc_type,
                data_type=data_type,
                interval=interval,
                location=location,
            )
            url = self.BASE_URL + query
            api_responses[location][data_type][interval] = {
                "url": url,
                "response": json.loads(utils.fetch(url))
            }

        return ClimateDataset(api_responses)
