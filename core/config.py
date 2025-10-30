import os
from typing import Any, Dict, Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Settings(BaseSettings):
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")  # 生产环境中应使用安全的随机密钥
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # 数据库配置
    MYSQL_SERVER: str = os.getenv("MYSQL_SERVER", "localhost")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "game_db")
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"mysql+aiomysql://{values.get('MYSQL_USER')}:{values.get('MYSQL_PASSWORD')}@{values.get('MYSQL_SERVER')}/{values.get('MYSQL_DB')}"

    # 游戏配置
    MAX_PLAYERS_PER_ROOM: int = int(os.getenv("MAX_PLAYERS_PER_ROOM", "4"))
    ROOM_CODE_LENGTH: int = int(os.getenv("ROOM_CODE_LENGTH", "6"))

    # 网站信息
    APP_NAME: str = os.getenv("APP_NAME", "Online Multiplayer Game")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "FastAPI backend for online multiplayer game")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
