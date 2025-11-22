from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

class DocumentResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    original_filename: str
    file_size: int
    file_type: str
    page_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 시험 관련 스키마
class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    exam_date: Optional[date] = None

class ExamCreate(ExamBase):
    pass

class ExamResponse(ExamBase):
    id: int
    question_pdf_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 문항 관련 스키마
class QuestionBase(BaseModel):
    number: int
    text: str
    score: Decimal

class QuestionCreate(QuestionBase):
    exam_id: int

class QuestionResponse(QuestionBase):
    id: int
    exam_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 답안지 관련 스키마
class AnswerSheetBase(BaseModel):
    student_code: str
    sheet_label: Optional[str] = None

class AnswerSheetCreate(AnswerSheetBase):
    exam_id: int

class AnswerSheetResponse(AnswerSheetBase):
    id: int
    exam_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 답변 관련 스키마
class AnswerBase(BaseModel):
    answer_text: str
    raw_score: Optional[Decimal] = None  # LLM JSON에서 추출한 점수
    max_score: Optional[Decimal] = None  # 최대 점수

class AnswerCreate(AnswerBase):
    answer_sheet_id: int
    question_id: int

class AnswerResponse(AnswerBase):
    id: int
    answer_sheet_id: int
    question_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 문항 패턴 관련 스키마
class QuestionPatternBase(BaseModel):
    total_responses: int
    avg_score: Optional[Decimal] = None
    pattern_json: Dict[str, Any]

class QuestionPatternCreate(QuestionPatternBase):
    question_id: int

class QuestionPatternResponse(QuestionPatternBase):
    id: int
    question_id: int
    computed_at: datetime
    
    class Config:
        from_attributes = True

# LLM 분석 관련 스키마
class LLMAnalysisCreate(BaseModel):
    answer_sheet_id: int
    pdf_path: str
    prompt: Optional[str] = None
    llm_response: Dict[str, Any]  # JSON 응답
    llm_api_type: str = "openai"
    llm_model: Optional[str] = None

class LLMAnalysisResponse(BaseModel):
    id: int
    answer_sheet_id: int
    pdf_path: str
    prompt: Optional[str] = None
    llm_response: Dict[str, Any]
    llm_api_type: str
    llm_model: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# LLM 추출 결과 관련 스키마
class QuestionItem(BaseModel):
    """문항 정보"""
    number: int  # 문항 번호
    text: str  # 문제 내용
    score: Decimal  # 배점

class QuestionExtractionResult(BaseModel):
    """LLM이 추출한 문제지 정보"""
    questions: List[QuestionItem]  # 문제 목록
    total_questions: int  # 문항수

class AnswerItem(BaseModel):
    """답변 정보"""
    question_number: int  # 문항 번호
    answer_text: str  # 학생 답안
    score: Optional[Decimal] = None  # 점수

class AnswerExtractionResult(BaseModel):
    """LLM이 추출한 답안지 정보"""
    student_code: str  # 학번/학생 식별자
    answers: List[AnswerItem]  # 문항별 답안 목록

# 오답 분석 결과 관련 스키마
class AnalysisResultBase(BaseModel):
    analysis_text: str  # LLM이 제공한 문항별 오답 분석 결과 텍스트
    cluster_data: Optional[Dict[str, Any]] = None  # 많이 등장한 답안 클러스터링 결과

class AnalysisResultCreate(AnalysisResultBase):
    question_id: int

class AnalysisResultResponse(AnalysisResultBase):
    id: int
    question_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

