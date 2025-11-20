from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# 定义房间状态枚举，方便管理
class RoomStatus(str, enum.Enum):
    WAITING = "WAITING"   # 等待玩家加入
    PLAYING = "PLAYING"   # 游戏中
    FINISHED = "FINISHED" # 游戏结束

# 用户模型
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    points = Column(Integer, default=1000) # 初始积分给一点，方便测试
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    # 注意：这里的 string reference 要和类名匹配
    created_rooms = relationship("Room", back_populates="creator", foreign_keys="[Room.created_by]")
    room_memberships = relationship("PlayerInRoom", back_populates="user", cascade="all, delete-orphan")

# 房间模型
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # 房间名
    capacity = Column(Integer, default=4) # 容量，通常是4人，也可以是3人麻将
    status = Column(String(20), default=RoomStatus.WAITING) # 房间状态
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 实时数据存储：建议存 JSON 字符串，包含当前局的 wall, discards, turn 等信息
    # 崩溃恢复时可以从这里读取
    on_time_data = Column(Text, nullable=True)  
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    creator = relationship("User", back_populates="created_rooms", foreign_keys=[created_by])
    members = relationship("PlayerInRoom", back_populates="room", cascade="all, delete-orphan")
    records = relationship("Record", back_populates="room", cascade="all, delete-orphan")

# 玩家-房间关联模型 (处理座位、准备状态、当前局点数)
class PlayerInRoom(Base):
    __tablename__ = "player_in_rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    player_number = Column(Integer, nullable=False)  # 座位号: 0(东), 1(南), 2(西), 3(北)
    current_score = Column(Integer, default=25000)   # 这一场游戏的当前分数 (日麻通常25000起)
    is_ready = Column(Boolean, default=False)        # 是否已准备

    # 关系
    room = relationship("Room", back_populates="members", foreign_keys=[room_id])
    user = relationship("User", back_populates="room_memberships", foreign_keys=[user_id])

# 游戏记录模型 (用于通过牌谱回放)
class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False) # 修复：之前缺少这个外键列
    
    turn_count = Column(Integer, nullable=False) # 第几局 (例如: 东1局=0, 东2局=1...)
    
    # 牌谱数据：存储完整的动作序列 JSON
    # 格式示例: [{"type": "discard", "p": 0, "tile": "1m"}, ...]
    replay_data = Column(Text, nullable=True) 
    
    result_data = Column(Text, nullable=True) # 这一局的结果 JSON (谁胡了，多少番)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    room = relationship("Room", back_populates="records", foreign_keys=[room_id])