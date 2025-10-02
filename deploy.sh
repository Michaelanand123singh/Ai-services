#!/bin/bash

# =============================================================================
# BLOOCUBE AI SERVICES - GCP CLOUD RUN DEPLOYMENT SCRIPT
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="bloocube-ai-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
SERVICE_ACCOUNT="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Parse command line arguments
ENVIRONMENT="production"
SKIP_BUILD=false
SKIP_SECRETS=false
FORCE_DEPLOY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --skip-secrets)
      SKIP_SECRETS=true
      shift
      ;;
    --force)
      FORCE_DEPLOY=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --env ENVIRONMENT     Set environment (default: production)"
      echo "  --project PROJECT_ID  Set GCP project ID"
      echo "  --region REGION       Set GCP region (default: us-central1)"
      echo "  --skip-build          Skip Docker image build"
      echo "  --skip-secrets        Skip secrets creation"
      echo "  --force               Force deployment without confirmation"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
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
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    # Check if project is set
    if [[ "$PROJECT_ID" == "your-gcp-project-id" ]]; then
        log_error "Please set your GCP project ID using --project or GOOGLE_CLOUD_PROJECT env var"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_gcp_project() {
    log_info "Setting up GCP project: $PROJECT_ID"
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com \
        secretmanager.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com
    
    log_success "GCP project setup completed"
}

create_service_account() {
    log_info "Creating service account: $SERVICE_ACCOUNT"
    
    # Create service account if it doesn't exist
    if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" &> /dev/null; then
        gcloud iam service-accounts create "$SERVICE_NAME" \
            --display-name="Bloocube AI Service" \
            --description="Service account for Bloocube AI Services"
        
        # Grant necessary roles
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor"
        
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/monitoring.metricWriter"
        
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/logging.logWriter"
        
        log_success "Service account created and configured"
    else
        log_info "Service account already exists"
    fi
}

create_secrets() {
    if [[ "$SKIP_SECRETS" == "true" ]]; then
        log_info "Skipping secrets creation"
        return
    fi
    
    log_info "Creating secrets in Google Secret Manager..."
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        log_warning ".env file not found. Please create it from .env.example"
        log_info "Creating secrets manually. You'll need to update them later."
    fi
    
    # List of secrets to create
    declare -A secrets=(
        ["mongodb-url"]="mongodb://localhost:27017/bloocube"
        ["redis-url"]="redis://localhost:6379/0"
        ["openai-api-key"]="your-openai-api-key"
        ["pinecone-api-key"]="your-pinecone-api-key"
        ["pinecone-environment"]="your-pinecone-environment"
        ["backend-service-url"]="https://your-backend-service.com"
        ["backend-api-key"]="your-backend-api-key"
        ["jwt-secret"]="your-jwt-secret"
        ["twitter-api-key"]="your-twitter-api-key"
        ["twitter-api-secret"]="your-twitter-api-secret"
        ["twitter-bearer-token"]="your-twitter-bearer-token"
        ["youtube-api-key"]="your-youtube-api-key"
        ["facebook-app-id"]="your-facebook-app-id"
        ["facebook-app-secret"]="your-facebook-app-secret"
        ["linkedin-client-id"]="your-linkedin-client-id"
        ["linkedin-client-secret"]="your-linkedin-client-secret"
    )
    
    for secret_name in "${!secrets[@]}"; do
        if ! gcloud secrets describe "bloocube-secrets" --format="value(name)" &> /dev/null; then
            # Create the secret if it doesn't exist
            echo -n "${secrets[$secret_name]}" | gcloud secrets create "$secret_name" --data-file=-
            log_info "Created secret: $secret_name"
        else
            log_info "Secret already exists: $secret_name"
        fi
    done
    
    # Create a combined secret for all values
    if [[ -f ".env" ]]; then
        gcloud secrets create bloocube-secrets --data-file=.env || true
        log_success "Secrets created from .env file"
    fi
}

build_and_push_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_info "Skipping Docker image build"
        return
    fi
    
    log_info "Building Docker image..."
    
    # Build the image
    docker build -t "$IMAGE_NAME:latest" .
    
    # Configure Docker to use gcloud as a credential helper
    gcloud auth configure-docker
    
    # Push the image
    log_info "Pushing image to Google Container Registry..."
    docker push "$IMAGE_NAME:latest"
    
    log_success "Docker image built and pushed successfully"
}

deploy_to_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    # Update the cloudrun.yaml with actual project ID
    sed "s/PROJECT_ID/$PROJECT_ID/g" cloudrun.yaml > cloudrun-deploy.yaml
    
    # Deploy using gcloud
    gcloud run services replace cloudrun-deploy.yaml \
        --region="$REGION" \
        --platform=managed
    
    # Update traffic to 100% for the new revision
    gcloud run services update-traffic "$SERVICE_NAME" \
        --to-latest \
        --region="$REGION"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)")
    
    # Clean up temporary file
    rm -f cloudrun-deploy.yaml
    
    log_success "Deployment completed successfully!"
    log_info "Service URL: $SERVICE_URL"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create uptime check
    gcloud alpha monitoring uptime create \
        --display-name="Bloocube AI Service Health Check" \
        --http-check-path="/health" \
        --http-check-port=443 \
        --http-check-use-ssl \
        --monitored-resource-type="uptime_url" \
        --monitored-resource-labels="host=$SERVICE_URL" \
        --timeout=10s \
        --period=60s \
        --project="$PROJECT_ID" || true
    
    log_success "Monitoring setup completed"
}

run_health_check() {
    log_info "Running health check..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)")
    
    # Wait for service to be ready
    for i in {1..30}; do
        if curl -f "$SERVICE_URL/health" &> /dev/null; then
            log_success "Health check passed!"
            break
        else
            log_info "Waiting for service to be ready... ($i/30)"
            sleep 10
        fi
    done
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    curl -s "$SERVICE_URL/" | jq . || log_warning "Root endpoint test failed"
    curl -s "$SERVICE_URL/docs" &> /dev/null && log_success "API docs accessible" || log_warning "API docs not accessible"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f cloudrun-deploy.yaml
}

main() {
    log_info "🚀 Starting Bloocube AI Services deployment to GCP Cloud Run"
    log_info "Environment: $ENVIRONMENT"
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    
    if [[ "$FORCE_DEPLOY" != "true" ]]; then
        echo -n "Continue with deployment? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run deployment steps
    check_prerequisites
    setup_gcp_project
    create_service_account
    create_secrets
    build_and_push_image
    deploy_to_cloud_run
    setup_monitoring
    run_health_check
    
    log_success "🎉 Deployment completed successfully!"
    log_info "📊 Service URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")"
    log_info "📖 API Documentation: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")/docs"
    log_info "💡 Monitor your service: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
}

# Run main function
main "$@"
