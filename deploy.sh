#!/bin/bash

# REALThon 배포 스크립트

set -e

echo "=== REALThon 배포 시작 ==="

# Docker Compose로 서비스 시작
echo "Docker Compose로 서비스 시작 중..."
docker compose down
docker compose build --no-cache
docker compose up -d

# 서비스 상태 확인
echo ""
echo "=== 서비스 상태 ==="
docker compose ps

# 헬스 체크
echo ""
echo "=== 헬스 체크 ==="
sleep 5

# 백엔드 헬스 체크
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ 백엔드 서비스가 정상적으로 실행 중입니다."
else
    echo "✗ 백엔드 서비스에 문제가 있습니다."
    docker compose logs backend
fi

# 데이터베이스 헬스 체크
if docker compose exec -T db pg_isready -U realthon > /dev/null 2>&1; then
    echo "✓ 데이터베이스가 정상적으로 실행 중입니다."
else
    echo "✗ 데이터베이스에 문제가 있습니다."
    docker compose logs db
fi

echo ""
echo "=== 배포 완료 ==="
echo "API 문서: http://$(curl -s ifconfig.me):8000/docs"
echo "API 엔드포인트: http://$(curl -s ifconfig.me):8000"

