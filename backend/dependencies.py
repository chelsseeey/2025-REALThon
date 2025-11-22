from sqlalchemy.orm import Session
from database import SessionLocal

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

