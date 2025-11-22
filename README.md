# 2025-REALThon

# 2025-REALThon

간단한 설명
---
2025-REALThon은 HTML, JavaScript, CSS로 구성된 웹 프로젝트입니다. 이 리포지토리는 프론트엔드 중심의 인터랙티브 웹 페이지를 포함하고 있으며 데모, UI/UX 인터랙션, 또는 실습용 웹 애플리케이션으로 사용될 수 있습니다.

주요 특징
---
- 순수 HTML/CSS/JavaScript 기반으로 작동
- 빠른 로컬 실행(정적 파일)
- 확장 및 커스터마이징이 쉬운 구조

프로젝트 구조(예시)
---
- index.html — 진입점(메인 페이지)
- assets/ 또는 static/ — 이미지, 폰트, 기타 정적 자원
- css/ — 스타일시트 파일
- js/ — 자바스크립트 파일

기술 스택
---
- HTML — 49.1%
- JavaScript — 44.8%
- CSS — 6.1%

요구사항(Prerequisites)
---
- 현대적인 웹 브라우저(Chrome, Firefox, Edge 등)
- (선택) 로컬 간단 서버: Node.js의 http-server, Python의 SimpleHTTPServer 등

로컬에서 실행하기
---
방법 A — 브라우저에서 직접 열기
1. 리포지토리를 클론하거나 ZIP을 내려받습니다.
2. 프로젝트 루트의 `index.html` 파일을 더블클릭하여 브라우저로 엽니다.

방법 B — 간단한 로컬 서버 사용 (권장)
- Node.js(http-server 사용)
  1. 전역 설치: `npm install -g http-server`
  2. 프로젝트 루트에서: `http-server .`
  3. 표시된 URL(예: http://127.0.0.1:8080)로 접속

- Python (3.x)
  1. 프로젝트 루트에서: `python -m http.server 8000`
  2. 브라우저에서 `http://localhost:8000` 접속

개발 가이드
---
- 자바스크립트 또는 스타일을 수정한 뒤 브라우저에서 새로고침하여 변경사항 확인
- 빌드 스크립트가 있는 경우(현재 없음) 해당 스크립트에 따라 빌드 및 배포

컨트리뷰션
---
기여 환영합니다. 기여 방법:
1. 이슈(issue)를 생성해 변경하고자 하는 내용이나 버그를 알려주세요.
2. 새 브랜치를 만들어 작업하세요. (예: `feature/my-feature`)
3. 변경사항 커밋 후 풀 리퀘스트(PR)를 생성하세요.

라이선스
---
특정 라이선스가 명시되어 있지 않다면, 기본적으로 기여 전에 라이선스를 명시해 주세요. (예: MIT, Apache-2.0 등)

문의 및 연락처
---
문제가 있거나 궁금한 점이 있으면 GitHub 리포지토리의 Issue를 통해 문의해 주세요: https://github.com/chelsseeey/2025-REALThon/issues

---

README 수정이나 추가 섹션(예: 사용법 데모, 스크린샷, 배포 가이드)을 원하시면 어떤 내용을 넣을지 알려주시면 반영해 드리겠습니다.

# 2025-REALThon Backend

시험 문제/답안 업로드 후 LLM(OpenAI) 기반 분석을 목표로 하는 FastAPI 백엔드 

## 현재 구현 상태 (실제 코드 기준)

### DB / ORM
- SQLite 사용 (config.py > database_url 기본값 추정)
- SQLAlchemy Base / engine 정의 (database.py)
- 세션 DI: dependencies.py get_db()
- 마이그레이션 없음 (Alembic 미사용)
- models.py에 일부 클래스 미완성:
  - Document, Question, AnswerSheet 정의됨
  

### 라우터 (routers/)
| 파일 | 주요 기능 | 구현 상태 |
|------|----------|----------|
| exams.py | 시험 생성(Create) / 단일 조회(Get) | 동작 가능 (파일 저장+Document 생성) |
| question_papers.py | 문제지 추출 JSON 저장 / 정답표 저장 |
| answer_sheets.py | 답안지 PDF 업로드 → LLM 분석 후 Answer/LLMAnalysis 저장 | LLM 호출·파싱 로직 존재. Answer/LLMAnalysis 모델 미구현으로 실제 저장 실패 |
| analysis.py | 문항별 패턴 분석 / 결과 생성·조회 | 

### 유틸
- utils/image.py: PDF 전체를 단일 base64 이미지로 취급(실제 Vision 전용 아님), 간소화된 텍스트 추출
- parse2.py / score.py / test_parse.py: LLM 활용 시험/점수 처리 스크립트 (직접 실행용, API 연결 미흡)

### 스키마 (schemas.py)
- Pydantic 모델 일부 정의(ExamResponse 등). 

### 기타
- .env 존재(내용 미확인). config.py에서 로드.
- requirements.txt에 FastAPI, SQLAlchemy, OpenAI 등 포함. pdf2image/Pillow 포함 (Poppler 필요).
- Dockerfile 존재. docker-compose 없음.


## 실행 방법

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Poppler(Windows):
```powershell
choco install poppler
```

접속:
- 문서: http://localhost:8000/docs

## 필요 수정 (우선순위)

1. models.py: Answer, QuestionPattern, LLMAnalysis, AnalysisResult 컬럼/관계 구현
2. question_papers.py / answer-key: JSON 파싱 및 저장 로직 작성 (json import 추가)
3. analysis.py: 모델 컬럼 존재 후 재검증
4. answer_sheets.py: 모델 완성 후 Answer / LLMAnalysis 정상 저장 확인
5. 초기 DB 테이블 생성 코드(main.py startup) 추가
6. 에러/무결성 검증(중복 문항, 정답 누락, JSON 형식) 강화
7. 단일 시험 자동 생성(Exam 없을 때)
