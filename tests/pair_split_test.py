import unittest
from utils.pair_split import common_pair_split

class TestCommonPairSplit(unittest.TestCase):
    def test_common_pair_split(self):
        hand = [1, 1, 2, 2, 3, 3, 4, 4]
        furo = [[6, 7, 8], [15, 15, 15]]
        expected_output = [
            [[1, 1], [2, 3, 4], [2, 3, 4], [6, 7, 8], [15, 15, 15]],
            [[4, 4], [1, 2, 3], [1, 2, 3], [6, 7, 8], [15, 15, 15]]
        ]
        result = common_pair_split(hand, furo)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()