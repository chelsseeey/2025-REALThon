from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, JSONB, Numeric, Boolean, Date, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # 사용자 ID (고유 식별자)
    password = Column(String, nullable=False)  # 해시된 비밀번호 (hashed_password 대신 password로 명명)
    
    # 관계
    documents = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_type = Column(String, nullable=False, default="pdf")  # pdf, answer_sheet, graded_paper 등
    page_count = Column(Integer, nullable=True)  # PDF 페이지 수
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    owner = relationship("User", back_populates="documents")


class Exam(Base):
    __tablename__ = "exam"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # 시험 이름 (예: 2025-1 중간고사)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    
    # 관계
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    answer_sheets = relationship("AnswerSheet", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "question"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)  # 시험지 상 문항 번호 (1,2,3,...)
    text = Column(Text, nullable=False)  # 문항 지문
    score = Column(Numeric(5, 2), nullable=False)  # 배점 (예: 5.0점)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('exam_id', 'number', name='uq_question_exam_number'),
    )
    
    # 관계
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    question_pattern = relationship("QuestionPattern", back_populates="question", uselist=False, cascade="all, delete-orphan")


class AnswerSheet(Base):
    __tablename__ = "answer_sheet"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id", ondelete="CASCADE"), nullable=False)
    student_code = Column(String(100), nullable=False)  # 학번/학생 식별자 (로그인 계정 아님)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 관계
    exam = relationship("Exam", back_populates="answer_sheets")
    answers = relationship("Answer", back_populates="answer_sheet", cascade="all, delete-orphan")
    llm_analyses = relationship("LLMAnalysis", back_populates="answer_sheet", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answer"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_sheet_id = Column(Integer, ForeignKey("answer_sheet.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    
    # 학생이 실제로 작성한 서술형 답변
    answer_text = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('answer_sheet_id', 'question_id', name='uq_answer_sheet_question'),
    )
    
    # 관계
    answer_sheet = relationship("AnswerSheet", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class QuestionPattern(Base):
    __tablename__ = "question_pattern"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_responses = Column(Integer, nullable=False)  # 해당 문항에 답변한 총 인원 수
    avg_score = Column(Numeric(5, 2), nullable=True)  # 서술형 채점이 되어있다면 평균 점수
    computed_at = Column(DateTime(timezone=True), nullable=False)  # 분석/계산 시점
    pattern_json = Column(JSON, nullable=False)  # 실제 "패턴"을 JSON으로 저장
    
    # 관계
    question = relationship("Question", back_populates="question_pattern")


class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_sheet_id = Column(Integer, ForeignKey("answer_sheet.id", ondelete="CASCADE"), nullable=False)
    pdf_path = Column(String, nullable=False)  # 분석한 PDF 경로
    prompt = Column(Text, nullable=True)  # LLM에 보낸 프롬프트
    llm_response = Column(JSON, nullable=False)  # LLM 응답 (JSON)
    llm_api_type = Column(String, nullable=False, default="openai")  # 사용한 LLM API 타입
    llm_model = Column(String, nullable=True)  # 사용한 모델명
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    answer_sheet = relationship("AnswerSheet", back_populates="llm_analyses")

