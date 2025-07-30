#!/bin/bash

# Google Cloud 프로젝트 설정
PROJECT_ID="aimovietalk"
REGION="us-central1"
SERVICE_NAME="movie-agent-real-mcp"

echo "🚀 실제 MCP 시스템 Google Cloud Run 배포를 시작합니다..."

# 1. Google Cloud 프로젝트 설정 확인
echo "📋 현재 설정된 프로젝트: $(gcloud config get-value project)"

# 2. 필요한 API 활성화
echo "🔧 필요한 Google Cloud API들을 활성화합니다..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Docker 이미지 빌드 및 Container Registry에 푸시
echo "🏗️  Docker 이미지를 빌드하고 푸시합니다..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# 로컬에서 이미지 빌드
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Container Registry에 푸시
docker push $IMAGE_NAME

# 4. Cloud Run에 배포
echo "☁️  Cloud Run에 배포합니다..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY="$(grep '^OPENAI_API_KEY=' .env | cut -d '=' -f2)" \
  --set-env-vars OPENAI_API_KEY_BACKUP="$(grep '^OPENAI_API_KEY_BACKUP=' .env | cut -d '=' -f2)" \
  --set-env-vars GOOGLE_API_KEY="$(grep '^GOOGLE_API_KEY=' .env | cut -d '=' -f2)" \
  --set-env-vars TAVILY_API_KEY="$(grep '^TAVILY_API_KEY=' .env | cut -d '=' -f2)" \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300

echo "✅ 실제 MCP 시스템 배포가 완료되었습니다!"
echo "🔧 실제 JSON-RPC 2.0 MCP 프로토콜 활성화됨"
echo "🌐 서비스 URL: https://$SERVICE_NAME-$(gcloud config get-value project | tr ':' '-' | tr '.' '-')-$REGION.a.run.app"

# 배포 완료 후 테스트
echo ""
echo "🧪 배포 테스트를 수행합니다..."
SERVICE_URL="https://$SERVICE_NAME-$(gcloud config get-value project | tr ':' '-' | tr '.' '-')-$REGION.a.run.app"

echo "⏳ 서비스 시작 대기 중... (30초)"
sleep 30

echo "🔍 헬스 체크 수행 중..."
if curl -s --max-time 30 "$SERVICE_URL" | grep -q "영화"; then
    echo "✅ 배포 성공! 서비스가 정상적으로 실행 중입니다."
    echo "🎬 실제 MCP 기반 영화 추론 에이전트 준비 완료!"
else
    echo "⚠️ 서비스가 아직 준비되지 않았습니다. 몇 분 후 다시 확인해주세요."
fi