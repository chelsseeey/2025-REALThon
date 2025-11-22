import os
import sys
import base64
import json
import re
from decimal import Decimal
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------------------------------------
# [설정] 백엔드 모듈 경로 및 DB 임포트
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Question
# -----------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

client = OpenAI(api_key=OPENAI_API_KEY)


def encode_image(image_path: str) -> str:
    """이미지를 base64 data URL 형태로 인코딩"""
    import mimetypes
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def count_subquestions(text: str) -> int:
    """문제 텍스트에서 소문항 개수 세기"""
    paren_nums = re.findall(r"\(\s*\d+\s*\)", text)
    circled_nums = re.findall(r"[①②③④⑤⑥⑦⑧⑨]", text)
    cnt = len(paren_nums) + len(circled_nums)
    return cnt if cnt > 0 else 1


def call_openai_for_problems(image_path: str) -> dict:
    """OpenAI API를 통해 문제 정보 추출"""
    image_data_url = encode_image(image_path)

    # ▼▼▼ [수정됨] "JSON" 단어 필수 포함 ▼▼▼
    system_prompt = """
    당신은 한국어 수학 시험지를 구조화하는 도우미입니다.
    이미지에서 각 문제의 번호, 문제 전체 텍스트, 문제의 배점을 추출하여 **JSON 형식**으로 출력해야 합니다.
    """

    user_prompt = """
    이미지에는 1, 2, 3 처럼 번호가 매겨진 '큰 문제'들이 있고,
    각 문제의 본문 끝에는 "[40점]", "[30점]"과 같이 배점이 적혀 있습니다.

    각 문제에 대해 다음 정보를 추출하여 JSON으로 반환해주세요.

    반환 형식(중요!):
    {
      "problems": [
        {
          "problem_index": 1,
          "raw_text": "문제 1 전체 텍스트 (지문 + 소문항 포함)",
          "score": 40
        }
      ]
    }

    규칙:
    - problem_index: 문제 번호를 정수로 추출.
    - raw_text: 문제의 모든 텍스트를 하나로 합침.
    - score: 배점을 정수로 추출.
    - 오직 JSON 데이터만 출력하세요.
    """

    resp = client.chat.completions.create(
        model="gpt-4o", 
        response_format={"type": "json_object"}, # 이 옵션을 쓰려면 프롬프트에 'JSON'이 있어야 함
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        max_tokens=1400,
    )

    content = resp.choices[0].message.content
    raw = json.loads(content)
    
    problems_out = []
    total_score = 0
    
    for p in raw.get("problems", []):
        idx = p.get("problem_index")
        text = p.get("raw_text", "")
        score = int(p.get("score", 0))
        
        q_count = count_subquestions(text)
        total_score += score
        
        problems_out.append({
            "problem_index": idx,
            "question_count": q_count,
            "score": score,
            "raw_text": text,
        })
    
    return {
        "problems": problems_out,
        "total_score": total_score,
    }


def save_questions_to_db(parse_result: dict):
    """파싱된 결과를 Question 테이블에 저장"""
    db = SessionLocal()
    saved_count = 0
    
    try:
        print("\n 데이터베이스 저장 시작...")
        problems = parse_result.get("problems", [])
        
        for p in problems:
            q_num = p["problem_index"]
            q_text = p["raw_text"]
            q_score = p["score"]
            
            # 이미 존재하는지 확인
            existing_q = db.query(Question).filter(Question.number == q_num).first()
            
            if existing_q:
                # 업데이트
                existing_q.text = q_text
                existing_q.score = Decimal(str(q_score))
                print(f"  [UPDATE] 문항 {q_num}번 업데이트됨")
            else:
                # 새로 생성
                new_q = Question(
                    number=q_num,
                    text=q_text,
                    score=Decimal(str(q_score))
                )
                db.add(new_q)
                print(f"  [INSERT] 문항 {q_num}번 새로 등록됨")
            
            saved_count += 1
            
        db.commit()
        print(f"총 {saved_count}개의 문제가 DB에 저장되었습니다.")
        
    except Exception as e:
        print(f" DB 저장 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


def parse_exam(image_path: str, output_json_path: str | None = None) -> dict:
    result = call_openai_for_problems(image_path)

    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    # 1. 이미지 파일 경로 (확인 필요)
    img = "문제지.png"  
    out = "문제지_parsed.json"

    if not os.path.exists(img):
        print(f" 오류: '{img}' 파일이 없습니다. 문제지 이미지를 준비해주세요.")
        exit(1)

    # 2. 파싱 실행 (LLM)
    print(f" '{img}' 분석 중... (OpenAI API 호출)")
    parsed_data = parse_exam(img, out)
    
    # 3. JSON 결과 출력
    print("\n--- [LLM 파싱 결과] ---")
    print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    print(f" 파일 저장 완료: {out}")

    # 4. DB 저장 실행
    save_questions_to_db(parsed_data)