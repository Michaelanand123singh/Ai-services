#!/bin/bash
# =============================================================================
# BLOOCUBE AI SERVICES - DEPLOYMENT SCRIPT
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-asia-southeast1}"
SERVICE_NAME="ai-services"
REPO_NAME="bloocube"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if PROJECT_ID is set
    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID environment variable is not set."
        exit 1
    fi
    
    log_success "All requirements met"
}

authenticate_gcp() {
    log_info "Authenticating with GCP..."
    
    # Check if already authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_success "Already authenticated with GCP"
    else
        log_info "Please authenticate with GCP..."
        gcloud auth login
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    log_success "Project set to $PROJECT_ID"
}

configure_docker() {
    log_info "Configuring Docker for GCR..."
    gcloud auth configure-docker "${REGION}-docker.pkg.dev"
    log_success "Docker configured for GCR"
}

build_image() {
    log_info "Building Docker image..."
    
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"
    
    docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --progress=plain \
        -t "$image_name" \
        -t "${image_name}:$(git rev-parse --short HEAD)" \
        .
    
    log_success "Docker image built successfully"
}

push_image() {
    log_info "Pushing Docker image to registry..."
    
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"
    
    docker push "$image_name"
    docker push "${image_name}:$(git rev-parse --short HEAD)"
    
    log_success "Docker image pushed successfully"
}

deploy_service() {
    log_info "Deploying to Cloud Run..."
    
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"
    
    gcloud run deploy "$SERVICE_NAME" \
        --image "$image_name" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --cpu 4 \
        --memory 8Gi \
        --timeout 900 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --port 8080 \
        --set-env-vars NODE_ENV=production,ENVIRONMENT=production,LOG_LEVEL=info,AI_SERVICE_NAME=bloocube-ai-service,AI_SERVICE_VERSION=1.0.0,UVICORN_WORKERS=1
    
    log_success "Service deployed successfully"
}

health_check() {
    log_info "Performing health check..."
    
    # Wait for service to be ready
    sleep 30
    
    # Get service URL
    local service_url=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    log_info "Service URL: $service_url"
    
    # Test endpoints
    local endpoints=("ping" "test" "/" "health" "docs")
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing $endpoint endpoint..."
        if curl -f -s --max-time 30 "${service_url}/${endpoint#/}"; then
            log_success "$endpoint endpoint working"
        else
            log_warning "$endpoint endpoint failed"
        fi
    done
    
    log_success "Health check completed"
}

main() {
    log_info "Starting Bloocube AI Services deployment..."
    echo "=================================================="
    
    check_requirements
    authenticate_gcp
    configure_docker
    build_image
    push_image
    deploy_service
    health_check
    
    echo "=================================================="
    log_success "Deployment completed successfully!"
    
    # Get final service URL
    local service_url=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    echo ""
    log_info "🌐 Service URL: $service_url"
    log_info "📚 API Documentation: $service_url/docs"
    log_info "🔍 Health Check: $service_url/health"
    echo ""
}

# Run main function
main "$@"