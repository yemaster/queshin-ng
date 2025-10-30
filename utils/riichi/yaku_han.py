def convert_tile_num(str):
    """Convert tile string to tile number.
    
    Args:
        str (str): Tile string, e.g. "1m", "5p", "7z", "0p". 0m for red 5m, 0p for red 5p, 0s for red 5s.
    
    Returns:
        int: Tile number (0-33). 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors.
    """
    suit_dict = {'m': 0, 'p': 9, 's': 18, 'z': 27}
    number = int(str[0])
    suit = str[1]
    if suit not in suit_dict:
        raise ValueError("Invalid suit: {}".format(suit))
    if suit == 'z' and (number < 1 or number > 7):
        raise ValueError("Invalid honor tile number: {}".format(number))
    if suit != 'z' and (number < 0 or number > 9):
        raise ValueError("Invalid tile number: {}".format(number))
    return suit_dict[suit] + (number - 1 if number != 0 else 4)