class Meld:
    def __init__(self, num: int, furo: bool):
        self.num = num
        self.furo = furo
    
    def __eq__(self, other):
        if isinstance(other, Meld):
            return len(self) == len(other) and self.num == other.num
        if isinstance(other, list):
            return list(self) == other
        return False
    
    def __lt__(self, other):
        if not isinstance(other, Meld):
            raise ValueError(f"Cannot compare Meld and {type(other)}")
        if len(self) < len(other):
            return True
        if len(self) == len(other):
            if self.num < other.num:
                return True
            if self.num == other.num:
                if isinstance(self, Sequence) and not isinstance(self, Triplet):
                    return True
        return False
    
    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)
    
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    
    def __ge__(self, other):
        return not self.__lt__(other)

class Pair(Meld):
    def __len__(self):
        return 2
    
    def __getitem__(self, index):
        if index >= 0 and index < 2:
            return self.num
        raise IndexError("Index out of range")

class Triplet(Meld):
    def __len__(self):
        return 3
    
    def __getitem__(self, index):
        if index >= 0 and index < 3:
            return self.num
        raise IndexError("Index out of range")

class Sequence(Meld):
    def __len__(self):
        return 3
    
    def __getitem__(self, index):
        if index >= 0 and index < 3:
            return self.num + index
        raise IndexError("Index out of range")
    
class Quad(Meld):
    def __len__(self):
        return 4
    
    def __getitem__(self, index):
        if index >= 0 and index < 4:
            return self.num
        raise IndexError("Index out of range")

def seven_pair_split(hand, furo, allow_same_pair=True, allow_furo=False):
    """Split a hand into seven pairs and the rest of the tiles.

    Args:
        hand (list[num]): A list of tiles representing the hand. 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors.
        furo (list[list[num]]): A list of melds.

    Returns:
        list[list[list[num]]]: List of seven pairs.
    """
    tile_count = {}

    # Count occurrences of each tile in the hand
    for tile in hand:
        if tile in tile_count:
            tile_count[tile] += 1
        else:
            tile_count[tile] = 1
    
    pairs = []
    for tile, count in tile_count.items():
        if count >= 4 and not allow_same_pair:
            return []  # Cannot have the same pair more than once if not allowed
        pairs.extend([[tile, tile]] * (count // 2))
    
    if allow_furo and allow_same_pair:
        for meld in furo:
            if len(meld) == 4 and meld[0] == meld[1] and meld[2] == meld[3] and meld[2] == meld[3]:
                pairs.append([meld[0], meld[1]])
                pairs.append([meld[2], meld[3]])
    
    if len(pairs) < 7:
        return []  # Not enough pairs to form seven pairs
    
    return [pairs[:7]]

def common_pair_split(hand, furo):
    """Split the tiles into one pair and four melds.

    Args:
        hand (list[num]): A list of tiles representing the hand. 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors.
        furo (list[list[num]]): A list of melds.

    Returns:
        list[list[list[num]]]: List of common pairs.
    
    Example:
        >>> hand = [1, 1, 2, 2, 3, 3, 4, 4]
        >>> furo = [[6, 7, 8], [15, 15, 15]]
        >>> common_pair_split(hand, furo)
        [[[1, 1], [2, 3, 4], [2, 3, 4], [6, 7, 8], [15, 15, 15]], [[4, 4], [1, 2, 3], [1, 2, 3], [6, 7, 8], [15, 15, 15]]]
    """
    tile_count = [0] * 34

    # Count occurrences of each tile in the hand
    for tile in hand:
        tile_count[tile] += 1
            
    pairs = []
    for meld in furo:
        if len(meld) == 3:
            if meld[0] == meld[1]:
                pairs.append(Triplet(meld[0], True))
            else:
                pairs.append(Sequence(min(meld), True))
        elif len(meld) == 4:
            if -1 in meld:
                pairs.append(Triplet([tile for tile in meld if tile != -1][0], False))
            else:
                pairs.append(Triplet(meld[0], True))
    
    def find_melds(last_tile=0):
        if len(pairs) == 5:
            res = pairs.copy()
            # sort: first is pair, then melds in ascending order
            yield sorted(res)
            return
        
        for tile in range(last_tile, 34):
            count = tile_count[tile]
            if count == 0:
                continue
        
            # Check for triplet
            if count >= 3:
                tile_count[tile] -= 3
                pairs.append(Triplet(tile, False))
                yield from find_melds(tile)
                tile_count[tile] += 3
                pairs.pop()
            
            # Check for sequence
            # 0~8 are manzu, 9~17 are pinzu, 18~26 are souzu, 27~33 are honors
            if tile <= 26 and tile % 9 <= 6:
                if tile_count[tile + 1] > 0 and tile_count[tile + 2] > 0:
                    tile_count[tile] -= 1
                    tile_count[tile + 1] -= 1
                    tile_count[tile + 2] -= 1
                    pairs.append(Sequence(tile, False))
                    yield from find_melds(tile)
                    tile_count[tile] += 1
                    tile_count[tile + 1] += 1
                    tile_count[tile + 2] += 1
                    pairs.pop()

    def find_one_pair():
        for tile in range(34):
            count = tile_count[tile]
            if count >= 2:
                tile_count[tile] -= 2
                pairs.append(Pair(tile, False))
                yield from find_melds(0)
                tile_count[tile] += 2
                pairs.pop()
    
    return list(find_one_pair())