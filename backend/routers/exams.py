from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from models import Exam
from schemas import ExamCreate, ExamResponse
from dependencies import get_db

router = APIRouter(prefix="/exams", tags=["시험"])


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam: ExamCreate,
    db: Session = Depends(get_db)
):
    """시험 생성 (인증 없음)"""
    db_exam = Exam(
        title=exam.title,
        description=exam.description,
        exam_date=exam.exam_date,
        llm_analysis_text=exam.llm_analysis_text
    )
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


@router.get("", response_model=List[ExamResponse])
async def get_exams(
    db: Session = Depends(get_db)
):
    """시험 목록 조회 (인증 없음)"""
    exams = db.query(Exam).all()
    return exams


@router.get("/current", response_model=ExamResponse)
async def get_current_exam(
    db: Session = Depends(get_db)
):
    """현재 시험 조회 (시험이 하나만 있다고 가정) (인증 없음)"""
    exam = db.query(Exam).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시험이 없습니다."
        )
    return exam


@router.post("/llm-analysis", response_model=ExamResponse)
async def update_exam_llm_analysis(
    llm_analysis_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    시험지 LLM 분석 텍스트 업데이트 (시험이 하나만 있다고 가정) (인증 없음)
    
    - llm_analysis_text: LLM API로 받은 시험지 분석 텍스트
    """
    exam = db.query(Exam).first()
    if not exam:
        # 시험이 없으면 생성
        exam = Exam(title="기본 시험")
        db.add(exam)
        db.flush()
    
    exam.llm_analysis_text = llm_analysis_text
    db.commit()
    db.refresh(exam)
    return exam

