import random
import string
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from core.config import settings
from core.db import get_db, get_async_db
from models.room import Room, PlayerInRoom
from models.user import User
from api.deps import get_current_user

router = APIRouter()


def generate_room_code(length: int = settings.ROOM_CODE_LENGTH) -> str:
    """
    生成随机房间号
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


@router.post("/", response_model=dict)
async def create_room(
    max_players: int = settings.MAX_PLAYERS_PER_ROOM,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
) -> Any:
    """
    创建新房间
    """
    # 生成唯一房间号
    while True:
        room_code = generate_room_code()
        # 检查房间号是否已存在
        result = await db.execute(select(Room).filter(Room.room_code == room_code))
        if not result.scalars().first():
            break
    
    # 创建房间
    room = Room(
        room_code=room_code,
        max_players=max_players,
        created_by=current_user.id
    )
    db.add(room)
    await db.flush()  # 获取room.id
    
    # 添加创建者到房间
    player_in_room = PlayerInRoom(
        user_id=current_user.id,
        room_id=room.id,
        is_admin=True  # 创建者默认为管理员
    )
    db.add(player_in_room)
    await db.commit()
    
    return {
        "message": "Room created successfully",
        "room_code": room.room_code,
        "max_players": room.max_players
    }


@router.get("/", response_model=List[dict])
async def get_rooms(
    db: Session = Depends(get_async_db)
) -> Any:
    """
    获取所有房间列表
    """
    result = await db.execute(select(Room))
    rooms = result.scalars().all()
    
    room_list = []
    for room in rooms:
        # 获取房间内玩家数量
        player_count = await db.scalar(
            select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id).count()
        )
        
        room_list.append({
            "room_code": room.room_code,
            "max_players": room.max_players,
            "current_players": player_count,
            "is_game_started": room.is_game_started,
            "created_at": room.created_at
        })
    
    return room_list


@router.get("/{room_code}", response_model=dict)
async def get_room_detail(
    room_code: str,
    db: Session = Depends(get_async_db)
) -> Any:
    """
    获取房间详情
    """
    result = await db.execute(select(Room).filter(Room.room_code == room_code))
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # 获取房间内玩家列表
    result = await db.execute(
        select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id)
    )
    players = result.scalars().all()
    
    player_list = []
    for player in players:
        # 获取玩家信息
        result = await db.execute(select(User).filter(User.id == player.user_id))
        user = result.scalars().first()
        
        player_list.append({
            "user_id": user.id,
            "username": user.username,
            "is_ready": player.is_ready,
            "is_admin": player.is_admin,
            "joined_at": player.joined_at
        })
    
    return {
        "room_code": room.room_code,
        "max_players": room.max_players,
        "current_players": len(player_list),
        "is_game_started": room.is_game_started,
        "created_at": room.created_at,
        "players": player_list
    }


@router.post("/{room_code}/join", response_model=dict)
async def join_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
) -> Any:
    """
    加入房间
    """
    # 查找房间
    result = await db.execute(select(Room).filter(Room.room_code == room_code))
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # 检查房间是否已满
    player_count = await db.scalar(
        select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id).count()
    )
    if player_count >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full"
        )
    
    # 检查游戏是否已开始
    if room.is_game_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game has already started"
        )
    
    # 检查用户是否已在房间内
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == current_user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already in this room"
        )
    
    # 添加用户到房间
    player_in_room = PlayerInRoom(
        user_id=current_user.id,
        room_id=room.id,
        is_admin=False  # 非创建者默认为普通玩家
    )
    db.add(player_in_room)
    await db.commit()
    
    return {
        "message": "Joined room successfully",
        "room_code": room.room_code
    }


@router.post("/{room_code}/leave", response_model=dict)
async def leave_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
) -> Any:
    """
    离开房间
    """
    # 查找房间
    result = await db.execute(select(Room).filter(Room.room_code == room_code))
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # 查找用户在房间中的记录
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == current_user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not in this room"
        )
    
    # 检查是否为管理员
    is_admin = player_in_room.is_admin
    
    # 删除用户在房间中的记录
    await db.delete(player_in_room)
    
    # 如果是管理员且房间还有其他玩家，需要转移管理员权限
    if is_admin:
        # 获取房间内剩余玩家
        result = await db.execute(
            select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id)
        )
        remaining_players = result.scalars().all()
        
        if remaining_players:
            # 选择最早加入的玩家作为新管理员
            new_admin = min(remaining_players, key=lambda p: p.joined_at)
            new_admin.is_admin = True
        else:
            # 如果没有其他玩家，删除房间
            await db.delete(room)
    
    await db.commit()
    
    return {
        "message": "Left room successfully"
    }
