# Windows Setup Guide - FCCS MCP Server (SQLite Edition)

Complete guide to install and run the FCCS MCP Agentic Server on Windows.

---

## Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| Windows | 10 or 11 | - |
| Python | 3.10+ | https://python.org/downloads |
| Git | Any | https://git-scm.com/download/win |

---

## Quick Start (5 Minutes)

```powershell
# 1. Clone the repository
git clone https://github.com/ivossos/fccs-mcp-sqlite.git
cd fccs-mcp-sqlite

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -e .

# 4. Create configuration file
Copy-Item .env.example .env

# 5. Initialize database
python scripts\init_db.py

# 6. Start the server
python -m web.server
```

Server will be running at: **http://localhost:8080**

---

## Detailed Installation

### Step 1: Install Python

1. Download Python from https://python.org/downloads
2. Run the installer
3. **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"

Verify installation:
```powershell
python --version
# Should show: Python 3.10.x or higher
```

### Step 2: Install Git

1. Download Git from https://git-scm.com/download/win
2. Run installer with default settings

Verify installation:
```powershell
git --version
# Should show: git version 2.x.x
```

### Step 3: Clone Repository

```powershell
# Navigate to your preferred directory
cd C:\Users\YourName\Projects

# Clone the repository
git clone https://github.com/ivossos/fccs-mcp-sqlite.git

# Enter the project directory
cd fccs-mcp-sqlite
```

### Step 4: Set Up Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the beginning of your prompt.

### Step 5: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install project
pip install -e .
```

### Step 6: Configure Environment

```powershell
# Copy example configuration
Copy-Item .env.example .env

# Edit configuration (optional)
notepad .env
```

**Default .env configuration:**
```env
# FCCS Connection (use mock mode for testing)
FCCS_MOCK_MODE=true

# Database (SQLite - no external database needed!)
DATABASE_URL=sqlite:///./data/fccs_agent.db

# Server
PORT=8080
```

**For production with real FCCS:**
```env
FCCS_URL=https://your-instance.epm.us-phoenix-1.ocs.oraclecloud.com
FCCS_USERNAME=your_username
FCCS_PASSWORD=your_password
FCCS_MOCK_MODE=false

DATABASE_URL=sqlite:///./data/fccs_agent.db
PORT=8080
```

### Step 7: Initialize Database

```powershell
python scripts\init_db.py
```

**Expected output:**
```
============================================================
FCCS Agent Database Initialization (SQLite)
============================================================

Database URL: sqlite:///./data/fccs_agent.db

Step 1: Ensuring database directory exists...
Ensured directory exists: data

Step 2: Initializing database schema...
Database schema initialized successfully.
Created tables:
  - tool_executions
  - tool_metrics

============================================================
Database initialization completed successfully!
============================================================

SQLite database location: C:\...\fccs-mcp-sqlite\data\fccs_agent.db
```

### Step 8: Start the Server

**Option A: Web API Server**
```powershell
python -m web.server
```

**Option B: MCP Server (for Claude Desktop)**
```powershell
python -m cli.mcp_server
```

**Option C: Interactive CLI**
```powershell
python -m cli.main
```

---

## Verify Installation

### Test the Web Server

1. Start the server: `python -m web.server`
2. Open browser: http://localhost:8080
3. You should see the API documentation

### Test Database Connection

```powershell
python -c "from fccs_agent.services.feedback_service import FeedbackService; print('Database OK!')"
```

### Test Package Imports

```powershell
python -c "import fastapi; import mcp; import sqlalchemy; print('All packages installed!')"
```

---

## Claude Desktop Integration

To use with Claude Desktop, configure the MCP server:

### 1. Open Claude Desktop Config

```powershell
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

### 2. Add Server Configuration

```json
{
  "mcpServers": {
    "fccs-agent": {
      "command": "C:\\Users\\YourName\\Projects\\fccs-mcp-sqlite\\venv\\Scripts\\python.exe",
      "args": ["-m", "cli.mcp_server"],
      "cwd": "C:\\Users\\YourName\\Projects\\fccs-mcp-sqlite",
      "env": {
        "FCCS_MOCK_MODE": "true"
      }
    }
  }
}
```

**Note:** Replace `YourName` with your actual Windows username.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

---

## Daily Usage

### Start Server

```powershell
# Navigate to project
cd C:\Users\YourName\Projects\fccs-mcp-sqlite

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server
python -m web.server
```

### Create a Start Script

Create `start.bat` in the project root:

```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m web.server
```

Double-click `start.bat` to start the server.

---

## Database Location

The SQLite database is stored at:
```
./data/fccs_agent.db
```

This file contains:
- Tool execution history
- User feedback and ratings
- RL (Reinforcement Learning) metrics
- Performance statistics

### Backup Database

```powershell
Copy-Item data\fccs_agent.db data\fccs_agent_backup.db
```

### Reset Database

```powershell
Remove-Item data\fccs_agent.db
python scripts\init_db.py
```

---

## Troubleshooting

### "python: command not found"

**Solution:** Reinstall Python and check "Add Python to PATH"

### "Execution Policy Error"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "ModuleNotFoundError"

**Solution:** Make sure venv is activated (you should see `(venv)` in prompt):
```powershell
.\venv\Scripts\Activate.ps1
pip install -e .
```

### "Port 8080 already in use"

**Solution:** Either stop the other process or change the port:
```powershell
# Find what's using port 8080
netstat -ano | findstr :8080

# Or change port in .env
PORT=8081
```

### "Database locked" error

**Solution:** Make sure only one server instance is running. Check Task Manager for other Python processes.

### Server won't start

**Check these:**
1. Virtual environment is activated
2. All dependencies installed: `pip install -e .`
3. .env file exists and is configured
4. Database is initialized: `python scripts\init_db.py`

---

## Project Structure

```
fccs-mcp-sqlite/
├── data/                    # SQLite database directory
│   └── fccs_agent.db       # Database file (created on init)
├── fccs_agent/             # Main application code
│   ├── services/           # RL, Feedback, Cache services
│   └── tools/              # FCCS tools
├── web/                    # Web server
├── cli/                    # CLI and MCP server
├── scripts/                # Utility scripts
│   └── init_db.py         # Database initialization
├── docs/                   # Documentation
├── .env                    # Configuration (create from .env.example)
├── .env.example           # Example configuration
└── pyproject.toml         # Python project definition
```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `python -m web.server` | Start web API server |
| `python -m cli.mcp_server` | Start MCP server |
| `python -m cli.main` | Interactive CLI |
| `python scripts\init_db.py` | Initialize database |
| `pip install -e .` | Install/update dependencies |
| `pip list` | Show installed packages |

---

## Next Steps

1. **Test the API:** Open http://localhost:8080/docs for interactive API docs
2. **Configure FCCS:** Update `.env` with real FCCS credentials
3. **Integrate with Claude:** Configure Claude Desktop (see above)
4. **Explore tools:** Check available FCCS tools at `/tools` endpoint

---

## Support

- Check the [Troubleshooting](#troubleshooting) section
- Review server logs in the terminal
- Check GitHub Issues for known problems

**Installation complete!**
