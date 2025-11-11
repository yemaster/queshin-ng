from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey,Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base

# 用户模型
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    created_rooms = relationship("Room", back_populates="creator", foreign_keys="[Room.created_by]")
    room_memberships = relationship("PlayerInRoom", back_populates="user", cascade="all, delete-orphan")
    
# 房间模型(暂时放在这)
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    capacity = Column(Integer, default=4)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    on_time_data = Column(Text, nullable=True)  # 实时数据存储
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # 关系
    creator = relationship("User", back_populates="created_rooms", foreign_keys=[created_by])
    members = relationship("PlayerInRoom", back_populates="room", cascade="all, delete-orphan")
    records = relationship("Record", back_populates="room", cascade="all, delete-orphan")
    
# 玩家-房间关联模型
class PlayerInRoom(Base):
    __tablename__ = "player_in_rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_number = Column(Integer, nullable=False)  #起始顺序标识
    points = Column(Integer, default=0)  # 玩家在该房间中的积分

    # 关系
    room = relationship("Room", back_populates="members", foreign_keys=[room_id])
    user = relationship("User", back_populates="room_memberships", foreign_keys=[user_id])

# 游戏记录模型
class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    turn= Column(Integer, nullable=False)
    replay= Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    room = relationship("Room", back_populates="records", foreign_keys="[Record.room_id]")

async def end_game():
    
async def end_round():