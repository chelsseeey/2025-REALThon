from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

class DocumentResponse(BaseModel):
    id: int
    filename: str
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
    llm_analysis_text: Optional[str] = None  # LLM API로 받은 시험지 분석 텍스트

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
    answer_text: Optional[str] = None  # 정답 텍스트

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    answer_text: Optional[str] = None  # 정답 텍스트
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 답안지 관련 스키마
class AnswerSheetBase(BaseModel):
    student_code: str
    sheet_label: Optional[str] = None

class AnswerSheetCreate(AnswerSheetBase):
    pass

class AnswerSheetResponse(AnswerSheetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 답변 관련 스키마
class AnswerBase(BaseModel):
    answer_text: str
    raw_score: Optional[Decimal] = None  # LLM JSON에서 추출한 점수

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
    prompt: Optional[str] = None
    llm_response: Dict[str, Any]  # JSON 응답
    llm_api_type: str = "openai"
    llm_model: Optional[str] = None

class LLMAnalysisResponse(BaseModel):
    id: int
    answer_sheet_id: int
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

# test_parse.py 결과 형식 스키마
class TestParseProblemItem(BaseModel):
    """test_parse.py의 문제 항목"""
    problem_index: int  # 문제 번호
    question_count: int  # 소문항 개수
    score: int  # 배점
    raw_text: str  # 문제 전체 텍스트

class TestParseResult(BaseModel):
    """test_parse.py의 parse_exam 함수 반환 형식"""
    problems: List[TestParseProblemItem]  # 문제 목록
    total_score: int  # 총 배점

class AnswerItem(BaseModel):
    """답변 정보"""
    question_number: int  # 문항 번호
    answer_text: str  # 학생 답안
    score: Optional[Decimal] = None  # 점수

class AnswerExtractionResult(BaseModel):
    """LLM이 추출한 답안지 정보"""
    student_code: str  # 학번/학생 식별자
    answers: List[AnswerItem]  # 문항별 답안 목록

# 정답표 관련 스키마
class AnswerKeyItem(BaseModel):
    """정답표 항목"""
    question_number: int  # 문항 번호
    answer_text: str  # 정답 텍스트

class AnswerKeyResult(BaseModel):
    """정답표 정보 (score.py 형식)"""
    answers: List[AnswerKeyItem]  # 문항별 정답 목록

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

