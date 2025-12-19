# ChatGPT Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Deploy to Cloud Run

```powershell
# Authenticate
gcloud auth login

# Set project
gcloud config set project gen-lang-client-0229610994

# Deploy
.\deploy-cloud-run.ps1
```

**Copy the service URL** (e.g., `https://fccs-mcp-server-xxxxx-uc.a.run.app`)

### Step 2: Configure ChatGPT Custom GPT

1. Go to: https://chat.openai.com/gpts
2. Click **"Create"** → **"Configure"**
3. Fill in:
   - **Name:** FCCS Assistant
   - **Description:** Oracle FCCS Financial Consolidation Assistant
   - **Instructions:** See below

4. Go to **"Actions"** tab
5. Click **"Create new action"**
6. Choose **"API"**
7. Enter:
   - **Schema:** `https://your-cloud-run-url.run.app/openapi.json`
   - Or manually add endpoints (see below)

### Step 3: Test

In ChatGPT, try:
```
"Get information about the FCCS application"
```

## 📝 Custom GPT Instructions

Paste this in the "Instructions" field:

```
You are an Oracle FCCS (Financial Consolidation and Close) assistant with access to the FCCS API.

Available capabilities:
- Application information and API versions
- Business rules and data rules execution
- Dimension and member queries
- Consolidation journal management
- Data export and import
- Report generation
- Consolidation processes

When users ask about FCCS:
1. Use the available tools/actions to retrieve data
2. Format financial numbers with currency symbols and commas
3. Provide clear, structured responses
4. Explain what operations you're performing

For analysis requests:
- Use smart_retrieve for quick queries
- Use export_data_slice for complex grids
- Format results in tables when appropriate

Be helpful, accurate, and explain your actions.
```

## 🔧 Manual API Configuration

If OpenAPI schema doesn't work, configure manually:

### Endpoint 1: List Tools
- **Method:** GET
- **URL:** `https://your-url.run.app/tools`
- **Description:** Get all available FCCS tools

### Endpoint 2: Execute Tool
- **Method:** POST
- **URL:** `https://your-url.run.app/execute`
- **Body:**
```json
{
  "tool_name": "get_application_info",
  "arguments": {},
  "session_id": "chatgpt"
}
```

### Endpoint 3: Health Check
- **Method:** GET
- **URL:** `https://your-url.run.app/health`
- **Description:** Check server status

## ✅ Test Commands

Try these in ChatGPT:

1. **"What tools are available?"**
2. **"Get FCCS application information"**
3. **"List all dimensions"**
4. **"Show me Entity dimension members"**
5. **"Get Net Income for FY25"**

## 🐛 Troubleshooting

**Can't connect?**
- Check Cloud Run URL is accessible
- Test: `curl https://your-url.run.app/health`

**Tools not working?**
- Verify endpoint URLs are correct
- Check ChatGPT action configuration
- Review Cloud Run logs

**Need help?**
- See `CHATGPT_CONFIGURATION.md` for detailed guide
- Check Cloud Run logs: `gcloud run logs tail fccs-mcp-server --region us-central1`












