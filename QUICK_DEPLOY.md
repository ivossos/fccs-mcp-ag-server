# Quick Deploy to Google Cloud Run

**Project ID:** `gen-lang-client-0229610994`

## Prerequisites

1. **Authenticate with Google Cloud:**
   ```powershell
   gcloud auth login
   ```

2. **Set the project:**
   ```powershell
   gcloud config set project gen-lang-client-0229610994
   ```

## Deploy

### Option 1: Use the deployment script (Recommended)

**Windows:**
```powershell
.\deploy-cloud-run.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

### Option 2: Manual deployment

```powershell
# Set project
$env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0229610994"
gcloud config set project gen-lang-client-0229610994

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push
docker build -t gcr.io/gen-lang-client-0229610994/fccs-mcp-server:latest .
docker push gcr.io/gen-lang-client-0229610994/fccs-mcp-server:latest

# Deploy
gcloud run deploy fccs-mcp-server `
  --image gcr.io/gen-lang-client-0229610994/fccs-mcp-server:latest `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars "PORT=8080"
```

## Set Environment Variables/Secrets

After deployment, set your secrets:

```powershell
# Create secrets (if using Secret Manager)
echo -n "your-fccs-url" | gcloud secrets create FCCS_URL --data-file=-
echo -n "your-username" | gcloud secrets create FCCS_USERNAME --data-file=-
echo -n "your-password" | gcloud secrets create FCCS_PASSWORD --data-file=-

# Or set as environment variables directly
gcloud run services update fccs-mcp-server `
  --region us-central1 `
  --set-env-vars "FCCS_URL=your-url,FCCS_USERNAME=your-user,FCCS_PASSWORD=your-pass,FCCS_MOCK_MODE=false"
```

## Test Deployment

```powershell
# Get service URL
$URL = gcloud run services describe fccs-mcp-server --region us-central1 --format 'value(status.url)'

# Test health
curl "$URL/health"

# List tools
curl "$URL/tools"
```












