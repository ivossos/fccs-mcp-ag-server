# Deploy FCCS MCP Server to Google Cloud Run (PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
# Set your project ID here or use environment variable GOOGLE_CLOUD_PROJECT
$PROJECT_ID = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "gen-lang-client-0229610994" }
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$SERVICE_NAME = "fccs-mcp-server"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploying FCCS MCP Server to Cloud Run" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project ID: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Service Name: $SERVICE_NAME"
Write-Host ""

# Check if gcloud is installed
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    Write-Host "Install from: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
    exit 1
}

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Green
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "Enabling required APIs..." -ForegroundColor Green
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push image
Write-Host "Building Docker image..." -ForegroundColor Green
docker build -t "$IMAGE_NAME`:latest" .

Write-Host "Pushing image to Container Registry..." -ForegroundColor Green
docker push "$IMAGE_NAME`:latest"

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
$deployArgs = @(
    "run", "deploy", $SERVICE_NAME,
    "--image", "$IMAGE_NAME`:latest",
    "--region", $REGION,
    "--platform", "managed",
    "--allow-unauthenticated",
    "--port", "8080",
    "--memory", "512Mi",
    "--cpu", "1",
    "--timeout", "300",
    "--max-instances", "10",
    "--set-env-vars", "PORT=8080"
)

try {
    gcloud @deployArgs
} catch {
    Write-Host "Note: If secrets are needed, configure them in Cloud Console" -ForegroundColor Yellow
}

# Get service URL
Write-Host "Getting service URL..." -ForegroundColor Green
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
    --region $REGION `
    --format 'value(status.url)'

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test the deployment:" -ForegroundColor Yellow
Write-Host "  curl $SERVICE_URL/health" -ForegroundColor White
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  gcloud run logs tail $SERVICE_NAME --region $REGION" -ForegroundColor White
Write-Host ""

