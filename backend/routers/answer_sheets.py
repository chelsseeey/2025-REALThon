from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
import json

from models import AnswerSheet, Answer, Question
from schemas import AnswerExtractionResult
from dependencies import get_db

router = APIRouter(prefix="/answer-sheets", tags=["답안지"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_answer_sheets(
    extraction_results_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    여러개의 답안지 LLM 추출 결과(학생별 문항별 답안, 점수) JSON 받아서 Answer에 저장 (인증 없음)
    PDF 파일은 저장하지 않음
    
    - extraction_results_json: LLM 추출 결과들 (JSON 배열 문자열)
    """
    try:
        # LLM 추출 결과 파싱
        extraction_results = []
        try:
            results_list = json.loads(extraction_results_json)
            extraction_results = [AnswerExtractionResult(**result) for result in results_list]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LLM 추출 결과 JSON 파싱 실패: {str(e)}"
            )
        
        uploaded_sheets = []
        
        # 각 추출 결과 처리
        for idx, extraction_result in enumerate(extraction_results):
            
            # AnswerSheet 생성 또는 조회 (student_code만으로)
            student_code = extraction_result.student_code if extraction_result else f"student_{idx}"
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
            
            # LLM 추출 결과로 Answer에 저장
            if extraction_result:
                for answer_item in extraction_result.answers:
                    # 문항 조회 (number만으로)
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
                        existing_answer.raw_score = answer_item.score
                    else:
                        # 새 답변 생성
                        db_answer = Answer(
                            answer_sheet_id=answer_sheet.id,
                            question_id=question.id,
                            answer_text=answer_item.answer_text,
                            raw_score=answer_item.score
                        )
                        db.add(db_answer)
            
            uploaded_sheets.append({
                "student_code": extraction_result.student_code,
                "answers_count": len(extraction_result.answers)
            })
        
        db.commit()
        
        return {
            "message": f"{len(extraction_results)}개의 답안지 정보가 저장되었습니다.",
            "uploaded_sheets": uploaded_sheets
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
            detail=f"답안지 업로드 중 오류가 발생했습니다: {str(e)}"
        )

