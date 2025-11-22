# GCP VM 배포 가이드

이 가이드는 GCP Compute Engine VM에서 REALThon 백엔드와 데이터베이스를 배포하는 방법을 설명합니다.

## 사전 요구사항

- Google Cloud Platform 계정
- `gcloud` CLI 도구 설치 (선택사항)

## 1. GCP VM 인스턴스 생성

### 방법 1: GCP Console 사용

1. [GCP Console](https://console.cloud.google.com/)에 로그인
2. **Compute Engine** > **VM 인스턴스**로 이동
3. **인스턴스 만들기** 클릭
4. 다음 설정을 입력:
   - **이름**: `realthon-vm` (원하는 이름)
   - **지역**: `asia-northeast3` (서울) 또는 원하는 지역
   - **머신 유형**: `e2-medium` (2 vCPU, 4GB RAM) 이상 권장
   - **부팅 디스크**: Ubuntu 22.04 LTS
   - **방화벽**: HTTP 트래픽, HTTPS 트래픽 체크
5. **만들기** 클릭

### 방법 2: gcloud CLI 사용

```bash
gcloud compute instances create realthon-vm \
    --zone=asia-northeast3-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server \
    --boot-disk-size=20GB
```

## 2. 방화벽 규칙 설정

VM 인스턴스에 외부에서 접근할 수 있도록 방화벽 규칙을 설정합니다.

### GCP Console에서 설정

1. **VPC 네트워크** > **방화벽**으로 이동
2. **방화벽 규칙 만들기** 클릭
3. 다음 설정 입력:
   - **이름**: `allow-realthon-api`
   - **방향**: 수신
   - **대상**: 모든 인스턴스 또는 특정 태그
   - **소스 IP 범위**: `0.0.0.0/0` (모든 IP 허용) 또는 특정 IP 범위
   - **프로토콜 및 포트**: TCP, 포트 `8000`
4. **만들기** 클릭

### gcloud CLI로 설정

```bash
gcloud compute firewall-rules create allow-realthon-api \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow REALThon API access"
```

## 3. VM에 SSH 접속

### GCP Console에서

1. VM 인스턴스 목록에서 인스턴스 선택
2. **SSH** 버튼 클릭

### gcloud CLI로

```bash
gcloud compute ssh realthon-vm --zone=asia-northeast3-a
```

### 일반 SSH로

```bash
ssh -i ~/.ssh/gcp_key username@VM_EXTERNAL_IP
```

## 4. 프로젝트 파일 업로드

### 방법 1: Git 사용 (권장)

```bash
# Git 설치
sudo apt-get update
sudo apt-get install -y git

# 프로젝트 클론
git clone <your-repository-url>
cd 2025_REALThon
```

### 방법 2: SCP 사용

로컬 머신에서:

```bash
scp -r ./2025_REALThon username@VM_EXTERNAL_IP:~/
```

### 방법 3: gcloud compute scp 사용

```bash
gcloud compute scp --recurse ./2025_REALThon realthon-vm:~/ --zone=asia-northeast3-a
```

## 5. VM 설정 및 배포

VM에 SSH 접속 후:

```bash
# 프로젝트 디렉토리로 이동
cd ~/2025_REALThon

# 설정 스크립트 실행 권한 부여
chmod +x setup.sh deploy.sh

# 초기 설정 실행 (Docker 설치 등)
./setup.sh

# Docker 그룹 적용 (로그아웃/재로그인 또는)
newgrp docker

# 배포 실행
./deploy.sh
```

## 6. 환경 변수 설정 (선택사항)

프로덕션 환경에서는 보안을 위해 환경 변수를 설정하는 것이 좋습니다.

`.env` 파일 생성:

```bash
cd ~/2025_REALThon
nano .env
```

다음 내용 추가:

```env
DATABASE_URL=postgresql://realthon:강력한비밀번호@db:5432/realthon_db
SECRET_KEY=프로덕션용-강력한-시크릿-키
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`docker-compose.yml`에서 환경 변수 파일 사용하도록 수정:

```yaml
backend:
  env_file:
    - .env
```

## 7. 서비스 확인

### 로컬에서 확인

```bash
# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f

# 백엔드 헬스 체크
curl http://localhost:8000/
```

### 외부에서 확인

브라우저에서 다음 URL 접속:
- API 문서: `http://VM_EXTERNAL_IP:8000/docs`
- API 엔드포인트: `http://VM_EXTERNAL_IP:8000/`

VM의 외부 IP는 GCP Console의 VM 인스턴스 페이지에서 확인할 수 있습니다.

## 8. 자동 시작 설정 (선택사항)

VM 재시작 시 자동으로 서비스가 시작되도록 설정:

```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/realthon.service
```

다음 내용 추가:

```ini
[Unit]
Description=REALThon Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/사용자명/2025_REALThon
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=사용자명
Group=docker

[Install]
WantedBy=multi-user.target
```

서비스 활성화:

```bash
sudo systemctl daemon-reload
sudo systemctl enable realthon.service
sudo systemctl start realthon.service
```

## 9. 모니터링 및 유지보수

### 로그 확인

```bash
# 모든 서비스 로그
docker compose logs -f

# 특정 서비스 로그
docker compose logs -f backend
docker compose logs -f db
```

### 서비스 재시작

```bash
docker compose restart
```

### 서비스 중지

```bash
docker compose down
```

### 데이터베이스 백업

```bash
docker compose exec db pg_dump -U realthon realthon_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 데이터베이스 복원

```bash
docker compose exec -T db psql -U realthon realthon_db < backup_file.sql
```

## 10. 보안 권장사항

1. **강력한 비밀번호 사용**: 데이터베이스 비밀번호와 SECRET_KEY를 강력하게 설정
2. **방화벽 규칙 제한**: 가능하면 특정 IP 범위만 허용
3. **HTTPS 설정**: Nginx나 다른 리버스 프록시를 사용하여 HTTPS 적용
4. **정기 업데이트**: 시스템 및 Docker 이미지 정기 업데이트
5. **백업**: 데이터베이스 정기 백업 설정

## 문제 해결

### 포트가 열리지 않는 경우

```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list

# VM의 방화벽 태그 확인
gcloud compute instances describe realthon-vm --zone=asia-northeast3-a
```

### Docker 권한 오류

```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker
```

### 데이터베이스 연결 오류

```bash
# 데이터베이스 로그 확인
docker compose logs db

# 데이터베이스 컨테이너 접속
docker compose exec db psql -U realthon realthon_db
```

