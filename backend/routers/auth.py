# backend/routers/auth.py
from fastapi import APIRouter

# 빈 라우터 생성 (에러 방지용)
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.get("/")
def read_auth_root():
    return {"message": "Auth router is working"}