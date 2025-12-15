# Google Cloud Run Deployment Guide

This guide explains how to deploy the FCCS MCP Server to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
   ```bash
   # Install: https://cloud.google.com/sdk/docs/install
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Docker** installed and running
4. **Required APIs enabled**:
   - Cloud Build API
   - Cloud Run API
   - Container Registry API

## Quick Deploy

### Option 1: Using Deployment Script (Recommended)

**Windows (PowerShell):**
```powershell
.\deploy-cloud-run.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

### Option 2: Manual Deployment

1. **Set your project:**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   gcloud config set project $GOOGLE_CLOUD_PROJECT
   ```

2. **Enable required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

3. **Build and push Docker image:**
   ```bash
   docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/fccs-mcp-server:latest .
   docker push gcr.io/$GOOGLE_CLOUD_PROJECT/fccs-mcp-server:latest
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy fccs-mcp-server \
     --image gcr.io/$GOOGLE_CLOUD_PROJECT/fccs-mcp-server:latest \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --port 8080 \
     --memory 512Mi \
     --cpu 1 \
     --timeout 300 \
     --max-instances 10 \
     --set-env-vars "PORT=8080"
   ```

## Environment Variables

Set these as Cloud Run secrets or environment variables:

### Required (if not in mock mode):
- `FCCS_URL` - Oracle EPM Cloud URL
- `FCCS_USERNAME` - FCCS username
- `FCCS_PASSWORD` - FCCS password

### Optional:
- `FCCS_MOCK_MODE` - Set to `true` for testing without real FCCS connection
- `FCCS_API_VERSION` - API version (default: `v3`)
- `DATABASE_URL` - PostgreSQL connection string (for feedback service)
- `GOOGLE_API_KEY` - Google API key for Gemini model
- `MODEL_ID` - Model ID (default: `gemini-2.0-flash`)
- `PORT` - Server port (default: 8080, Cloud Run sets this automatically)

### Setting Secrets in Cloud Run

1. **Create secrets in Secret Manager:**
   ```bash
   echo -n "your-fccs-url" | gcloud secrets create FCCS_URL --data-file=-
   echo -n "your-username" | gcloud secrets create FCCS_USERNAME --data-file=-
   echo -n "your-password" | gcloud secrets create FCCS_PASSWORD --data-file=-
   ```

2. **Grant Cloud Run access:**
   ```bash
   gcloud secrets add-iam-policy-binding FCCS_URL \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Update Cloud Run service to use secrets:**
   ```bash
   gcloud run services update fccs-mcp-server \
     --region us-central1 \
     --set-secrets="FCCS_URL=FCCS_URL:latest,FCCS_USERNAME=FCCS_USERNAME:latest,FCCS_PASSWORD=FCCS_PASSWORD:latest"
   ```

## Using Cloud Build (CI/CD)

1. **Create a trigger:**
   ```bash
   gcloud builds triggers create github \
     --repo-name=your-repo \
     --repo-owner=your-org \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

2. **Or run manually:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

## Testing the Deployment

1. **Get the service URL:**
   ```bash
   gcloud run services describe fccs-mcp-server \
     --region us-central1 \
     --format 'value(status.url)'
   ```

2. **Test health endpoint:**
   ```bash
   curl https://your-service-url.run.app/health
   ```

3. **List available tools:**
   ```bash
   curl https://your-service-url.run.app/tools
   ```

4. **Call a tool:**
   ```bash
   curl -X POST https://your-service-url.run.app/execute \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "get_application_info",
       "arguments": {},
       "session_id": "test"
     }'
   ```

## Monitoring and Logs

1. **View logs:**
   ```bash
   gcloud run logs tail fccs-mcp-server --region us-central1
   ```

2. **View in Cloud Console:**
   - Go to Cloud Run → fccs-mcp-server → Logs
   - Or use Cloud Monitoring for metrics

## Scaling Configuration

Default settings:
- **Memory:** 512Mi
- **CPU:** 1
- **Timeout:** 300 seconds
- **Max Instances:** 10
- **Min Instances:** 0 (scales to zero)

To update:
```bash
gcloud run services update fccs-mcp-server \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 20 \
  --min-instances 1
```

## Troubleshooting

### Service won't start
- Check logs: `gcloud run logs tail fccs-mcp-server --region us-central1`
- Verify environment variables are set correctly
- Check that secrets are accessible

### Connection timeouts
- Increase timeout: `--timeout 600`
- Check FCCS URL is accessible from Cloud Run
- Verify firewall rules allow outbound connections

### Out of memory
- Increase memory: `--memory 1Gi` or `--memory 2Gi`

### Database connection issues
- Ensure DATABASE_URL is set correctly
- Check that Cloud SQL proxy is configured if using Cloud SQL
- Verify network connectivity

## Cost Optimization

- **Scale to zero:** Default setting (no cost when idle)
- **Min instances:** Set to 0 unless you need always-on
- **Memory:** Start with 512Mi, increase only if needed
- **CPU:** Use 1 CPU unless processing is CPU-bound

## Security Best Practices

1. **Use Secret Manager** for sensitive credentials
2. **Enable authentication** if needed: Remove `--allow-unauthenticated`
3. **Use VPC connector** for private resources
4. **Enable Cloud Armor** for DDoS protection
5. **Regular security updates:** Keep base image updated

## Next Steps

- Set up monitoring alerts
- Configure custom domain
- Set up CI/CD pipeline
- Enable authentication if needed
- Configure VPC connector for private resources


