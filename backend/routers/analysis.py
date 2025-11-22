from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from decimal import Decimal

from models import Question, Answer, AnswerSheet, AnalysisResult
from schemas import AnalysisResultCreate, AnalysisResultResponse
from dependencies import get_db

router = APIRouter(prefix="/analysis", tags=["오답 분석"])


@router.post("/exams/{question_id}/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_wrong_answers(
    question_id: int,
    analysis_text: str = Form(...),
    cluster_data_json: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    문항별 전체 학생 answer중 raw_score가 question.score(배점)보다 낮은 answer 분석 실행 (LLM 분석 결과 텍스트 저장) (인증 없음)
    
    - question_id: 문항 ID
    - analysis_text: LLM이 제공한 문항별 오답 분석 결과 텍스트
    - cluster_data_json: 많이 등장한 답안 클러스터링 결과 (JSON 문자열, 선택사항)
    """
    try:
        # 문항 존재 확인
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문항을 찾을 수 없습니다."
            )
        
        # 클러스터 데이터 파싱
        cluster_data = None
        if cluster_data_json:
            try:
                import json
                cluster_data = json.loads(cluster_data_json)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"클러스터 데이터 JSON 파싱 실패: {str(e)}"
                )
        
        # 기존 분석 결과 확인
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.question_id == question_id
        ).first()
        
        if existing_result:
            # 기존 결과 업데이트
            existing_result.analysis_text = analysis_text
            existing_result.cluster_data = cluster_data
            db.commit()
            db.refresh(existing_result)
            return existing_result
        else:
            # 새 분석 결과 생성
            db_result = AnalysisResult(
                question_id=question_id,
                analysis_text=analysis_text,
                cluster_data=cluster_data
            )
            db.add(db_result)
            db.commit()
            db.refresh(db_result)
            return db_result
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오답 분석 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/questions/{question_id}/report")
async def get_question_analysis_report(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    문항별 답안 분석 결과, 문항별 정답률 조회 (인증 없음)
    """
    try:
        # 문항 존재 확인
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문항을 찾을 수 없습니다."
            )
        
        # 해당 문항의 모든 답변 조회
        answers = db.query(Answer).filter(Answer.question_id == question_id).all()
        
        # 통계 계산
        total_answers = len(answers)
        correct_answers = 0
        wrong_answers = []
        
        for answer in answers:
            # raw_score가 question.score와 같거나 큰 경우 정답으로 간주
            if answer.raw_score is not None:
                if answer.raw_score >= question.score:
                    correct_answers += 1
                else:
                    wrong_answers.append({
                        "answer_id": answer.id,
                        "student_code": answer.answer_sheet.student_code,
                        "answer_text": answer.answer_text,
                        "score": float(answer.raw_score) if answer.raw_score else None,
                        "max_score": float(question.score)
                    })
            else:
                # 점수가 없는 경우 오답으로 간주
                wrong_answers.append({
                    "answer_id": answer.id,
                    "student_code": answer.answer_sheet.student_code,
                    "answer_text": answer.answer_text,
                    "score": None,
                    "max_score": float(question.score)
                })
        
        # 정답률 계산
        correct_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        # 분석 결과 조회
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.question_id == question_id
        ).first()
        
        return {
            "question_id": question_id,
            "question_number": question.number,
            "question_text": question.text,
            "max_score": float(question.score),
            "statistics": {
                "total_answers": total_answers,
                "correct_answers": correct_answers,
                "wrong_answers": len(wrong_answers),
                "correct_rate": round(correct_rate, 2)
            },
            "wrong_answers": wrong_answers,
            "analysis_result": {
                "analysis_text": analysis_result.analysis_text if analysis_result else None,
                "cluster_data": analysis_result.cluster_data if analysis_result else None
            } if analysis_result else None
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 리포트 조회 중 오류가 발생했습니다: {str(e)}"
        )

