# ChatGPT Custom GPT Configuration Guide

This guide explains how to configure ChatGPT (Custom GPT) to use the FCCS MCP Server.

## Option 1: Using Cloud Run (Recommended)

### Step 1: Deploy to Cloud Run

First, deploy the server to Google Cloud Run (see `QUICK_DEPLOY.md`):

```powershell
.\deploy-cloud-run.ps1
```

After deployment, you'll get a URL like:
```
https://fccs-mcp-server-xxxxx-uc.a.run.app
```

### Step 2: Configure ChatGPT Custom GPT

1. **Go to ChatGPT Custom GPTs:**
   - Visit: https://chat.openai.com/gpts
   - Click "Create" or "Edit" on your GPT

2. **Configure the Action:**
   - Go to the "Actions" section
   - Click "Create new action"
   - Choose "API" or "OpenAPI schema"

3. **Add API Configuration:**
   
   **Schema URL (if using OpenAPI):**
   ```
   https://your-cloud-run-url.run.app/openapi.json
   ```
   
   **Or Manual Configuration:**
   - **Base URL:** `https://your-cloud-run-url.run.app`
   - **Authentication:** None (or API Key if you enable auth)

4. **Available Endpoints:**
   - `GET /health` - Health check
   - `GET /tools` - List all available tools
   - `POST /execute` - Execute any tool
   - `POST /message` - MCP-compatible endpoint

### Step 3: Test Connection

In ChatGPT, try:
```
"List all available FCCS tools"
```

ChatGPT should call `/tools` endpoint and show you all available tools.

## Option 2: Using Local Server

### Step 1: Start Local Server

```powershell
# Set environment variables
$env:FCCS_URL = "your-fccs-url"
$env:FCCS_USERNAME = "your-username"
$env:FCCS_PASSWORD = "your-password"

# Or use mock mode
$env:FCCS_MOCK_MODE = "true"

# Start server
python -m web.server
```

Server will run on: `http://localhost:8080`

### Step 2: Expose Local Server (ngrok)

Since ChatGPT needs a public URL, use ngrok:

1. **Install ngrok:**
   ```powershell
   # Download from https://ngrok.com/download
   # Or use chocolatey
   choco install ngrok
   ```

2. **Start ngrok tunnel:**
   ```powershell
   ngrok http 8080
   ```

3. **Copy the public URL:**
   ```
   https://xxxx-xx-xx-xx-xx.ngrok-free.app
   ```

4. **Use this URL in ChatGPT Custom GPT configuration**

## Option 3: Direct API Integration

### Using the `/message` Endpoint (MCP-compatible)

ChatGPT can call the MCP-compatible endpoint:

**Request Format:**
```json
POST /message
{
  "method": "tools/list",
  "params": {}
}
```

**Or:**
```json
POST /message
{
  "method": "tools/call",
  "params": {
    "name": "get_application_info",
    "arguments": {}
  }
}
```

### Using Standard REST Endpoints

**List Tools:**
```json
GET /tools
```

**Execute Tool:**
```json
POST /execute
{
  "tool_name": "get_application_info",
  "arguments": {},
  "session_id": "chatgpt-session"
}
```

## ChatGPT Custom GPT Instructions

Add these instructions to your Custom GPT:

```
You are an Oracle FCCS (Financial Consolidation and Close) assistant. 
You have access to the FCCS API through the configured actions.

Available capabilities:
- Get application information and API versions
- List and execute business rules and data rules
- Query dimensions and members
- Manage consolidation journals
- Export and import data slices
- Generate reports
- Run consolidation processes

When the user asks about FCCS data or operations, use the available tools/actions.
Always provide clear, structured responses with the data retrieved.

For financial analysis:
- Use smart_retrieve for quick data queries
- Use export_data_slice for complex grid exports
- Format financial numbers with proper currency symbols and commas

Be helpful and explain what operations you're performing.
```

## Example Prompts for ChatGPT

Once configured, you can use prompts like:

1. **"Get information about the FCCS application"**
   - Calls: `get_application_info`

2. **"Show me the top 10 performing entities in 2024"**
   - Calls: `smart_retrieve` with Net Income data

3. **"List all dimensions in the application"**
   - Calls: `get_dimensions`

4. **"Get members of the Entity dimension"**
   - Calls: `get_members` with dimension_name="Entity"

5. **"Run the consolidation business rule"**
   - Calls: `run_business_rule`

6. **"Show me journals for January 2025"**
   - Calls: `get_journals` with filters

## Authentication (Optional)

If you want to secure your API:

### Option 1: API Key Authentication

1. **Update web server** to require API key
2. **Set API key in ChatGPT Custom GPT** configuration
3. **Add header:** `Authorization: Bearer YOUR_API_KEY`

### Option 2: Cloud Run Authentication

1. **Remove `--allow-unauthenticated`** from deployment
2. **Enable authentication** in Cloud Run
3. **Configure service account** in ChatGPT

## Troubleshooting

### ChatGPT can't connect
- Verify the server URL is accessible
- Check Cloud Run service is running
- Test with: `curl https://your-url.run.app/health`

### Tools not showing
- Check `/tools` endpoint returns data
- Verify JSON format is correct
- Check ChatGPT action configuration

### Authentication errors
- Verify API key is set correctly
- Check Cloud Run IAM permissions
- Ensure service account has access

### Timeout errors
- Increase Cloud Run timeout: `--timeout 600`
- Check FCCS API response times
- Consider async operations for long-running tasks

## Testing the Configuration

1. **Test health endpoint:**
   ```powershell
   curl https://your-url.run.app/health
   ```

2. **Test tools list:**
   ```powershell
   curl https://your-url.run.app/tools
   ```

3. **Test tool execution:**
   ```powershell
   curl -X POST https://your-url.run.app/execute `
     -H "Content-Type: application/json" `
     -d '{"tool_name": "get_application_info", "arguments": {}, "session_id": "test"}'
   ```

## Next Steps

1. Deploy to Cloud Run (see `QUICK_DEPLOY.md`)
2. Configure ChatGPT Custom GPT with the Cloud Run URL
3. Test with simple queries
4. Add custom instructions for your use case
5. Set up monitoring and logging

## Support

For issues:
- Check Cloud Run logs: `gcloud run logs tail fccs-mcp-server --region us-central1`
- Test endpoints directly with curl/Postman
- Verify environment variables are set correctly














