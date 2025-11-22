from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import answer_sheets, answer_key, question_papers  
Base.metadata.create_all(bind=engine)
app = FastAPI(title="REALThon API", version="1.0.0")
origins = [
    "http://localhost:3000",  # 리액트/Next.js 기본 포트
    "http://localhost:5173",  # Vite(Vue/React) 기본 포트
    "*"                       # (개발용) 모든 곳에서 허용하려면 이걸 쓰세요
]
# 라우터 등록
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (프로덕션에서는 특정 도메인으로 제한)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(answer_sheets.router)
app.include_router(answer_key.router)
app.include_router(question_papers.router)



@app.get("/")
async def root():
    return {"message": "REALThon API"}

