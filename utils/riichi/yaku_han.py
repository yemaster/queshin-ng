from utils.pair_split import seven_pair_split, common_pair_split, Triplet, Sequence, Quad, Pair

def convert_tile_to_num(tile):
    """Convert tile string to tile number.
    
    Args:
        tile (str): Tile string, e.g. "1m", "5p", "7z", "0p". 0m for red 5m, 0p for red 5p, 0s for red 5s.
    
    Returns:
        int: Tile number (0-33). 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors.
    """
    if tile == "-":
        return -1
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
        number = 12 - number  # 5z 6z 7z 是白发中，但是 31 32 33 是中发白
    return suit_dict[suit] + (number - 1 if number != 0 else 4)

def convert_hand_to_num(hand):
    """Convert hand to tile number.
    
    Args:
        hand (list[int]): Hand String List, e.g. ["1m", "2m", "3m"].
    
    Returns:
        list[int]: Tile number list (0-33)"""
    
    return [convert_tile_to_num(tile) for tile in hand]

def is_menzenqing(hand_num, furo_num, hu_num):
    for meld in furo_num:
        if len(meld) == 3 or (-1 not in meld):
            return False
    return True

def is_pinfu(pair_split, hu_num, settings):
    """Check is pinfu.
    
    Args:
        pair_split: number[][] 分割好的牌型
        hu_num: 胡的牌（数字形式）
        settings: 设置信息，包含以下字段：
            dora: str[] 宝牌列表
            dora_num: number[] 宝牌数字列表
            ura_dora: str[] 里宝牌列表
            ura_dora_num: number[] 里宝牌数字列表
            player_wind: str 自风
            player_wind_num: number 自风数字
            phase_wind: str 场风
            phase_wind_num: number 场风数字
            round: number 第几巡
            riichi: number 是否立直，1为立直，2为两立直
            ippatus: boolean 是否一发
            after_a_kan: boolean 是否岭上
            robbing_a_kan: boolean 是否抢杠
            under_the_sea: boolean 是否海底
            under_the_river: boolean 是否河底
            ron: boolean 是否荣和


    
    Returns:
        bool
    """
    # One pair and four melds
    if len(pair_split) != 5:
        return False
    
    has_pair = False
    for meld in pair_split:
        if isinstance(meld, Pair):
            if has_pair:
                return False # Only allow one pair
            has_pair = True
            if meld[0] == settings["player_wind_num"] or \
               meld[0] == settings["phase_wind_num"] or \
               meld[0] in [31, 32, 33]:
                return False # Yaku tile are not allowed
        elif not isinstance(meld, Sequence):
            return False
    
    for meld in pair_split:
        if len(meld) == 3:
            if hu_num == meld[0] or hu_num == meld[2]: # double
                return True
    
    return False

def is_tanyao(pair_split, hu_num, settings):
    disallow_nums = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    for meld in pair_split:
        for tile in meld:
            if tile in disallow_nums:
                return False
    return True

def is_yakuhai_player_wind(pair_split, hu_num, settings):
    for meld in pair_split:
        if isinstance(meld, Triplet) or isinstance(meld, Quad):
            if meld.num == settings["player_wind_num"]:
                return True
    return False

def is_yakuhai_phase_wind(pair_split, hu_num, settings):
    for meld in pair_split:
        if isinstance(meld, Triplet) or isinstance(meld, Quad):
            if meld.num == settings["phase_wind_num"]:
                return True
    return False

def is_yakuhai_chuu(pair_split, hu_num, settings):
    for meld in pair_split:
        if isinstance(meld, Triplet) or isinstance(meld, Quad):
            if meld.num == 31:
                return True
    return False

def is_yakuhai_hatsu(pair_split, hu_num, settings):
    for meld in pair_split:
        if isinstance(meld, Triplet) or isinstance(meld, Quad):
            if meld.num == 32:
                return True
    return False

