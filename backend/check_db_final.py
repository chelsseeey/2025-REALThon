import sys
import os

# 1. 로깅 시작
print(">>> SCRIPT START", flush=True)

# 2. 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, text
    print(">>> SQLAlchemy Imported", flush=True)
except ImportError as e:
    print(f">>> Import Failed: {e}", flush=True)
    sys.exit(1)

def test():
    # =================================================================
    # ★ 핵심: 여기서 +psycopg를 강제로 넣어서 연결합니다.
    # 본인의 ID/PW/DB명에 맞게 아래 문자열을 수정해서 쓰셔도 됩니다.
    # =================================================================
    
    # 기본값 (환경변수 무시하고 직접 테스트)
    DB_URL = "postgresql+psycopg://realthon:realthon123@localhost:5432/realthon_db"
    
    print(f">>> Testing Connection to: {DB_URL}", flush=True)
    
    try:
        # 엔진 생성
        engine = create_engine(DB_URL)
        
        # 연결 시도
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f">>> [SUCCESS] Connected! DB Version: {version}", flush=True)
            
    except Exception as e:
        print(f">>> [ERROR] Connection Failed: {e}", flush=True)
        print(">>> Tip: ID, 비밀번호, DB이름(realthon_db)이 정확한지 확인하세요.")

if __name__ == "__main__":
    test()