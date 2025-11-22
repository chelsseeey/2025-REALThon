from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from models import Exam, Question
from schemas import QuestionExtractionResult, QuestionResponse
from utils.pdf import save_uploaded_pdf, is_allowed_file
from dependencies import get_db

router = APIRouter(prefix="/question-papers", tags=["문제지"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_question_paper(
    exam_id: int = Form(...),
    file: UploadFile = File(...),
    extraction_result_json: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    문제지 PDF 업로드 및 압축 저장, LLM 추출 결과(문제, 문항수, 배점) JSON 받아서 Question에 저장 (인증 없음)
    
    - file: 문제지 PDF 파일
    - extraction_result: LLM이 추출한 문제지 정보 (JSON body)
    """
    try:
        # 시험 존재 확인
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="시험을 찾을 수 없습니다."
            )
        
        # 파일 확장자 확인
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF 파일만 업로드 가능합니다."
            )
        
        # PDF 저장 (압축 저장)
        file_info = save_uploaded_pdf(
            file=file,
            user_id=None,
            file_type="question_paper"
        )
        
        # Exam에 PDF 경로 저장
        exam.question_pdf_path = file_info["filepath"]
        db.commit()
        
        # LLM 추출 결과가 있으면 Question에 저장
        questions_created = []
        extraction_result = None
        if extraction_result_json:
            try:
                extraction_result = QuestionExtractionResult(**json.loads(extraction_result_json))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"LLM 추출 결과 JSON 파싱 실패: {str(e)}"
                )
        
        if extraction_result:
            for question_item in extraction_result.questions:
                # 문항 번호 중복 확인
                existing_question = db.query(Question).filter(
                    Question.exam_id == exam_id,
                    Question.number == question_item.number
                ).first()
                
                if existing_question:
                    # 기존 문항 업데이트
                    existing_question.text = question_item.text
                    existing_question.score = question_item.score
                else:
                    # 새 문항 생성
                    db_question = Question(
                        exam_id=exam_id,
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
            "message": "문제지가 업로드되었습니다.",
            "exam_id": exam_id,
            "pdf_path": file_info["filepath"],
            "questions_created": len(questions_created) if extraction_result else 0,
            "total_questions": extraction_result.total_questions if extraction_result else 0
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

