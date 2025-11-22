import sys
import os

# 1. Print immediately
print(">>> SCRIPT START", flush=True)

# 2. Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import engine
    from sqlalchemy import text
    print(">>> Import Success", flush=True)
except Exception as e:
    print(f">>> Import Failed: {e}", flush=True)
    sys.exit(1)

def test():
    print(">>> Connecting to Database...", flush=True)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(">>> [SUCCESS] Database Connected!", flush=True)
    except Exception as e:
        print(f">>> [ERROR] Connection Failed: {e}", flush=True)

if __name__ == "__main__":
    test()