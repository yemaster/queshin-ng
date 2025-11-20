import asyncio
from app.database import engine, AsyncSessionLocal, Base
from app.models import User

async def init_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # 创建两个测试用户
        user1 = User(username="player1", email="p1@test.com", hashed_password="pw1", points=1000)
        user2 = User(username="player2", email="p2@test.com", hashed_password="pw2", points=1000)
        user3 = User(username="player3", email="p3@test.com", hashed_password="pw3", points=1000)
        user4 = User(username="player4", email="p4@test.com", hashed_password="pw4", points=1000)
        
        db.add_all([user1, user2, user3, user4])
        try:
            await db.commit()
            print("测试用户创建成功！ID 分别为 1, 2, 3, 4")
        except Exception:
            print("用户可能已存在，跳过创建。")

if __name__ == "__main__":
    asyncio.run(init_data())