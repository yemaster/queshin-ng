from fastapi import APIRouter

from api.api_v1.endpoints import auth, rooms, ws

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(ws.router, tags=["ws"])
