#!/bin/bash
# Deploy FCCS MCP Server to Google Cloud Run

set -e

# Configuration
# Set your project ID here or use environment variable GOOGLE_CLOUD_PROJECT
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0229610994}
REGION=${REGION:-us-central1}
SERVICE_NAME="fccs-mcp-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=========================================="
echo "Deploying FCCS MCP Server to Cloud Run"
echo "=========================================="
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Name: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "Pushing image to Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PORT=8080" \
    --set-secrets "FCCS_URL=FCCS_URL:latest,FCCS_USERNAME=FCCS_USERNAME:latest,FCCS_PASSWORD=FCCS_PASSWORD:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    || echo "Note: Secrets not configured. Set them manually in Cloud Console."

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test the deployment:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "View logs:"
echo "  gcloud run logs tail ${SERVICE_NAME} --region ${REGION}"
echo ""

