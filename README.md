# 2025-REALThon

답안지와 채점된 문제를 LLM으로 분석하는 백엔드 API 서버

## 기술 스택

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL

## 프로젝트 구조

```
.
├── backend/
│   ├── main.py          # FastAPI 애플리케이션 진입점
│   ├── models.py        # SQLAlchemy 데이터베이스 모델
│   ├── schemas.py       # Pydantic 스키마
│   ├── database.py      # 데이터베이스 연결 설정
│   ├── config.py        # 설정 관리
│   ├── dependencies.py # 공통 의존성
│   ├── requirements.txt # Python 의존성
│   ├── routers/         # API 라우터
│   │   ├── exams.py           # 시험 관리
│   │   ├── question_papers.py # 문제지 관리
│   │   ├── answer_sheets.py   # 답안지 관리
│   │   └── analysis.py        # 오답 분석
│   ├── score.py         # 답안지 점수 파싱 스크립트
│   ├── parse2.py        # 답안지 파싱 스크립트
│   └── test_parse.py    # 문제지 파싱 테스트 스크립트
└── README.md
```

## 시작하기

### 사전 요구사항

- Python 3.11 이상
- PostgreSQL 15 이상

### 설치 및 실행

1. **PostgreSQL 데이터베이스 설정**

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE realthon_db;

# 사용자 생성
CREATE USER realthon WITH PASSWORD 'realthon123';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE realthon_db TO realthon;
\c realthon_db
GRANT ALL ON SCHEMA public TO realthon;
```

2. **프로젝트 설정**

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **의존성 설치**

```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**

프로젝트 루트에 `.env` 파일 생성:

# >>> exit()으로 인터프리터에서 나옵니다.
(venv) $ export DATABASE_URL="postgresql+psycopg://realthon:realthon123@localhost:5432/realthon_db"

# 이후 테이블 생성 코드 재실행
(venv) $ venv/Scripts/python.exe

6. **서버 실행**

```bash
cd backend
venv/Scripts/python.exe -m uvicorn main:app --reload
```

7. **서비스 확인**

- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc

## API 엔드포인트

### 시험 관리 (`/exams`)

- `GET /exams` - 시험 목록 조회
- `GET /exams/current` - 현재 시험 조회 (시험이 하나만 있다고 가정)
- `POST /exams/llm-analysis` - 시험 LLM 분석 텍스트 업데이트

### 문제지 관리 (`/question-papers`)

- `POST /question-papers/upload` - 문제지 LLM 추출 결과 저장
  - `extraction_result_json`: test_parse.py의 결과 JSON
- `POST /question-papers/answer-key` - 정답표 저장
  - `answer_key_json`: 정답표 JSON

### 답안지 관리 (`/answer-sheets`)

- `POST /answer-sheets/upload` - 답안지 LLM 추출 결과 저장
  - `extraction_results_json`: LLM 추출 결과들 (JSON 배열 문자열)

### 오답 분석 (`/analysis`)

- `POST /analysis/exams/{question_id}/analyze` - 문항별 오답 분석 실행
  - `question_id`: 문항 ID
  - `analysis_text`: LLM 분석 결과 텍스트
  - `cluster_data_json`: 클러스터링 결과 (선택사항)
- `GET /analysis/questions/{question_id}/report` - 문항별 분석 리포트 조회

## 환경 변수

`.env` 파일에서 다음 환경 변수를 설정할 수 있습니다:

- `DATABASE_URL`: PostgreSQL 연결 URL (필수)

## 데이터베이스

기본 설정:
- 사용자: `realthon`
- 비밀번호: `realthon123`
- 데이터베이스: `realthon_db`
- 포트: `5432`

## 스크립트

### `score.py`
답안지 이미지(PNG)에서 학번과 점수를 추출하여 DB에 저장하는 스크립트

```bash
python score.py
```

### `parse2.py`
답안지 이미지를 LLM으로 파싱하여 JSON 결과를 반환하는 스크립트

### `test_parse.py`
문제지 이미지를 LLM으로 파싱하여 문제 정보를 추출하는 스크립트
