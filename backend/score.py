import os
import sys
import base64
import json
import glob
from pathlib import Path
from decimal import Decimal
from openai import OpenAI
from dotenv import load_dotenv

# 상위 디렉토리를 경로에 추가 (backend 모듈 import를 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import AnswerSheet, Answer, Question

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenAI API 키를 환경변수에서 읽어오기
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

def parse_sheet(image_path: str) -> dict:
    image_data_url = encode_image(image_path)

    prompt = """
이미지에는 한 학생의 답안이 있으며,
상단에 "학번 : XXXX" 형식의 텍스트와
그 아래에 '문항'과 '점수' 헤더를 가진 표가 있습니다.

당신의 임무는 이미지에서 학번과 각 문항의 점수를 읽어,
아래 예시와 같은 형식의 JSON 한 개만 출력하는 것입니다.

예시:
{
  "student_code": "2271022",
  "answers": [
    {
      "question_number": 1,
      "answer_text": "",
      "score": 15
    },
    {
      "question_number": 2,
      "answer_text": "",
      "score": 15
    },
    {
      "question_number": 3,
      "answer_text": "",
      "score": 15
    },
    {
      "question_number": 4,
      "answer_text": "",
      "score": 20
    }
  ]
}

규칙:
- 최종 출력은 반드시 위 예시와 동일한 구조의 JSON 객체 하나여야 합니다.
- student_code:
  - "학번" 또는 "학 번"이라는 단어 뒤에 나오는 숫자 전체를 문자열로 넣으세요.
  - 숫자 사이에 공백이나 하이픈이 있어도 모두 붙인 하나의 문자열로 만드세요.
- answers:
  - 배열 형태로 각 문항의 정보를 저장합니다.
  - 각 항목은 question_number, answer_text, score를 포함합니다.
  - question_number:
    - 표에서 '문항' 열에 있는 값을 정수형 숫자로 넣으세요. (예: "1" → 1)
  - answer_text:
    - 답안 텍스트가 없으므로 빈 문자열("")로 넣으세요.
  - score:
    - 같은 행의 '점수' 열 값을 정수형 숫자로 넣으세요. (예: "15" → 15)
  - 문항 번호가 숫자가 아니거나, 점수가 인식되지 않은 행은 무시하세요.
  - 표에 존재하는 모든 문항을 누락 없이 포함하세요.
- 표에 다른 열이 더 있더라도, '문항'과 '점수' 두 열만 사용하세요.
- JSON 이외의 설명, 주석, 불필요한 텍스트는 절대 출력하지 마세요.
"""



    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 또는 gpt-4o / gpt-4.1 등 비전 지원 모델
        response_format={"type": "json_object"},  # JSON 모드
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # 모델이 반환한 JSON 문자열 파싱
    content = response.choices[0].message.content
    result = json.loads(content)

    return result


def save_to_db(result: dict, db) -> dict:
    """parse_sheet 결과를 DB에 저장"""
    from schemas import AnswerExtractionResult
    
    try:
        # 스키마 검증
        extraction_result = AnswerExtractionResult(**result)
        
        # AnswerSheet 생성 또는 조회
        student_code = extraction_result.student_code
        answer_sheet = db.query(AnswerSheet).filter(
            AnswerSheet.student_code == student_code
        ).first()
        
        if not answer_sheet:
            # 새 답안지 생성
            answer_sheet = AnswerSheet(
                student_code=student_code
            )
            db.add(answer_sheet)
            db.flush()  # ID를 얻기 위해 flush
        
        # Answer에 저장
        saved_count = 0
        for answer_item in extraction_result.answers:
            # 문항 조회
            question = db.query(Question).filter(
                Question.number == answer_item.question_number
            ).first()
            
            if not question:
                continue  # 문항이 없으면 스킵
            
            # 기존 답변 확인
            existing_answer = db.query(Answer).filter(
                Answer.answer_sheet_id == answer_sheet.id,
                Answer.question_id == question.id
            ).first()
            
            if existing_answer:
                # 기존 답변 업데이트
                existing_answer.answer_text = answer_item.answer_text
                existing_answer.raw_score = Decimal(str(answer_item.score)) if answer_item.score else None
            else:
                # 새 답변 생성
                db_answer = Answer(
                    answer_sheet_id=answer_sheet.id,
                    question_id=question.id,
                    answer_text=answer_item.answer_text,
                    raw_score=Decimal(str(answer_item.score)) if answer_item.score else None
                )
                db.add(db_answer)
                saved_count += 1
        
        db.commit()
        return {"success": True, "student_code": student_code, "saved_count": saved_count}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 점수 폴더의 모든 png 파일을 찾기
    score_folder = "점수"
    image_files = sorted(glob.glob(os.path.join(score_folder, "*.png")))
    
    if not image_files:
        print(f"'{score_folder}' 폴더에 PNG 파일이 없습니다.")
        exit(1)
    
    print(f"{len(image_files)}개의 이미지 파일을 찾았습니다.")
    
    # DB 세션 생성
    db = SessionLocal()
    
    success_count = 0
    error_count = 0
    
    try:
        for idx, image_path in enumerate(image_files, 1):
            filename = Path(image_path).name
            print(f"\n[{idx}/{len(image_files)}] 처리 중: {filename}")
            
            try:
                # 이미지 파싱
                result = parse_sheet(image_path)
                print(f" 파싱 완료: 학번 {result.get('student_code', 'N/A')}")
                
                # DB에 저장
                save_result = save_to_db(result, db)
                if save_result["success"]:
                    print(f" DB 저장 완료: {save_result['saved_count']}개 답변 저장")
                    success_count += 1
                else:
                    print(f" DB 저장 실패: {save_result.get('error', 'Unknown error')}")
                    error_count += 1
                    
            except Exception as e:
                print(f" 오류: {e}")
                error_count += 1
                # 에러가 나도 계속 진행
        
        print(f"\n{'='*50}")
        print(f"처리 완료: 성공 {success_count}개, 실패 {error_count}개")
        print(f"총 {len(image_files)}개의 시험지 처리 완료")
        print(f"{'='*50}")
    
    finally:
        db.close()
