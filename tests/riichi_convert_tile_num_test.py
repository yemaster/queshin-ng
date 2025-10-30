import unittest
from utils.riichi.yaku_han import convert_tile_to_num

class TestConvertTileNum(unittest.TestCase):
    def test_convert_tile_to_num(self):
        test_cases = {
            "0m": 4,
            "1m": 0,
            "2m": 1,
            "3m": 2,
            "4m": 3,
            "5m": 4,
            "6m": 5,
            "7m": 6,
            "8m": 7,
            "9m": 8,
            "0p": 13,
            "1p": 9,
            "2p": 10,
            "3p": 11,
            "4p": 12,
            "5p": 13,
            "6p": 14,
            "7p": 15,
            "8p": 16,
            "9p": 17,
            "0s": 22,
            "1s": 18,
            "2s": 19,
            "3s": 20,
            "4s": 21,
            "5s": 22,
            "6s": 23,
            "7s": 24,
            "8s": 25,
            "9s": 26,
            "1z": 27,
            "2z": 28,
            "3z": 29,
            "4z": 30,
            "5z": 31,
            "6z": 32,
            "7z": 33,
        }
        for tile_str, expected_num in test_cases.items():
            with self.subTest(tile_str=tile_str):
                self.assertEqual(convert_tile_to_num(tile_str), expected_num)

if __name__ == '__main__':
    unittest.main()