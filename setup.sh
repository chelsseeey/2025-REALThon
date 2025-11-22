#!/bin/bash

# REALThon GCP VM 설정 스크립트

set -e

echo "=== REALThon GCP VM 설정 시작 ==="

# 시스템 업데이트
echo "시스템 패키지 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# Docker 설치
if ! command -v docker &> /dev/null; then
    echo "Docker 설치 중..."
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
    
    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    echo "Docker 설치 완료. 로그아웃 후 다시 로그인하거나 'newgrp docker'를 실행하세요."
else
    echo "Docker가 이미 설치되어 있습니다."
fi

# Docker Compose 설치 확인
if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose 설치 중..."
    # Docker Compose는 docker-compose-plugin에 포함되어 있음
    sudo apt-get install -y docker-compose-plugin
else
    echo "Docker Compose가 이미 설치되어 있습니다."
fi

# 프로젝트 디렉토리 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "오류: docker-compose.yml 파일을 찾을 수 없습니다."
    exit 1
fi

echo "=== 설정 완료 ==="
echo ""
echo "다음 명령어로 서비스를 시작하세요:"
echo "  docker compose up -d"
echo ""
echo "서비스 상태 확인:"
echo "  docker compose ps"
echo ""
echo "로그 확인:"
echo "  docker compose logs -f"

