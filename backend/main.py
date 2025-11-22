from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import documents, exams, question_papers, answer_sheets, analysis

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="REALThon API", version="1.0.0")

# 정적 파일 서빙 (업로드된 PDF 접근용)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (프로덕션에서는 특정 도메인으로 제한)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(documents.router)
app.include_router(exams.router)
app.include_router(question_papers.router)
app.include_router(answer_sheets.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    return {"message": "REALThon API"}

