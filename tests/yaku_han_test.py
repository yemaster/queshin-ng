import unittest
from utils.riichi.yaku_han import yaku_han

class TestYakuHan(unittest.TestCase):
    def test_normal_yaku(self):
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

            self.assertEqual(result and (("yaku.pinghu", 1) in result["yakus"]), test_case[1])


if __name__ == '__main__':
    unittest.main()