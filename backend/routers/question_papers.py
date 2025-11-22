from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
import json

from models import Question
from schemas import QuestionExtractionResult
from dependencies import get_db

router = APIRouter(prefix="/question-papers", tags=["문제지"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_question_paper(
    extraction_result_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    LLM 추출 결과(문제, 문항수, 배점) JSON 받아서 Question에 저장 (인증 없음)
    PDF 파일은 저장하지 않음
    
    - extraction_result: LLM이 추출한 문제지 정보 (JSON)
    """
    try:
        # LLM 추출 결과 검증
        questions_created = []
        extraction_result = None
        try:
            extraction_result = QuestionExtractionResult(**json.loads(extraction_result_json))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LLM 추출 결과 JSON 파싱 실패: {str(e)}"
            )
        
        if extraction_result:
            for question_item in extraction_result.questions:
                # 문항 번호 중복 확인 (exam_id 없이)
                existing_question = db.query(Question).filter(
                    Question.number == question_item.number
                ).first()
                
                if existing_question:
                    # 기존 문항 업데이트
                    existing_question.text = question_item.text
                    existing_question.score = question_item.score
                else:
                    # 새 문항 생성 (exam_id는 None, 시험 하나만 있다고 가정)
                    db_question = Question(
                        exam_id=None,
                        number=question_item.number,
                        text=question_item.text,
                        score=question_item.score
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
            "total_questions": extraction_result.total_questions
        }
    
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

