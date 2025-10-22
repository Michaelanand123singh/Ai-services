# 🚀 Bloocube AI Services - Deployment Guide

This guide provides comprehensive instructions for deploying the Bloocube AI Services to Google Cloud Platform (GCP) Cloud Run.

## 📋 Prerequisites

### Required Tools
- **Google Cloud SDK** (`gcloud`) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- **Docker** - [Install Guide](https://docs.docker.com/get-docker/)
- **Git** - [Install Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Required GCP Resources
- **Google Cloud Project** with billing enabled
- **Artifact Registry** repository for Docker images
- **Cloud Run** service
- **Service Account** with necessary permissions

### Required Environment Variables
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-southeast1"  # Optional, defaults to asia-southeast1
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  Cloud Build     │───▶│   Cloud Run     │
│                 │    │                  │    │                 │
│ AI-services/    │    │ - Build Image    │    │ - FastAPI App   │
│ - src/          │    │ - Run Tests      │    │ - AI Services   │
│ - Dockerfile    │    │ - Deploy         │    │ - Health Checks │
│ - cloudbuild.yaml│   │ - Health Check   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Deployment Methods

### Method 1: GitHub Actions (Recommended)

#### 1.1 Setup GitHub Secrets
Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

```
GCP_PROJECT_ID: your-gcp-project-id
GCP_SA_KEY: your-service-account-key-json
GCP_REGION: asia-southeast1 (optional)
```

#### 1.2 Create Service Account
```bash
# Create service account
gcloud iam service-accounts create bloocube-ai-deploy \
    --display-name="Bloocube AI Deploy" \
    --description="Service account for AI services deployment"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:bloocube-ai-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:bloocube-ai-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:bloocube-ai-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

# Create and download key
gcloud iam service-accounts keys create bloocube-ai-key.json \
    --iam-account=bloocube-ai-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

#### 1.3 Deploy
Simply push to the `main` branch:
```bash
git add .
git commit -m "Deploy AI services"
git push origin main
```

### Method 2: Cloud Build (Manual)

#### 2.1 Setup Artifact Registry
```bash
# Create repository
gcloud artifacts repositories create bloocube \
    --repository-format=docker \
    --location=asia-southeast1 \
    --description="Bloocube Docker repository"
```

#### 2.2 Trigger Build
```bash
# Submit build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions=_REGION=asia-southeast1,_SERVICE=ai-services,_REPO=bloocube
```

### Method 3: Local Deployment

#### 3.1 Using PowerShell (Windows)
```powershell
# Set environment variables
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_REGION = "asia-southeast1"

# Run deployment script
.\deploy.ps1
```

#### 3.2 Using Bash (Linux/Mac)
```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-southeast1"

# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NODE_ENV` | Environment | `production` | No |
| `LOG_LEVEL` | Logging level | `info` | No |
| `AI_SERVICE_NAME` | Service name | `bloocube-ai-service` | No |
| `AI_SERVICE_VERSION` | Service version | `1.0.0` | No |
| `UVICORN_WORKERS` | Number of workers | `1` | No |

### Cloud Run Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| **CPU** | 4 | High CPU for AI processing |
| **Memory** | 8Gi | Large memory for AI models |
| **Timeout** | 900s | 15 minutes for long AI operations |
| **Min Instances** | 1 | Always keep one instance warm |
| **Max Instances** | 10 | Scale up to 10 instances |
| **Concurrency** | 80 | Requests per instance |

## 🧪 Testing

### Health Check Endpoints

| Endpoint | Description | Expected Response |
|----------|-------------|-------------------|
| `/ping` | Basic health check | `{"status": "pong"}` |
| `/test` | Simple test | `{"status": "ok"}` |
| `/` | Root endpoint | Service information |
| `/health` | Detailed health | System status |
| `/docs` | API documentation | Swagger UI |

### Manual Testing
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ai-services --region=asia-southeast1 --format="value(status.url)")

# Test endpoints
curl "$SERVICE_URL/ping"
curl "$SERVICE_URL/test"
curl "$SERVICE_URL/health"
curl "$SERVICE_URL/docs"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Build Failures
**Problem**: Docker build fails with memory/timeout errors
**Solution**: 
- Increase Cloud Build machine type to `E2_HIGHCPU_8`
- Increase disk size to 200GB
- Increase timeout to 40 minutes

#### 2. Service Not Starting
**Problem**: Cloud Run shows placeholder page
**Solution**:
- Check Cloud Run logs for startup errors
- Verify all environment variables are set
- Test the Docker image locally first

#### 3. Import Errors
**Problem**: Python import errors during startup
**Solution**:
- Check `requirements.txt` for missing dependencies
- Verify Python path configuration
- Test imports in the Docker container

### Debugging Commands

```bash
# Check Cloud Run logs
gcloud run services logs read ai-services --region=asia-southeast1

# Test Docker image locally
docker run -p 8080:8080 gcr.io/PROJECT_ID/ai-services:latest

# Check service status
gcloud run services describe ai-services --region=asia-southeast1
```

## 📊 Monitoring

### Cloud Run Metrics
- **Request Count**: Number of requests
- **Request Latency**: Response time
- **CPU Utilization**: CPU usage
- **Memory Utilization**: Memory usage
- **Instance Count**: Number of running instances

### Logs
- **Application Logs**: FastAPI application logs
- **System Logs**: Cloud Run system logs
- **Build Logs**: Cloud Build logs

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
1. **Code Push** → Triggers workflow
2. **Tests** → Run linting and tests
3. **Build** → Build Docker image
4. **Deploy** → Deploy to Cloud Run
5. **Health Check** → Verify deployment
6. **Notify** → Send notifications

### Cloud Build Pipeline
1. **Fetch Source** → Get code from repository
2. **Build Image** → Build Docker image
3. **Push Image** → Push to Artifact Registry
4. **Deploy Service** → Deploy to Cloud Run
5. **Health Check** → Verify deployment
6. **Cleanup** → Clean up old images

## 📈 Scaling

### Automatic Scaling
- **CPU-based**: Scales when CPU > 70%
- **Request-based**: Scales when requests > 80 per instance
- **Min Instances**: Always keep 1 instance warm
- **Max Instances**: Scale up to 10 instances

### Manual Scaling
```bash
# Update service configuration
gcloud run services update ai-services \
    --region=asia-southeast1 \
    --min-instances=2 \
    --max-instances=20 \
    --cpu=8 \
    --memory=16Gi
```

## 🔒 Security

### Best Practices
- Use least privilege service accounts
- Enable Cloud Run authentication when needed
- Use HTTPS only
- Regular security updates
- Monitor for vulnerabilities

### Network Security
- Configure VPC connector if needed
- Use private Google access
- Set up firewall rules
- Enable DDoS protection

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Cloud Run logs
3. Check GitHub Actions logs
4. Contact the development team

---

**Last Updated**: $(date)
**Version**: 1.0.0


