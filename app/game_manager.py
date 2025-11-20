from typing import List, Dict, Optional
import random
from app.utils.yaku_han import yaku_han

class MajRoom:
    def __init__(self, room_id: int, room_name: str):
        self.room_id = room_id      # 对应数据库 rooms.id (Integer)
        self.room_name = room_name  # 对应数据库 rooms.name
        self.players: List[str] = []  # 存储玩家 sid (socket id)
        self.player_ids: List[int] = [] # 存储玩家 user_id (数据库 id)
        self.hands: Dict[str, List[str]] = {} 
        self.discards: List[str] = [] 
        self.wall: List[str] = [] 
        self.turn_index = 0
        self.is_playing = False
        
        # 游戏规则设置
        self.settings = {
            "dora": ["1m"], "ura_dora": ["2m"],
            "player_wind": "1z", "phase_wind": "1z",
            "round": 1, "riichi": 0, "ippatus": False,
            "after_a_kan": False, "robbing_a_kan": False,
            "under_the_sea": False, "under_the_river": False,
            "ron": True
        }

    def add_player(self, sid: str, user_id: int):
        """
        在内存中添加玩家
        """
        if len(self.players) < 4:
            self.players.append(sid)
            self.player_ids.append(user_id)
            return True
        return False

    def init_game(self):
        self.is_playing = True
        # 生成牌山 (简化版，实际需136张)
        suits = ['m', 'p', 's']
        honors = ['1z', '2z', '3z', '4z', '5z', '6z', '7z']
        self.wall = []
        for _ in range(4):
            for s in suits:
                for n in range(1, 10):
                    self.wall.append(f"{n}{s}")
            for h in honors:
                self.wall.append(h)
        random.shuffle(self.wall)

        # 发牌
        for p in self.players:
            self.hands[p] = [self.wall.pop() for _ in range(13)]
            self.hands[p].sort()

    def draw_tile(self, sid: str):
        if not self.wall:
            return None
        tile = self.wall.pop()
        self.hands[sid].append(tile)
        return tile

    def check_win(self, sid: str, win_tile: str):
        hand = self.hands[sid]
        # 暂时假设无副露
        furo = [] 
        result = yaku_han(hand, furo, win_tile, self.settings.copy())
        return result

class RoomManager:
    def __init__(self):
        # 使用 room_name 作为键来查找内存中的房间
        self.rooms: Dict[str, MajRoom] = {}

    def create_room(self, room_id: int, room_name: str):
        if room_name not in self.rooms:
            # 初始化时传入数据库 ID
            self.rooms[room_name] = MajRoom(room_id, room_name)
            return self.rooms[room_name]
        return None

    def get_room(self, room_name: str) -> Optional[MajRoom]:
        return self.rooms.get(room_name)

    def remove_room(self, room_name: str):
        if room_name in self.rooms:
            del self.rooms[room_name]

room_manager = RoomManager()