def is_yakuhai_shiro(pair_split, hu_num, settings):
    for meld in pair_split:
        if isinstance(meld, Triplet) or isinstance(meld, Quad):
            if meld.num == 33:
                return True
    return False

def is_riichi(pair_split, hu_num, settings):
    return (settings["riichi"] == 1)

def is_ippatus(pair_split, hu_num, settings):
    return settings["ippatus"]

def is_fully_concealed_hands(pair_split, hu_num, settings):
    return (not settings["ron"])

def is_pure_double_sequence(pair_split, hu_num, settings):
    meld_count = []
    for meld in pair_split:
        if len(meld) == 3:
            if meld[0] != meld[1] and meld[1] != meld[2]:
                if meld in meld_count:
                    return True
                meld_count.append(meld)
    return False

def is_after_a_kan(pair_split, hu_num, settings):
    return settings["after_a_kan"]

def is_robbing_a_kan(pair_split, hu_num, settings):
    return settings["robbing_a_kan"]

def is_under_the_sea(pair_split, hu_num, settings):
    return settings["under_the_sea"]

def is_under_the_river(pair_split, hu_num, settings):
    return settings["under_the_river"]

def is_double_riichi(pair_split, hu_num, settings):
    return (settings["riichi"] == 2)

def is_triple_triplets(pair_split, hu_num, settings):
    triplets = []
    for meld in pair_split:
        if len(meld) == 3:
            if meld[0] == meld[1]:
                triplets.append(meld[0])
        elif len(meld) == 4:
            triplets.append([tile for tile in meld if tile != -1][0])
    for i in range(9):
        if i in triplets and (i + 9) in triplets and (i + 18) in triplets:
            return True
    return False

def is_three_quads(pair_split, hu_num, settings):
    quad_len = 0
    for meld in pair_split:
        if len(meld) == 4:
            quad_len += 1
    return (quad_len == 3)

def is_all_triplets(pair_split, hu_num, settings):
    for meld in pair_split:
        if len(meld) == 3:
            if meld[0] != meld[1] or meld[1] != meld[2]:
                return False
    return True

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

def yaku_han(hand, furo, hu, settings):
    settings["player_wind_num"] = convert_tile_to_num(settings["player_wind"])
    settings["phase_wind_num"] = convert_tile_to_num(settings["phase_wind"])
    settings["dora_num"] = convert_hand_to_num(settings["dora"])
    settings["ura_dora_num"] = convert_hand_to_num(settings["ura_dora"])

    hand_num = convert_hand_to_num(hand)
    furo_num = [convert_hand_to_num(meld) for meld in furo]
    hu_num = convert_tile_to_num(hu)
    all_tile = hand + [tile for meld in furo for tile in meld]
    if len(hand_num) % 3 == 1:
        hand_num.append(hu_num)
        all_tile.append(hu)
    
    menzenqing = is_menzenqing(hand_num, furo_num, hu_num)

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
            if yaku_han["allow_furo"] == 0 and not menzenqing:
                continue
            if yaku_han["validator"](pair_split, hu_num, settings):
                update_han = yaku_han["han"]
                if yaku_han["allow_furo"] == -1 and not menzenqing:
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
            if tile in settings["dora"]:
                dora_num += 1
            if tile in settings["ura_dora"]:
                ura_dora_num += 1
            if tile in ["0m", "0p", "0s"]:
                red_dora_num += 1
        if dora_num > 0:
            max_han += dora_num
            max_yakus.append(("yaku.dora", dora_num))
        if red_dora_num:
            max_han += red_dora_num
            max_yakus.append(("yaku.red_dora", red_dora_num))
        if settings["riichi"]:
            max_han += ura_dora_num
            max_yakus.append(("yaku.ura_dora", ura_dora_num))
        return {
            "han": max_han,
            "yakus": max_yakus,
            "yakuman": max_yakuman,
            "yakuman_yakus": max_yakuman_yakus
        }
    
    return False