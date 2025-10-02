#!/bin/bash

# =============================================================================
# BLOOCUBE AI SERVICES - GCP SETUP SCRIPT
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="${1:-your-gcp-project-id}"
REGION="${2:-us-central1}"
SERVICE_NAME="bloocube-ai-service"

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

if [[ "$PROJECT_ID" == "your-gcp-project-id" ]]; then
    log_error "Please provide your GCP project ID as the first argument"
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    exit 1
fi

log_info "🚀 Setting up GCP resources for Bloocube AI Services"
log_info "Project: $PROJECT_ID"
log_info "Region: $REGION"

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
    logging.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com

log_success "APIs enabled successfully"

# Create service account
SERVICE_ACCOUNT="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
log_info "Creating service account: $SERVICE_ACCOUNT"

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
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/cloudsql.client"
    
    log_success "Service account created and configured"
else
    log_info "Service account already exists"
fi

# Create secrets
log_info "Creating secrets in Google Secret Manager..."

# Function to create secret if it doesn't exist
create_secret() {
    local secret_name="$1"
    local secret_value="$2"
    
    if ! gcloud secrets describe "$secret_name" &> /dev/null; then
        echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
        log_info "Created secret: $secret_name"
    else
        log_info "Secret already exists: $secret_name"
    fi
}

# Create individual secrets
create_secret "mongodb-url" "mongodb://your-mongodb-connection-string"
create_secret "redis-url" "redis://your-redis-connection-string"
create_secret "openai-api-key" "your-openai-api-key"
create_secret "pinecone-api-key" "your-pinecone-api-key"
create_secret "pinecone-environment" "your-pinecone-environment"
create_secret "backend-service-url" "https://your-backend-service.com"
create_secret "backend-api-key" "your-backend-api-key"
create_secret "jwt-secret" "your-jwt-secret-must-match-backend"
create_secret "twitter-api-key" "your-twitter-api-key"
create_secret "twitter-api-secret" "your-twitter-api-secret"
create_secret "twitter-bearer-token" "your-twitter-bearer-token"
create_secret "youtube-api-key" "your-youtube-api-key"
create_secret "facebook-app-id" "your-facebook-app-id"
create_secret "facebook-app-secret" "your-facebook-app-secret"
create_secret "linkedin-client-id" "your-linkedin-client-id"
create_secret "linkedin-client-secret" "your-linkedin-client-secret"

log_success "Secrets created successfully"

# Create Cloud Storage bucket for data storage
BUCKET_NAME="${PROJECT_ID}-ai-service-data"
log_info "Creating Cloud Storage bucket: $BUCKET_NAME"

if ! gsutil ls -b gs://"$BUCKET_NAME" &> /dev/null; then
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" gs://"$BUCKET_NAME"
    
    # Set bucket permissions
    gsutil iam ch serviceAccount:"$SERVICE_ACCOUNT":objectAdmin gs://"$BUCKET_NAME"
    
    log_success "Cloud Storage bucket created"
else
    log_info "Cloud Storage bucket already exists"
fi

# Create Cloud SQL instance (optional, for PostgreSQL)
INSTANCE_NAME="${SERVICE_NAME}-db"
log_info "Creating Cloud SQL instance: $INSTANCE_NAME"

if ! gcloud sql instances describe "$INSTANCE_NAME" &> /dev/null; then
    gcloud sql instances create "$INSTANCE_NAME" \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --enable-bin-log \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --maintenance-release-channel=production
    
    # Create database
    gcloud sql databases create bloocube_ai --instance="$INSTANCE_NAME"
    
    # Create user
    gcloud sql users create aiservice \
        --instance="$INSTANCE_NAME" \
        --password="$(openssl rand -base64 32)"
    
    log_success "Cloud SQL instance created"
else
    log_info "Cloud SQL instance already exists"
fi

# Create Memorystore Redis instance (optional)
REDIS_INSTANCE_NAME="${SERVICE_NAME}-redis"
log_info "Creating Memorystore Redis instance: $REDIS_INSTANCE_NAME"

if ! gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" &> /dev/null; then
    gcloud redis instances create "$REDIS_INSTANCE_NAME" \
        --size=1 \
        --region="$REGION" \
        --redis-version=redis_6_x \
        --tier=basic
    
    log_success "Memorystore Redis instance created"
else
    log_info "Memorystore Redis instance already exists"
fi

# Set up monitoring
log_info "Setting up monitoring and alerting..."

# Create notification channel (email)
NOTIFICATION_CHANNEL=$(gcloud alpha monitoring channels create \
    --display-name="Bloocube AI Service Alerts" \
    --type=email \
    --channel-labels=email_address=your-email@example.com \
    --format="value(name)")

log_info "Notification channel created: $NOTIFICATION_CHANNEL"

# Create alerting policy
cat > alert-policy.json << EOF
{
  "displayName": "AI Service High Error Rate",
  "conditions": [
    {
      "displayName": "High error rate",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.1,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_MEAN",
            "groupByFields": ["resource.label.service_name"]
          }
        ]
      }
    }
  ],
  "notificationChannels": ["$NOTIFICATION_CHANNEL"],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=alert-policy.json
rm alert-policy.json

log_success "Monitoring and alerting configured"

# Create VPC connector (if needed for private resources)
CONNECTOR_NAME="${SERVICE_NAME}-connector"
log_info "Creating VPC connector: $CONNECTOR_NAME"

if ! gcloud compute networks vpc-access connectors describe "$CONNECTOR_NAME" --region="$REGION" &> /dev/null; then
    gcloud compute networks vpc-access connectors create "$CONNECTOR_NAME" \
        --region="$REGION" \
        --subnet=default \
        --subnet-project="$PROJECT_ID" \
        --min-instances=2 \
        --max-instances=10
    
    log_success "VPC connector created"
else
    log_info "VPC connector already exists"
fi

# Output summary
log_success "🎉 GCP setup completed successfully!"
echo ""
log_info "📋 Summary of created resources:"
echo "  • Service Account: $SERVICE_ACCOUNT"
echo "  • Cloud Storage Bucket: gs://$BUCKET_NAME"
echo "  • Cloud SQL Instance: $INSTANCE_NAME"
echo "  • Redis Instance: $REDIS_INSTANCE_NAME"
echo "  • VPC Connector: $CONNECTOR_NAME"
echo "  • Secrets: Created in Secret Manager"
echo "  • Monitoring: Configured with alerts"
echo ""
log_info "📝 Next steps:"
echo "  1. Update the secrets with your actual API keys and credentials"
echo "  2. Update the cloudrun.yaml file with your project ID"
echo "  3. Run the deployment script: ./deploy.sh --project $PROJECT_ID"
echo ""
log_warning "⚠️  Don't forget to update the placeholder values in Secret Manager!"

# Create a summary file
cat > gcp-setup-summary.txt << EOF
GCP Setup Summary for Bloocube AI Services
==========================================

Project ID: $PROJECT_ID
Region: $REGION
Service Name: $SERVICE_NAME

Created Resources:
- Service Account: $SERVICE_ACCOUNT
- Cloud Storage Bucket: gs://$BUCKET_NAME
- Cloud SQL Instance: $INSTANCE_NAME
- Redis Instance: $REDIS_INSTANCE_NAME
- VPC Connector: $CONNECTOR_NAME

Secrets Created in Secret Manager:
- mongodb-url
- redis-url
- openai-api-key
- pinecone-api-key
- pinecone-environment
- backend-service-url
- backend-api-key
- jwt-secret
- twitter-api-key
- twitter-api-secret
- twitter-bearer-token
- youtube-api-key
- facebook-app-id
- facebook-app-secret
- linkedin-client-id
- linkedin-client-secret

Next Steps:
1. Update secrets with actual values
2. Deploy the service using ./deploy.sh
3. Configure monitoring dashboards
4. Set up CI/CD pipeline

Generated on: $(date)
EOF

log_info "Setup summary saved to: gcp-setup-summary.txt"
