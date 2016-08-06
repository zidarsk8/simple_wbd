"""World Bank Data climate API helper.

This is a simple climate API helper focused on ease of use and getting data for
use with Orange data mining software. For a more comprehensive APIs see wbpy or
wbdata packages.
"""
import itertools
import json
import logging

from collections import defaultdict

from simple_wbd import utils

logger = logging.getLogger(__name__)


class ClimateDataset(object):
    """Clime API response object.

    This object is just a holder for functions to transform climate API
    response into a more user friendly structure.
    """
    # pylint: disable=too-few-public-methods


    KEYS = ["country", "type", "interval", "data"]
    _levels_map = {key: index for key, index in enumerate(KEYS)}
    _time_key_map = {"decade": "year"}

    def __init__(self, api_responses):
        self.api_responses = api_responses
        self.rows = None
        self.columns = None

    def as_dict(self):
        """Return api responses as nested dictionary.

        Resulting dict looks like
        result = {
            alpha3-country-code: {
                data-type: {
                    interval:{
                        interval-start: value
                    }
                }
            }
        }
        data-type: "pr" for precipitation and "tas" for temperature.
        interval: decade, year, month
        interval-start: year, starting year of a decade, 0 base indexed month.
        """
        result = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(dict))))
        for country, country_dict in self.api_responses.items():
            for type_, type_dict in country_dict.items():
                for interval, interval_dict in type_dict.items():
                    value_data = result[country][type_][interval]
                    for value in interval_dict.get("response", []):
                        time_key = self._time_key_map.get(interval, interval)
                        value_data[value[time_key]] = value["data"]
        return result

    def _gather_key_by_level(self, data, level=0, accomulator=None):
        """Gather all keys of a nested dict grouped by levels."""
        if accomulator is None:
            accomulator = defaultdict(set)

        if not isinstance(data, dict):
            return accomulator

        for key, value in data.items():
            accomulator[level].add(key)
            self._gather_key_by_level(value, level+1, accomulator)

        return accomulator

    def _get_all_keys(self, data):
        """Gather all key values by level for the current dataset."""
        keys = self._gather_key_by_level(data)
        countries = keys[0]
        types = keys[1]
        intervals = keys[2]
        data_keys = keys[3]
        return countries, types, intervals, data_keys

    def _generate_list(self):
        """Generate 2D array."""
        dict_ = self.as_dict()
        # countries, types, intervals, data_keys = self._get_all_keys(dict_)
        return dict_

    def as_list(self, columns=None):
        """Get a 2D array data representation."""
        if not columns:
            self.columns = ["type", "interval", "data"]
            self.rows = ["country"]
        else:
            self.columns = columns
            self.rows = [key for key in self.KEYS if key not in columns]

        if not set(self.columns) < set(self.KEYS):
            raise TypeError("Columns argument contains invalid data")

        return self._generate_list()


class ClimateAPI(utils.ApiBase):
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

    _default_intervals = [
        "year",
        "month",
    ]

    BASE_URL = "http://climatedataapi.worldbank.org/climateweb/rest/"
    INSTRUMENTAL_QUERY = "v1/{loc_type}/cru/{data_type}/{interval}/{location}"
    MAX_BASSIN_ID = 468

    def __init__(self, dataset_class=None):
        """Initialize climate api.

        Args:
            dataset_class: Optional subclass of ClimateData.
        """
        self.progress = {
            "pages": 0,
            "current_page": 0,
        }
        self._dataset_class = ClimateDataset
        super().__init__(dataset_class)

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
            intervals = self._default_intervals

        api_responses = defaultdict(lambda: defaultdict(dict))
        parameters = list(itertools.product(locations, data_types, intervals))
        self.progress["pages"] = len(parameters)
        self.progress["current_page"] = 0
        for location, data_type, interval in parameters:
            self.progress["current_page"] += 1
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

        return self._dataset_class(api_responses)
