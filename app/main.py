# app/main.py
import socketio
from fastapi import FastAPI
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

# 导入本地模块
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth,lobby
from app.security import decode_access_token
from app.game_manager import room_manager
from app.models import Room, PlayerInRoom, RoomStatus, User, Record

# --- 1. 配置 FastAPI 和 Socket.IO ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# 挂载认证路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/api/lobby", tags=["lobby"])

# 挂载 Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.on_event("startup")
async def startup():
    # 初始化数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- 2. Socket.IO 中间件：身份验证 ---

@sio.event
async def connect(sid, environ, auth):
    """
    连接时验证 Token，并将 user_id 存入 session
    """
    token = None
    # 1. 尝试从 auth 字典获取
    if auth and 'token' in auth:
        token = auth['token']
    # 2. 尝试从 URL 参数获取 (方便调试)
    elif 'QUERY_STRING' in environ:
        import urllib.parse
        qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
        if 'token' in qs:
            token = qs['token'][0]

    if not token:
        print(f"Connection rejected: No token {sid}")
        return False
    
    # 处理 Bearer 前缀
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    payload = decode_access_token(token)
    if not payload:
        print(f"Connection rejected: Invalid token {sid}")
        return False
    
    user_id = payload.get("user_id")
    username = payload.get("sub")
    
    # 将用户信息存入 Socket 会话，后续事件直接使用
    await sio.save_session(sid, {'user_id': user_id, 'username': username})
    
    print(f"User {username}({user_id}) connected as {sid}")
    await sio.emit('response', {'message': f'Welcome {username}!'}, room=sid)

# --- 3. 业务逻辑事件 ---

@sio.event
async def create_room(sid, data):
    """
    创建房间
    Data: {'room_name': 'xxx'}
    """
    session = await sio.get_session(sid)
    user_id = session['user_id']
    room_name = data.get('room_name')

    if not room_name:
        await sio.emit('error', {'msg': 'Room name required'}, room=sid)
        return

    async with AsyncSessionLocal() as db:
        try:
            # 1. 数据库：创建房间
            new_room = Room(name=room_name, created_by=user_id, status=RoomStatus.WAITING)
            db.add(new_room)
            await db.flush() # 获取 ID

            # 2. 数据库：创建房主记录 (座位0)
            player_entry = PlayerInRoom(
                room_id=new_room.id, 
                user_id=user_id, 
                player_number=0,
                is_ready=True
            )
            db.add(player_entry)
            await db.commit()

            # 3. 内存：初始化游戏房间
            maj_room = room_manager.create_room(new_room.id, room_name)
            if maj_room:
                maj_room.add_player(sid, user_id)
                
                sio.enter_room(sid, room_name)
                await sio.emit('room_joined', {
                    'room_id': new_room.id, 
                    'room_name': room_name,
                    'msg': 'Room created'
                }, room=sid)
            else:
                await sio.emit('error', {'msg': 'Memory error'}, room=sid)

        except IntegrityError:
            await db.rollback()
            await sio.emit('error', {'msg': 'Room name already exists'}, room=sid)
        except Exception as e:
            await db.rollback()
            print(f"Create Error: {e}")
            await sio.emit('error', {'msg': 'Internal server error'}, room=sid)

