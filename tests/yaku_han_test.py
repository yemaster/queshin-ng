import unittest
from utils.riichi.yaku_han import yaku_han

class TestYakuHan(unittest.TestCase):
    def test_pinfu(self):
        test_cases = [
            [{
                "hand": ["1m", "2m", "3m", "3m", "4m", "5p", "6p", "7p", "2s", "2s", "3s", "4s", "5s"],
                "furo": [],
                "hu": "2m",
                "setting": {
                    "dora": ["1z"],
                    "ura_dora": ["1z"],
                    "player_wind": "2z",
                    "phase_wind": "3z",
                    "riichi": True
                }
            }, True]
        ]
        for test_case in test_cases:
            hand = test_case[0]["hand"]
            furo = test_case[0]["furo"]
            hu = test_case[0]["hu"]
            setting = test_case[0]["setting"]
            
            result = yaku_han(hand, furo, hu, setting)

            self.assertEqual(result and (("yaku.pinfu", 1) in result["yakus"]), test_case[1])

    def test_player_wind(self):
        test_cases = [
            [{
                "hand": ["1m", "2m", "3m", "3m", "4m", "5p", "6p", "7p", "2s", "2s", "1z", "1z", "1z"],
                "furo": [],
                "hu": "2m",
                "setting": {
                    "dora": ["1z"],
                    "ura_dora": ["1z"],
                    "player_wind": "1z",
                    "phase_wind": "1z",
                    "riichi": False
                }
            }, True],
            [{
                "hand": ["1m", "2m", "3m", "3m", "4m", "5p", "6p", "7p", "2s", "2s"],
                "furo": [["2z", "2z", "2z", "2z"]],
                "hu": "2m",
                "setting": {
                    "dora": ["1z"],
                    "ura_dora": ["1z"],
                    "player_wind": "2z",
                    "phase_wind": "1z",
                    "riichi": False
                }
            }, True]
        ]
        for test_case in test_cases:
            hand = test_case[0]["hand"]
            furo = test_case[0]["furo"]
            hu = test_case[0]["hu"]
            setting = test_case[0]["setting"]
            
            result = yaku_han(hand, furo, hu, setting)

            self.assertEqual(result and (("yaku.yakuhai.player_wind", 1) in result["yakus"]), test_case[1])


if __name__ == '__main__':
    unittest.main()