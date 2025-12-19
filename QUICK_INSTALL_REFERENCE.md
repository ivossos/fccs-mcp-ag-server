# Quick Install Reference - FCCS MCP Server (Windows)

## 🚀 Fast Track Installation (5 Minutes)

### Prerequisites Check
```powershell
python --version    # Should be 3.10+
git --version       # Should be installed
```

### Installation Steps

```powershell
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/fccs-mcp-ag-server.git
cd fccs-mcp-ag-server

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -e .

# 4. Create .env file (minimum config)
@"
FCCS_MOCK_MODE=true
DATABASE_URL=sqlite:///./fccs_agent.db
PORT=8080
"@ | Out-File -FilePath .env -Encoding utf8

# 5. Start server
python -m web.server
```

## 📝 Common Commands

### Start Servers
```powershell
.\start-server.bat          # Web API server
.\start-mcp-server.bat       # MCP server
python -m cli.main           # Interactive CLI
```

### Daily Workflow
```powershell
cd fccs-mcp-ag-server
.\venv\Scripts\Activate.ps1
python -m web.server
```

### Troubleshooting
```powershell
# Fix execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Reinstall dependencies
pip install -e .

# Check port usage
netstat -ano | findstr :8080
```

## 🔧 Configuration

### Minimal .env (Development)
```env
FCCS_MOCK_MODE=true
DATABASE_URL=sqlite:///./fccs_agent.db
PORT=8080
```

### Production .env
```env
FCCS_URL=https://your-instance.epm...
FCCS_USERNAME=your_username
FCCS_PASSWORD=your_password
DATABASE_URL=postgresql+psycopg://postgres:pass@localhost:5432/fccs_agent
```

## ✅ Verification

```powershell
# Test installation
python -c "import fastapi; import mcp; print('OK')"

# Test server
# Open browser: http://localhost:8080
```

## 📚 Full Guide

See `WINDOWS_INSTALLATION_GUIDE.md` for complete step-by-step instructions.









