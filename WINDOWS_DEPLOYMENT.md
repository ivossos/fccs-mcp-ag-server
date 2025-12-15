# Windows Deployment Guide

Complete guide for deploying the FCCS MCP Agentic Server on Windows.

## Prerequisites

### 1. Python 3.10 or Higher

**Download and Install:**
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Verify installation:
  ```powershell
  python --version
  pip --version
  ```

### 2. PostgreSQL (Optional but Recommended)

**For Production:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Install with default settings
- Note the postgres user password you set during installation
- Verify installation:
  ```powershell
  psql --version
  ```

**For Development (SQLite):**
- No installation needed - SQLite is included with Python

### 3. Git (for cloning repository)

- Download from [git-scm.com](https://git-scm.com/download/win)
- Verify installation:
  ```powershell
  git --version
  ```

## Quick Setup

### Option 1: Automated Setup Script

1. **Run the setup script:**
   ```powershell
   .\setup-windows.bat
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Create `.env` file from template
   - Initialize the database (if PostgreSQL is configured)

### Option 2: Manual Setup

#### Step 1: Clone or Navigate to Project

```powershell
cd C:\path\to\fccs-mcp-ag-server
```

#### Step 2: Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Install Dependencies

```powershell
pip install --upgrade pip
pip install -e .
```

#### Step 4: Configure Environment

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env with your settings (use Notepad or your preferred editor)
notepad .env
```

**Minimum Configuration:**
- Set `FCCS_MOCK_MODE=true` for development/testing
- Configure `DATABASE_URL` (SQLite for dev, PostgreSQL for production)

#### Step 5: Initialize Database

**For PostgreSQL:**
```powershell
python scripts/init_db.py
```

**For SQLite:**
- Database will be created automatically on first run
- No initialization needed

#### Step 6: Verify Installation

```powershell
# Test connection
python scripts/test_connection.py

# Test MCP server
python -m cli.mcp_server --help
```

## Running the Server

### MCP Server (for Claude Desktop)

```powershell
python -m cli.mcp_server
```

### Web API Server

```powershell
python -m web.server
```

Server will be available at: `http://localhost:8080`

### Interactive CLI

```powershell
python -m cli.main
```

## Windows Service (Optional)

To run as a Windows service, use [NSSM](https://nssm.cc/):

```powershell
# Download NSSM and extract to C:\nssm
# Install service
C:\nssm\nssm.exe install FCCS-MCP-Server "C:\path\to\venv\Scripts\python.exe" "-m" "web.server"
C:\nssm\nssm.exe set FCCS-MCP-Server AppDirectory "C:\path\to\fccs-mcp-ag-server"
C:\nssm\nssm.exe set FCCS-MCP-Server AppEnvironmentExtra "FCCS_MOCK_MODE=true"

# Start service
C:\nssm\nssm.exe start FCCS-MCP-Server
```

## Claude Desktop Configuration

1. **Open Claude Desktop config file:**
   ```powershell
   notepad $env:APPDATA\Claude\claude_desktop_config.json
   ```

2. **Add MCP server configuration:**
   ```json
   {
     "mcpServers": {
       "fccs-agent": {
         "command": "python",
         "args": ["-m", "cli.mcp_server"],
         "cwd": "C:\\path\\to\\fccs-mcp-ag-server",
         "env": {
           "FCCS_MOCK_MODE": "true"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Troubleshooting

### Python Not Found

**Error:** `python: command not found`

**Solution:**
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python311\python.exe`

### Virtual Environment Activation Fails

**Error:** `Execution Policy Error`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### PostgreSQL Connection Issues

**Error:** `could not connect to server`

**Solutions:**
1. Verify PostgreSQL service is running:
   ```powershell
   Get-Service postgresql*
   ```

2. Check connection string in `.env`:
   ```
   DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/fccs_agent
   ```

3. Test connection:
   ```powershell
   psql -U postgres -d fccs_agent
   ```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
- Change `PORT` in `.env` file
- Or find and stop the process using port 8080:
  ```powershell
  netstat -ano | findstr :8080
  taskkill /PID <PID> /F
  ```

### Module Not Found Errors

**Error:** `ModuleNotFoundError`

**Solution:**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -e .
```

## Development Workflow

### Daily Startup

```powershell
# Navigate to project
cd C:\path\to\fccs-mcp-ag-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server
python -m web.server
```

### Running Scripts

All scripts in the `scripts/` directory can be run directly:

```powershell
python scripts/test_connection.py
python scripts/get_top_10_performers_2025.py
python scripts/show_cache_status.py
```

### Updating Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Update dependencies
pip install --upgrade -e .
```

## Production Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] PostgreSQL installed and running
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file configured with production credentials
- [ ] Database initialized (`python scripts/init_db.py`)
- [ ] Test connection successful
- [ ] Windows Firewall configured (if needed)
- [ ] Service installed (if using NSSM)
- [ ] Logs directory configured
- [ ] Backup strategy in place

## Next Steps

- See [README.md](README.md) for API documentation
- See [CHATGPT_QUICK_START.md](CHATGPT_QUICK_START.md) for ChatGPT integration
- See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for Cloud Run deployment