@sio.event
async def join_room(sid, data):
    """
    加入房间
    Data: {'room_name': 'xxx'}
    """
    session = await sio.get_session(sid)
    user_id = session['user_id']
    room_name = data.get('room_name')

    async with AsyncSessionLocal() as db:
        # 1. 查找房间及当前玩家
        result = await db.execute(
            select(Room).where(Room.name == room_name)
        )
        db_room = result.scalars().first()

        if not db_room:
            await sio.emit('error', {'msg': 'Room not found'}, room=sid)
            return

        # 获取已在房间的玩家
        p_result = await db.execute(
            select(PlayerInRoom).where(PlayerInRoom.room_id == db_room.id)
        )
        current_players = p_result.scalars().all()

        # 2. 检查是否已加入
        for p in current_players:
            if p.user_id == user_id:
                # 已在房间，可能是重连
                # 这里简单处理：让 socket 重新加入房间频道
                sio.enter_room(sid, room_name)
                
                # 尝试更新内存中的 sid
                maj_room = room_manager.get_room(room_name)
                if maj_room:
                    # 注意：这里需要复杂的重连逻辑来替换旧sid，这里简化处理
                    pass 
                    
                await sio.emit('room_joined', {'room_name': room_name, 'msg': 'Welcome back'}, room=sid)
                return

        # 3. 检查满员
        if len(current_players) >= db_room.capacity:
            await sio.emit('error', {'msg': 'Room is full'}, room=sid)
            return

        # 4. 数据库：写入新玩家
        seat_num = len(current_players)
        new_player = PlayerInRoom(
            room_id=db_room.id,
            user_id=user_id,
            player_number=seat_num,
            is_ready=True # 简化逻辑：加入即准备
        )
        db.add(new_player)
        
        # 如果加入后满员，更新房间状态
        start_game = False
        if len(current_players) + 1 == db_room.capacity:
            db_room.status = RoomStatus.PLAYING
            start_game = True
            
        await db.commit()

        # 5. 内存：同步状态
        maj_room = room_manager.get_room(room_name)
        if not maj_room:
            # 如果内存中没有（可能是重启后），重新创建
            maj_room = room_manager.create_room(db_room.id, room_name)
            # 恢复已有的其他玩家（此处简化，仅为防止报错）
            for existing_p in current_players:
                 # 注意：这里没有真实sid，无法推送到旧玩家，实际生产需配合 Redis 存储 sid
                 maj_room.add_player("offline", existing_p.user_id)

        maj_room.add_player(sid, user_id)
        sio.enter_room(sid, room_name)

        # 广播新玩家加入
        await sio.emit('room_joined', {
            'room_name': room_name, 
            'player_count': len(current_players) + 1
        }, room=room_name)

        # 6. 游戏开始逻辑
        if start_game:
            print(f"Room {room_name} is starting!")
            maj_room.init_game()
            
            # 给房间里每个人发牌
            # maj_room.players 存的是 sid
            for i, p_sid in enumerate(maj_room.players):
                if p_sid == "offline": continue
                
                await sio.emit('game_start', {
                    'hand': maj_room.hands[p_sid],
                    'seat': i,
                    'dora': maj_room.settings['dora'][0] # 示例：显示第一张宝牌
                }, room=p_sid)

@sio.event
async def action_discard(sid, data):
    """
    出牌
    Data: {'room_name': 'xxx', 'tile': '1m'}
    """
    session = await sio.get_session(sid)
    user_id = session['user_id'] # 可用于验证是否轮到该用户
    
    room_name = data.get('room_name')
    tile = data.get('tile')
    room = room_manager.get_room(room_name)
    
    if not room:
        return

    # 简单的出牌逻辑
    if tile in room.hands[sid]:
        room.hands[sid].remove(tile)
        room.discards.append(tile)
        
        # 广播出牌
        await sio.emit('player_discard', {
            'sid': sid, 
            'user_id': user_id,
            'tile': tile
        }, room=room_name)
        
        # 检查胡牌 (Ron)
        for other_sid in room.players:
            if other_sid != sid and other_sid != "offline":
                # 这里的 check_win 调用了 yaku_han 算法
                result = room.check_win(other_sid, tile)
                if result:
                    # 获取胡牌者的信息
                    # 在实际项目中，应该去 DB 查 username，这里简化
                    await sio.emit('win_declared', {
                        'winner_sid': other_sid,
                        'from_sid': sid,
                        'result': result # 包含番数、役种
                    }, room=room_name)
                    
                    # TODO: 游戏结束，写入 Record 到数据库
                    return

        # 如果没人胡牌，摸牌 (Draw)
        # 简单的轮转逻辑：下家摸牌
        # 找到当前玩家索引
        current_idx = room.players.index(sid)
        next_idx = (current_idx + 1) % 4
        next_sid = room.players[next_idx]
        
        new_tile = room.draw_tile(next_sid)
        if new_tile:
            # 私发给下家
            await sio.emit('player_draw', {'tile': new_tile}, room=next_sid)
            # 广播给其他人（不含牌内容）
            await sio.emit('player_draw_secret', {'user_idx': next_idx}, room=room_name, skip_sid=next_sid)
        else:
            await sio.emit('game_draw', {'msg': 'Wall is empty (Ryuukyoku)'}, room=room_name)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # 这里可以添加逻辑：如果正在游戏中，不移除玩家，而是标记掉线
    # 如果在等待中，则从 Room 移除