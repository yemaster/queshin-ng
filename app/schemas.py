from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# 用户注册请求体
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# 用户信息返回体 (不包含密码)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    points: int
    
    class Config:
        from_attributes = True # 允许从 SQLAlchemy 模型读取数据

# Token 返回体
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    
class RoomBase(BaseModel):
    name: str
    capacity: int = 4 # 默认为4人

class RoomCreate(RoomBase):
    pass

# 房间列表项的返回格式
class RoomListItem(RoomBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    current_player_count: int # 计算属性：当前人数
    creator_username: str     # 计算属性：房主名字

    class Config:
        from_attributes = True

# 单个房间的详细信息（包含玩家列表）
class PlayerInfo(BaseModel):
    user_id: int
    username: str
    player_number: int
    is_ready: bool
    
    class Config:
        from_attributes = True

class RoomDetail(RoomListItem):
    players: List[PlayerInfo] = []