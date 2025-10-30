import json
from typing import Dict, List, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from core.config import settings
from core.db import get_async_db
from models.room import Room, PlayerInRoom
from models.user import User

router = APIRouter()

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        # 存储房间连接：room_code -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_code: str):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = set()
        self.active_connections[room_code].add(websocket)
    
    def disconnect(self, websocket: WebSocket, room_code: str):
        if room_code in self.active_connections:
            self.active_connections[room_code].discard(websocket)
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]
    
    async def broadcast(self, room_code: str, message: dict):
        """
        向房间内所有连接的客户端广播消息
        """
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code].copy():
                await connection.send_json(message)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        向特定客户端发送消息
        """
        await websocket.send_json(message)


manager = ConnectionManager()

# 用于WebSocket认证的依赖项
oauth2_scheme_ws = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user_ws(
    token: str = Depends(oauth2_scheme_ws),
    db: Session = Depends(get_async_db)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
            )
    except (JWTError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
        )

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@router.websocket("/ws/{room_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_code: str,
    token: str
):
    # 验证用户
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            await websocket.close(code=1008)  # Policy violation
            return
    except (JWTError):
        await websocket.close(code=1008)
        return
    
    # 获取数据库连接
    db = next(get_async_db())
    
    try:
        # 验证用户是否存在
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return
        
        # 验证房间是否存在
        result = await db.execute(select(Room).filter(Room.room_code == room_code))
        room = result.scalars().first()
        if not room:
            await websocket.close(code=1008)
            return
        
        # 验证用户是否在房间内
        result = await db.execute(
            select(PlayerInRoom).filter(
                PlayerInRoom.user_id == user.id,
                PlayerInRoom.room_id == room.id
            )
        )
        player_in_room = result.scalars().first()
        if not player_in_room:
            await websocket.close(code=1008)
            return
        
        # 接受连接
        await manager.connect(websocket, room_code)
        
        try:
            # 通知其他玩家有新玩家加入
            await manager.broadcast(room_code, {
                "event": "player_joined",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "is_admin": player_in_room.is_admin
                }
            })
            
            while True:
                data = await websocket.receive_json()
                event = data.get("event")
                event_data = data.get("data", {})
                
                if event == "player_ready":
                    # 处理玩家准备
                    await handle_player_ready(room, user, db, manager)
                elif event == "player_unready":
                    # 处理玩家取消准备
                    await handle_player_unready(room, user, db, manager)
                elif event == "start_game":
                    # 处理开始游戏
                    await handle_start_game(room, user, db, manager)
                elif event == "game_action":
                    # 处理游戏动作（示例）
                    await handle_game_action(room, user, event_data, db, manager)
        
        except WebSocketDisconnect:
            # 处理玩家断开连接
            await handle_player_disconnect(room, user, db, manager)
        finally:
            manager.disconnect(websocket, room_code)
    
    finally:
        await db.close()


async def handle_player_ready(room: Room, user: User, db: Session, manager: ConnectionManager):
    """
    处理玩家准备事件
    """
    if room.is_game_started:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "Game has already started"}
        }, websocket)
        return
    
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room:
        return
    
    player_in_room.is_ready = True
    await db.commit()
    
    # 获取房间内所有玩家
    result = await db.execute(
        select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id)
    )
    players = result.scalars().all()
    
    # 检查是否所有玩家都已准备
    all_ready = all(player.is_ready for player in players)
    
    # 广播玩家准备状态
    await manager.broadcast(room.room_code, {
        "event": "player_ready",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "all_ready": all_ready
        }
    })


async def handle_player_unready(room: Room, user: User, db: Session, manager: ConnectionManager):
    """
    处理玩家取消准备事件
    """
    if room.is_game_started:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "Game has already started"}
        }, websocket)
        return
    
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room:
        return
    
    player_in_room.is_ready = False
    await db.commit()
    
    # 广播玩家取消准备状态
    await manager.broadcast(room.room_code, {
        "event": "player_unready",
        "data": {
            "user_id": user.id,
            "username": user.username
        }
    })


async def handle_start_game(room: Room, user: User, db: Session, manager: ConnectionManager):
    """
    处理开始游戏事件
    """
    if room.is_game_started:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "Game has already started"}
        }, websocket)
        return
    
    # 检查是否为管理员
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room or not player_in_room.is_admin:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "Only the room admin can start the game"}
        }, websocket)
        return
    
    # 获取房间内所有玩家
    result = await db.execute(
        select(PlayerInRoom).filter(PlayerInRoom.room_id == room.id)
    )
    players = result.scalars().all()
    
    # 检查是否所有玩家都已准备
    all_ready = all(player.is_ready for player in players)
    if not all_ready:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "All players must be ready to start the game"}
        }, websocket)
        return
    
    # 开始游戏
    room.is_game_started = True
    await db.commit()
    
    # 获取玩家信息
    player_list = []
    for player in players:
        result = await db.execute(select(User).filter(User.id == player.user_id))
        player_user = result.scalars().first()
        player_list.append({
            "user_id": player_user.id,
            "username": player_user.username
        })
    
    # 广播游戏开始
    await manager.broadcast(room.room_code, {
        "event": "game_start",
        "data": {
            "players": player_list
        }
    })


async def handle_game_action(room: Room, user: User, action_data: dict, db: Session, manager: ConnectionManager):
    """
    处理游戏动作事件（示例）
    """
    if not room.is_game_started:
        await manager.send_personal_message({
            "event": "error",
            "data": {"message": "Game has not started yet"}
        }, websocket)
        return
    
    # 验证用户是否在房间内
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room:
        return
    
    # 广播游戏动作
    await manager.broadcast(room.room_code, {
        "event": "game_action",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "action": action_data.get("action"),
            "details": action_data.get("details")
        }
    })


async def handle_player_disconnect(room: Room, user: User, db: Session, manager: ConnectionManager):
    """
    处理玩家断开连接事件
    """
    # 查找用户在房间中的记录
    result = await db.execute(
        select(PlayerInRoom).filter(
            PlayerInRoom.user_id == user.id,
            PlayerInRoom.room_id == room.id
        )
    )
    player_in_room = result.scalars().first()
    
    if not player_in_room:
        return
    
    # 检查是否为管理员
    is_admin = player_in_room.is_admin
    
    # 删除用户在房间中的记录
    await db.delete(player_in_room)
    
    # 如果是管理员且房间还有其他玩家，需要转移管理员权限
    new_admin = None
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
            
            # 获取新管理员的用户信息
            result = await db.execute(select(User).filter(User.id == new_admin.user_id))
            new_admin_user = result.scalars().first()
        else:
            # 如果没有其他玩家，删除房间
            await db.delete(room)
    
    await db.commit()
    
    # 广播玩家离开
    message = {
        "event": "player_left",
        "data": {
            "user_id": user.id,
            "username": user.username
        }
    }
    
    # 如果有新管理员，添加到消息中
    if new_admin and new_admin_user:
        message["data"]["new_admin"] = {
            "user_id": new_admin_user.id,
            "username": new_admin_user.username
        }
    
    await manager.broadcast(room.room_code, message)
