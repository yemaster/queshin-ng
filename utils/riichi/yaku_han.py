from utils.pair_split import seven_pair_split, common_pair_split

def convert_tile_to_num(tile):
    """Convert tile string to tile number.
    
    Args:
        tile (str): Tile string, e.g. "1m", "5p", "7z", "0p". 0m for red 5m, 0p for red 5p, 0s for red 5s.
    
    Returns:
        int: Tile number (0-33). 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors.
    """
    suit_dict = {'m': 0, 'p': 9, 's': 18, 'z': 27}
    number = int(tile[0])
    suit = tile[1]
    if suit not in suit_dict:
        raise ValueError("Invalid suit: {}".format(suit))
    if suit == 'z' and (number < 1 or number > 7):
        raise ValueError("Invalid honor tile number: {}".format(number))
    if suit != 'z' and (number < 0 or number > 9):
        raise ValueError("Invalid tile number: {}".format(number))
    if suit == 'z' and number >= 5:
        number = 12 - number
    return suit_dict[suit] + (number - 1 if number != 0 else 4)

def convert_hand_to_num(hand):
    """Convert hand to tile number.
    
    Args:
        hand (list[int]): Hand String List, e.g. ["1m", "2m", "3m"].
    
    Returns:
        list[int]: Tile number list (0-33)"""
    
    return [convert_tile_to_num(tile) for tile in hand]

def is_pinfu(pair_split, hu_num, setting):
    """Check is normal pinfu."""
    # One pair and four melds
    if len(pair_split) != 5:
        return False
    
    has_pair = False
    for meld in pair_split:
        if len(meld) == 2:
            if has_pair:
                return False # Only allow one pair
            has_pair = True
            if meld[0] == setting["player_wind_num"] or \
               meld[0] == setting["phase_wind_num"] or \
               meld[0] in [31, 32, 33]:
                return False # Yaku tile are not allowed
        elif len(meld) != 3:
            return False  # Only allow chii meld
        else:
            if meld[0] == meld[1]:
                return False  # Only allow chii meld
    
    for meld in pair_split:
        if len(meld) == 3:
            if hu_num == meld[0] or hu_num == meld[2]: # double
                return True
    
    return False

def is_tanyao(pair_split, hu_num, setting):
    disallow_nums = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    for meld in pair_split:
        for tile in meld:
            if tile in disallow_nums:
                return False
    return True

def is_yakuhai_player_wind(pair_split, hu_num, setting):
    for meld in pair_split:
        if len(meld) >= 3:
            if all([tile == setting["player_wind_num"] for tile in meld]):
                return True
    return False

def is_yakuhai_phase_wind(pair_split, hu_num, setting):
    for meld in pair_split:
        if len(meld) >= 3:
            if all([tile == setting["phase_wind_num"] for tile in meld]):
                return True
    return False

def is_yakuhai_chuu(pair_split, hu_num, setting):
    for meld in pair_split:
        if len(meld) >= 3:
            if all([tile == 31 for tile in meld]):
                return True
    return False

def is_yakuhai_hatsu(pair_split, hu_num, setting):
    for meld in pair_split:
        if len(meld) >= 3:
            if all([tile == 32 for tile in meld]):
                return True
    return False

def is_yakuhai_shiro(pair_split, hu_num, setting):
    for meld in pair_split:
        if len(meld) >= 3:
            if all([tile == 33 for tile in meld]):
                return True
    return False


yaku_han_list = {
    "yaku.pinfu": {
        "han": 1,
        "yakuman": 0,
        "validator": is_pinfu,
        "allow_furo": 0,
    },
    "yaku.tanyao": {
        "han": 1,
        "yakuman": 0,
        "validator": is_tanyao,
        "allow_furo": 1,
    },
    "yaku.yakuhai.player_wind": {
        "han": 1,
        "yakuman": 0,
        "validator": is_yakuhai_player_wind,
        "allow_furo": 1,
    },
    "yaku.yakuhai.phase_wind": {
        "han": 1,
        "yakuman": 0,
        "validator": is_yakuhai_phase_wind,
        "allow_furo": 1,
    },
    "yaku.yakuhai.chuu": {
        "han": 1,
        "yakuman": 0,
        "validator": is_yakuhai_chuu,
        "allow_furo": 1,
    },
    "yaku.yakuhai.hatsu": {
        "han": 1,
        "yakuman": 0,
        "validator": is_yakuhai_hatsu,
        "allow_furo": 1,
    },
    "yaku.yakuhai.shiro": {
        "han": 1,
        "yakuman": 0,
        "validator": is_yakuhai_shiro,
        "allow_furo": 1,
    }
}

def yaku_han(hand, furo, hu, setting):
    setting["player_wind_num"] = convert_tile_to_num(setting["player_wind"])
    setting["phase_wind_num"] = convert_tile_to_num(setting["phase_wind"])
    setting["dora_num"] = convert_hand_to_num(setting["dora"])
    setting["ura_dora_num"] = convert_hand_to_num(setting["ura_dora"])

    hand_num = convert_hand_to_num(hand)
    furo_num = [convert_hand_to_num(meld) for meld in furo]
    hu_num = convert_tile_to_num(hu)
    all_tile = hand + [tile for meld in furo for tile in meld]
    if len(hand_num) % 3 == 1:
        hand_num.append(hu_num)
        all_tile.append(hu)

    pair_splits = seven_pair_split(hand_num, furo_num, False, False) + common_pair_split(hand_num, furo_num)

    max_han = 0
    max_yakuman = 0
    max_yakus = []
    max_yakuman_yakus = []
    
    for pair_split in pair_splits:
        han = 0
        yakuman = 0
        yakus = []
        yakuman_yakus = []

        for yaku_han_name in yaku_han_list:
            yaku_han = yaku_han_list[yaku_han_name]
            if yaku_han["allow_furo"] == 0 and len(furo_num) > 0:
                continue
            if yaku_han["validator"](pair_split, hu_num, setting):
                update_han = yaku_han["han"]
                if yaku_han["allow_furo"] == -1 and len(furo_num) > 0:
                    update_han -= 1
                han += update_han
                yakuman += yaku_han["yakuman"]
                if yaku_han["yakuman"] > 0:
                    yakuman_yakus.append((yaku_han_name, 0))
                else:
                    yakus.append((yaku_han_name, update_han))

        if yakuman > max_yakuman or (yakuman == max_yakuman and han > max_han):
            max_han = han
            max_yakuman = yakuman
            max_yakus = yakus
            max_yakuman_yakus = yakuman_yakus
            
    
    if max_han > 0:
        dora_num = 0
        red_dora_num = 0
        ura_dora_num = 0
        for tile in all_tile:
            if tile in setting["dora"]:
                dora_num += 1
            if tile in setting["ura_dora"]:
                ura_dora_num += 1
            if tile in ["0m", "0p", "0s"]:
                red_dora_num += 1
        if dora_num > 0:
            max_han += dora_num
            max_yakus.append(("yaku.dora", dora_num))
        if red_dora_num:
            max_han += red_dora_num
            max_yakus.append(("yaku.red_dora", red_dora_num))
        if setting["riichi"]:
            max_han += ura_dora_num
            max_yakus.append(("yaku.ura_dora", ura_dora_num))
        return {
            "han": max_han,
            "yakus": max_yakus,
            "yakuman": max_yakuman,
            "yakuman_yakus": max_yakuman_yakus
        }
    
    return False