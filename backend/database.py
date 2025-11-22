import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드 (환경 변수 강제 적용)
load_dotenv()

# 환경 변수 가져오기 (없으면 기본값)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://realthon:realthon123@localhost:5432/realthon_db")

# [핵심] 만약 URL이 옛날 방식(postgresql://)이라면 신버전(postgresql+psycopg://)으로 자동 교체
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델의 기본 클래스
Base = declarative_base()