from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. 检查用户名或邮箱是否已存在
    result = await db.execute(select(User).where((User.username == user.username) | (User.email == user.email)))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # 2. 创建新用户
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        points=1000 # 初始积分
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # OAuth2PasswordRequestForm 会自动从请求表单中提取 username 和 password
    # 注意：这里 username 字段可以填用户名也可以填邮箱，看你逻辑，这里默认用 username
    
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成 Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # 我们在 Token 里存 user_id 和 sub (username)，方便解析
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }