import unittest
from tests.pair_split_test import TestCommonPairSplit

suite = unittest.defaultTestLoader.discover('tests', pattern='*_test.py')
runner = unittest.TextTestRunner()
runner.run(suite)