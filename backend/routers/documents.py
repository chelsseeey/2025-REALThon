# backend/routers/documents.py
from fastapi import APIRouter

# 라우터 객체 생성
router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.get("/")
def read_documents_root():
    return {"message": "Documents router is working"}