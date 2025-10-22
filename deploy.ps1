# =============================================================================
# BLOOCUBE AI SERVICES - WINDOWS POWERSHELL DEPLOYMENT SCRIPT
# =============================================================================

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "ai-services",
    [string]$RepoName = "bloocube",
    [string]$ImageTag = "latest"
)

# Configuration
$ErrorActionPreference = "Stop"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Requirements {
    Write-Info "Checking requirements..."
    
    # Check if gcloud is installed
    try {
        gcloud version | Out-Null
    } catch {
        Write-Error "gcloud CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check if docker is installed
    try {
        docker version | Out-Null
    } catch {
        Write-Error "Docker is not installed. Please install it first."
        exit 1
    }
    
    # Check if PROJECT_ID is set
    if ([string]::IsNullOrEmpty($ProjectId)) {
        Write-Error "GCP_PROJECT_ID environment variable is not set."
        exit 1
    }
    
    Write-Success "All requirements met"
}

function Connect-GCP {
    Write-Info "Authenticating with GCP..."
    
    # Check if already authenticated
    $activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
    if ($activeAccount) {
        Write-Success "Already authenticated with GCP"
    } else {
        Write-Info "Please authenticate with GCP..."
        gcloud auth login
    }
    
    # Set project
    gcloud config set project $ProjectId
    Write-Success "Project set to $ProjectId"
}

function Initialize-Docker {
    Write-Info "Configuring Docker for GCR..."
    gcloud auth configure-docker "${Region}-docker.pkg.dev"
    Write-Success "Docker configured for GCR"
}

function Build-Image {
    Write-Info "Building Docker image..."
    
    $imageName = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:${ImageTag}"
    $commitHash = git rev-parse --short HEAD
    
    docker build `
        --build-arg BUILDKIT_INLINE_CACHE=1 `
        --progress=plain `
        -t $imageName `
        -t "${imageName}:${commitHash}" `
        .
    
    Write-Success "Docker image built successfully"
}

function Push-Image {
    Write-Info "Pushing Docker image to registry..."
    
    $imageName = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:${ImageTag}"
    $commitHash = git rev-parse --short HEAD
    
    docker push $imageName
    docker push "${imageName}:${commitHash}"
    
    Write-Success "Docker image pushed successfully"
}

function Deploy-Service {
    Write-Info "Deploying to Cloud Run..."
    
    $imageName = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:${ImageTag}"
    
    gcloud run deploy $ServiceName `
        --image $imageName `
        --region $Region `
        --platform managed `
        --allow-unauthenticated `
        --cpu 4 `
        --memory 8Gi `
        --timeout 900 `
        --min-instances 1 `
        --max-instances 10 `
        --concurrency 80 `
        --port 8080 `
        --set-env-vars NODE_ENV=production,ENVIRONMENT=production,LOG_LEVEL=info,AI_SERVICE_NAME=bloocube-ai-service,AI_SERVICE_VERSION=1.0.0,UVICORN_WORKERS=1
    
    Write-Success "Service deployed successfully"
}

function Test-Health {
    Write-Info "Performing health check..."
    
    # Wait for service to be ready
    Start-Sleep -Seconds 30
    
    # Get service URL
    $serviceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
    Write-Info "Service URL: $serviceUrl"
    
    # Test endpoints
    $endpoints = @("ping", "test", "", "health", "docs")
    
    foreach ($endpoint in $endpoints) {
        Write-Info "Testing $endpoint endpoint..."
        $url = if ($endpoint -eq "") { $serviceUrl } else { "$serviceUrl/$endpoint" }
        
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 30 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "$endpoint endpoint working"
            } else {
                Write-Warning "$endpoint endpoint returned status $($response.StatusCode)"
            }
        } catch {
            Write-Warning "$endpoint endpoint failed: $($_.Exception.Message)"
        }
    }
    
    Write-Success "Health check completed"
}

function Main {
    Write-Info "Starting Bloocube AI Services deployment..."
    Write-Host "=================================================="
    
    Test-Requirements
    Connect-GCP
    Initialize-Docker
    Build-Image
    Push-Image
    Deploy-Service
    Test-Health
    
    Write-Host "=================================================="
    Write-Success "Deployment completed successfully!"
    
    # Get final service URL
    $serviceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
    Write-Host ""
    Write-Info "🌐 Service URL: $serviceUrl"
    Write-Info "📚 API Documentation: $serviceUrl/docs"
    Write-Info "🔍 Health Check: $serviceUrl/health"
    Write-Host ""
}

# Run main function
Main


