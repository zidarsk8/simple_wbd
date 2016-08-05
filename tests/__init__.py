"""Basic tests package for simple_wbd."""
import unittest
import shutil
import os

import vcr

from simple_wbd import utils

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VCR_CASSETTES = os.path.join(CURRENT_DIR, "vcr_cassettes")

MY_VCR = vcr.VCR(
    cassette_library_dir=VCR_CASSETTES,
    # none (testing), all (updating), new_episodes (dev)
    record_mode="new_episodes",
)


class TestCase(unittest.TestCase):
    """Extended base test case for simple_wbd tests.

    This class is used as a base that handles cache and recording of api calls.
    """

    TEST_TEMP_DIR = os.path.join(CURRENT_DIR, "test_temp_folder")

    def setUp(self):
        self.clear_temp_dir()
        utils.remove_cache_dir()

    def tearDown(self):
        self.remove_temp_dir()

    def clear_temp_dir(self):
        self.remove_temp_dir()
        os.makedirs(self.TEST_TEMP_DIR)

    def remove_temp_dir(self):
        if os.path.exists(self.TEST_TEMP_DIR):
            shutil.rmtree(self.TEST_TEMP_DIR)
