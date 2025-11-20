from pydantic import BaseModel, EmailStr
from typing import Optional

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