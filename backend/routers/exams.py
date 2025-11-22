from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

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
        exam_date=exam.exam_date
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


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db)
):
    """시험 상세 조회 (인증 없음)"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시험을 찾을 수 없습니다."
        )
    return exam

