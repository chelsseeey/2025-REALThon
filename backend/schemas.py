from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

class UserBase(BaseModel):
    user_id: str
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    password: str  # 해시된 비밀번호 포함
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

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
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 문항 관련 스키마
class QuestionBase(BaseModel):
    number: int
    text: str
    score: Decimal
    chapter_label: Optional[str] = None
    topic_tags: Optional[str] = None
    rubric_text: Optional[str] = None
    model_answer: Optional[str] = None

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
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 답변 관련 스키마
class AnswerBase(BaseModel):
    answer_text: str
    raw_score: Optional[Decimal] = None
    max_score: Optional[Decimal] = None
    is_correct: Optional[bool] = None
    grading_status: Optional[str] = None

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

