from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
import json
from decimal import Decimal

from models import Question
from schemas import QuestionExtractionResult, TestParseResult, AnswerKeyResult
from dependencies import get_db

router = APIRouter(prefix="/question-papers", tags=["문제지"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_question_paper(
    extraction_result_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    test_parse.py의 결과(시험지 문제 추출 JSON 결과)를 받아서 Question에 저장 (인증 없음)
    
    - extraction_result_json: test_parse.py의 parse_exam 함수 반환 형식 JSON
      {
        "problems": [
          {
            "problem_index": 1,
            "question_count": 2,
            "score": 40,
            "raw_text": "문제 텍스트..."
          }
        ],
        "total_score": 100
      }
    """
    try:
        questions_created = []
        parsed_data = None
        
        # JSON 파싱
        try:
            parsed_data = json.loads(extraction_result_json)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON 파싱 실패: {str(e)}"
            )
        
        # test_parse.py 결과 형식 검증
        try:
            test_parse_result = TestParseResult(**parsed_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"test_parse.py 결과 형식 검증 실패: {str(e)}"
            )
        
        # 문제가 없는지 확인
        if not test_parse_result.problems:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="추출된 문제가 없습니다."
            )
        
        # test_parse.py 결과를 Question 모델에 저장
        for problem in test_parse_result.problems:
            # 문항 번호 중복 확인
            existing_question = db.query(Question).filter(
                Question.number == problem.problem_index
            ).first()
            
            if existing_question:
                # 기존 문항 업데이트
                existing_question.text = problem.raw_text
                existing_question.score = Decimal(str(problem.score))
            else:
                # 새 문항 생성
                db_question = Question(
                    number=problem.problem_index,
                    text=problem.raw_text,
                    score=Decimal(str(problem.score))
                )
                db.add(db_question)
                questions_created.append(db_question)
        
        db.commit()
        
        # 생성된 문항들 refresh
        for q in questions_created:
            db.refresh(q)
        
        return {
            "message": "문제지 정보가 저장되었습니다.",
            "questions_created": len(questions_created),
            "total_questions": len(test_parse_result.problems),
            "total_score": test_parse_result.total_score
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제지 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/answer-key", status_code=status.HTTP_201_CREATED)
async def upload_answer_key(
    answer_key_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    정답표 JSON을 받아서 Question 모델의 answer_text에 저장 (인증 없음)
    score.py 형식의 JSON을 받습니다.
    
    - answer_key_json: 정답표 JSON
      {
        "answers": [
          {
            "question_number": 1,
            "answer_text": "정답 텍스트..."
          },
          {
            "question_number": 2,
            "answer_text": "정답 텍스트..."
          }
        ]
      }
    """
    try:
        parsed_data = None
        
        # JSON 파싱
        try:
            parsed_data = json.loads(answer_key_json)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON 파싱 실패: {str(e)}"
            )
        
        # 정답표 형식 검증
        try:
            answer_key_result = AnswerKeyResult(**parsed_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"정답표 형식 검증 실패: {str(e)}"
            )
        
        # 정답이 없는지 확인
        if not answer_key_result.answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="정답이 없습니다."
            )
        
        updated_count = 0
        
        # 정답표를 Question 모델에 저장
        for answer_item in answer_key_result.answers:
            # 문항 조회
            question = db.query(Question).filter(
                Question.number == answer_item.question_number
            ).first()
            
            if question:
                # 기존 문항에 정답 업데이트
                question.answer_text = answer_item.answer_text
                updated_count += 1
            else:
                # 문항이 없으면 경고만 (문항은 먼저 생성되어야 함)
                continue
        
        db.commit()
        
        return {
            "message": "정답표가 저장되었습니다.",
            "updated_questions": updated_count,
            "total_answers": len(answer_key_result.answers)
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"정답표 저장 중 오류가 발생했습니다: {str(e)}"
        )

