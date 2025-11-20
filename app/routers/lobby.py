from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.database import get_db
from app.models import Room, User, PlayerInRoom, RoomStatus
from app.schemas import RoomCreate, RoomListItem, RoomDetail
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=RoomListItem)
async def create_room_api(
    room_in: RoomCreate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新房间 (HTTP 接口)
    """
    # 1. 检查同名房间
    result = await db.execute(select(Room).where(Room.name == room_in.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Room name already exists")

    # 2. 创建房间
    new_room = Room(
        name=room_in.name,
        capacity=room_in.capacity,
        created_by=current_user.id,
        status=RoomStatus.WAITING
    )
    db.add(new_room)
    await db.flush() # 拿到 ID

    # 3. 自动将房主加入房间 (座位0)
    creator_player = PlayerInRoom(
        room_id=new_room.id,
        user_id=current_user.id,
        player_number=0,
        is_ready=True
    )
    db.add(creator_player)
    await db.commit()
    
    # 4. 构造返回数据 (手动填充 computed fields)
    return RoomListItem(
        id=new_room.id,
        name=new_room.name,
        capacity=new_room.capacity,
        status=new_room.status,
        created_by=new_room.created_by,
        created_at=new_room.created_at,
        current_player_count=1, # 刚创建只有1人
        creator_username=current_user.username
    )

@router.get("/", response_model=List[RoomListItem])
async def get_rooms(
    skip: int = 0, 
    limit: int = 20, 
    status: str = Query(RoomStatus.WAITING, description="Filter by status (WAITING/PLAYING)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取大厅房间列表
    """
    # 这是一个复杂的查询：需要 Room 信息 + 关联的 User(房主) + 计算 PlayerInRoom 数量
    # 为了性能，这里我们用 Python 层面的处理或者预加载 (Eager Loading)
    
    query = (
        select(Room)
        .options(selectinload(Room.members), selectinload(Room.creator)) # 预加载 members 和 creator
        .where(Room.status == status)
        .order_by(Room.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    rooms = result.scalars().all()
    
    # 转换为 Schema 格式
    response_data = []
    for room in rooms:
        response_data.append(RoomListItem(
            id=room.id,
            name=room.name,
            capacity=room.capacity,
            status=room.status,
            created_by=room.created_by,
            created_at=room.created_at,
            current_player_count=len(room.members), # 统计人数
            creator_username=room.creator.username if room.creator else "Unknown"
        ))
        
    return response_data

@router.get("/{room_id}", response_model=RoomDetail)
async def get_room_detail(
    room_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # 需登录查看
):
    """
    获取单个房间详情（包括已有玩家名单）
    """
    query = (
        select(Room)
        .where(Room.id == room_id)
        .options(
            selectinload(Room.creator),
            selectinload(Room.members).selectinload(PlayerInRoom.user) # 嵌套预加载：Room -> Members -> User
        )
    )
    result = await db.execute(query)
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    # 构造玩家列表
    player_list = []
    for p in room.members:
        player_list.append({
            "user_id": p.user_id,
            "username": p.user.username if p.user else "Unknown",
            "player_number": p.player_number,
            "is_ready": p.is_ready
        })
        
    return RoomDetail(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        status=room.status,
        created_by=room.created_by,
        created_at=room.created_at,
        current_player_count=len(room.members),
        creator_username=room.creator.username,
        players=player_list
    )