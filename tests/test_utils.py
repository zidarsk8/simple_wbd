"""Unit tests for wbd utility functions."""

import unittest

from simple_wbd import utils


class TestUtils(unittest.TestCase):

    def test_add(self):
        """Dummy test."""
        self.assertEqual(5, utils.add(3, 2))
