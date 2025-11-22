# 2025-REALThon

답안지와 채점된 문제를 LLM으로 분석하는 백엔드 API 서버

## 기술 스택

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Container**: Docker & Docker Compose
- **Authentication**: JWT (JSON Web Token)

## 프로젝트 구조

```
.
├── backend/
│   ├── main.py          # FastAPI 애플리케이션 진입점
│   ├── models.py        # SQLAlchemy 데이터베이스 모델
│   ├── schemas.py       # Pydantic 스키마
│   ├── database.py      # 데이터베이스 연결 설정
│   ├── auth.py          # 인증 관련 유틸리티
│   ├── config.py        # 설정 관리
│   ├── requirements.txt # Python 의존성
│   └── Dockerfile       # 백엔드 Docker 이미지
├── docker-compose.yml   # Docker Compose 설정
└── README.md
```

## 시작하기

### 사전 요구사항

- Docker
- Docker Compose

### 설치 및 실행

1. 프로젝트 클론 또는 다운로드

2. Docker Compose로 서비스 시작:
```bash
docker-compose up -d
```

3. 서비스 확인:
   - 백엔드 API: http://localhost:8000
   - API 문서: http://localhost:8000/docs
   - 대체 문서: http://localhost:8000/redoc

4. 서비스 중지:
```bash
docker-compose down
```

5. 볼륨까지 삭제 (데이터베이스 데이터 포함):
```bash
docker-compose down -v
```

## API 엔드포인트

### 인증

- `POST /register` - 회원가입
  - Request Body:
    ```json
    {
      "email": "user@example.com",
      "username": "사용자명",
      "password": "비밀번호"
    }
    ```

- `POST /token` - 로그인 (토큰 발급)
  - Form Data:
    - `username`: 이메일
    - `password`: 비밀번호
  - Response:
    ```json
    {
      "access_token": "jwt_token_here",
      "token_type": "bearer"
    }
    ```

- `GET /users/me` - 현재 사용자 정보 조회
  - Headers: `Authorization: Bearer {token}`

## 환경 변수

`docker-compose.yml`에서 다음 환경 변수를 설정할 수 있습니다:

- `DATABASE_URL`: PostgreSQL 연결 URL
- `SECRET_KEY`: JWT 토큰 서명에 사용할 비밀키 (프로덕션에서는 반드시 변경)
- `ALGORITHM`: JWT 알고리즘 (기본값: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 토큰 만료 시간 (기본값: 30분)

## 데이터베이스

PostgreSQL 데이터베이스는 Docker 컨테이너로 실행되며, 데이터는 `postgres_data` 볼륨에 저장됩니다.

기본 설정:
- 사용자: `realthon`
- 비밀번호: `realthon123`
- 데이터베이스: `realthon_db`
- 포트: `5432`

## 개발

### 로컬 개발 환경 설정

1. Python 3.11 이상 설치
2. 가상 환경 생성 및 활성화:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정 (선택사항):
```bash
export DATABASE_URL="postgresql://realthon:realthon123@localhost:5432/realthon_db"
export SECRET_KEY="your-secret-key"
```

5. 서버 실행:
```bash
uvicorn main:app --reload
```

## GCP VM 배포

GCP Compute Engine VM에서 앱과 데이터베이스를 실행하는 방법은 [GCP_DEPLOY.md](./GCP_DEPLOY.md)를 참조하세요.

### 빠른 시작

1. GCP VM 인스턴스 생성
2. 프로젝트 파일 업로드
3. 설정 스크립트 실행:
```bash
chmod +x setup.sh deploy.sh
./setup.sh
./deploy.sh
```

자세한 내용은 [GCP_DEPLOY.md](./GCP_DEPLOY.md)를 확인하세요.

## 다음 단계

- [ ] 답안지 업로드 기능
- [ ] 채점 결과 업로드 기능
- [ ] LLM 분석 API 통합
- [ ] 분석 결과 저장 및 조회
