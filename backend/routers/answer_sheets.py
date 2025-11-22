from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import json

from models import Exam, AnswerSheet, Answer, Question
from schemas import AnswerExtractionResult
from utils.pdf import save_uploaded_pdf, is_allowed_file
from dependencies import get_db

router = APIRouter(prefix="/answer-sheets", tags=["답안지"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_answer_sheets(
    exam_id: int = Form(...),
    files: List[UploadFile] = File(...),
    extraction_results_json: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    여러개의 답안지 PDF 업로드, 하나씩 LLM 추출 결과(학생별 문항별 답안, 점수) JSON 받아서 Answer에 저장, 완료한 pdf 압축저장 (인증 없음)
    
    - files: 답안지 PDF 파일들 (여러 개)
    - extraction_results_json: LLM 추출 결과들 (JSON 배열 문자열)
    """
    try:
        # 시험 존재 확인
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="시험을 찾을 수 없습니다."
            )
        
        # LLM 추출 결과 파싱
        extraction_results = []
        if extraction_results_json:
            try:
                results_list = json.loads(extraction_results_json)
                extraction_results = [AnswerExtractionResult(**result) for result in results_list]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"LLM 추출 결과 JSON 파싱 실패: {str(e)}"
                )
        
        # 파일과 추출 결과 개수 확인
        if len(extraction_results) != len(files):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF 파일 개수({len(files)})와 추출 결과 개수({len(extraction_results)})가 일치하지 않습니다."
            )
        
        uploaded_sheets = []
        
        # 각 파일 처리
        for idx, file in enumerate(files):
            # 파일 확장자 확인
            if not is_allowed_file(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"파일 '{file.filename}'은 PDF 파일만 업로드 가능합니다."
                )
            
            # PDF 저장 (압축 저장)
            file_info = save_uploaded_pdf(
                file=file,
                user_id=None,
                file_type="answer_sheet"
            )
            
            # 추출 결과 가져오기
            extraction_result = extraction_results[idx] if idx < len(extraction_results) else None
            
            # AnswerSheet 생성 또는 조회
            answer_sheet = db.query(AnswerSheet).filter(
                AnswerSheet.exam_id == exam_id,
                AnswerSheet.student_code == extraction_result.student_code if extraction_result else None
            ).first()
            
            if not answer_sheet:
                # 새 답안지 생성
                answer_sheet = AnswerSheet(
                    exam_id=exam_id,
                    student_code=extraction_result.student_code if extraction_result else f"student_{idx}",
                    answer_pdf_path=file_info["filepath"]
                )
                db.add(answer_sheet)
                db.flush()  # ID를 얻기 위해 flush
            else:
                # 기존 답안지 업데이트
                answer_sheet.answer_pdf_path = file_info["filepath"]
            
            # LLM 추출 결과가 있으면 Answer에 저장
            if extraction_result:
                for answer_item in extraction_result.answers:
                    # 문항 조회
                    question = db.query(Question).filter(
                        Question.exam_id == exam_id,
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
                "student_code": extraction_result.student_code if extraction_result else f"student_{idx}",
                "pdf_path": file_info["filepath"],
                "answers_count": len(extraction_result.answers) if extraction_result else 0
            })
        
        db.commit()
        
        return {
            "message": f"{len(files)}개의 답안지가 업로드되었습니다.",
            "exam_id": exam_id,
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

