# Step-by-Step Installation Guide: FCCS MCP Server on Windows

Complete guide to install and deploy the FCCS MCP Agentic Server from GitHub on Windows.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Required Software](#step-1-install-required-software)
3. [Step 2: Clone Repository from GitHub](#step-2-clone-repository-from-github)
4. [Step 3: Set Up Python Environment](#step-3-set-up-python-environment)
5. [Step 4: Install Dependencies](#step-4-install-dependencies)
6. [Step 5: Configure Environment](#step-5-configure-environment)
7. [Step 6: Initialize Database (Optional)](#step-6-initialize-database-optional)
8. [Step 7: Verify Installation](#step-7-verify-installation)
9. [Step 8: Run the Server](#step-8-run-the-server)
10. [Step 9: Configure Claude Desktop (Optional)](#step-9-configure-claude-desktop-optional)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- **Windows 10 or 11**
- **Administrator access** (for some installations)
- **Internet connection** (for downloading and installing)

---

## Step 1: Install Required Software

### 1.1 Install Python 3.10 or Higher

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Download the latest Python 3.10+ version (Python 3.11 or 3.12 recommended)
   - Choose "Windows installer (64-bit)"

2. **Install Python:**
   - Run the installer
   - ⚠️ **IMPORTANT:** Check the box "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   ```powershell
   python --version
   pip --version
   ```
   You should see something like:
   ```
   Python 3.11.5
   pip 23.2.1
   ```

### 1.2 Install Git (if not already installed)

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - Download the installer

2. **Install Git:**
   - Run the installer
   - Use default settings (recommended)
   - Click "Next" through all steps

3. **Verify Installation:**
   ```powershell
   git --version
   ```
   You should see something like: `git version 2.42.0`

### 1.3 Install PostgreSQL (Optional - for Production)

**For Development:** You can skip this and use SQLite (included with Python).

**For Production:**

1. **Download PostgreSQL:**
   - Go to: https://www.postgresql.org/download/windows/
   - Download the installer

2. **Install PostgreSQL:**
   - Run the installer
   - Use default settings
   - **Remember the password** you set for the `postgres` user
   - Complete the installation

3. **Verify Installation:**
   ```powershell
   psql --version
   ```

---

## Step 2: Clone Repository from GitHub

### 2.1 Open PowerShell

1. Press `Windows Key + X`
2. Select "Windows PowerShell" or "Terminal"
3. Or press `Windows Key + R`, type `powershell`, press Enter

### 2.2 Navigate to Your Desired Directory

```powershell
# Example: Navigate to your Downloads or Documents folder
cd C:\Users\YourUsername\Downloads
# Or
cd C:\Users\YourUsername\Documents
```

### 2.3 Clone the Repository

**Option A: If you have the repository URL:**

```powershell
# Replace YOUR_USERNAME with the actual GitHub username
git clone https://github.com/YOUR_USERNAME/fccs-mcp-ag-server.git
```

**Option B: If you need to find the repository:**

1. Go to GitHub.com
2. Search for "fccs-mcp-ag-server"
3. Click on the repository
4. Click the green "Code" button
5. Copy the HTTPS URL
6. Use it in the clone command:

```powershell
git clone https://github.com/YOUR_USERNAME/fccs-mcp-ag-server.git
```

### 2.4 Navigate into the Project Directory

```powershell
cd fccs-mcp-ag-server
```

---

## Step 3: Set Up Python Environment

### 3.1 Create Virtual Environment

```powershell
python -m venv venv
```

This creates a folder called `venv` in your project directory.

### 3.2 Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:
```powershell
.\venv\Scripts\Activate.ps1
```

**You should see `(venv)` at the beginning of your prompt**, like:
```
(venv) PS C:\Users\YourUsername\Downloads\fccs-mcp-ag-server>
```

---

## Step 4: Install Dependencies

### 4.1 Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4.2 Install Project Dependencies

```powershell
pip install -e .
```

This will install all required packages. It may take a few minutes.

**Expected output:**
```
Successfully installed google-adk-1.0.0 mcp-1.0.0 fastapi-0.115.0 ...
```

---

## Step 5: Configure Environment

### 5.1 Create Environment File

Check if `.env.example` exists:
```powershell
dir .env.example
```

If it exists, copy it:
```powershell
Copy-Item .env.example .env
```

If it doesn't exist, create a new `.env` file:
```powershell
New-Item -Path .env -ItemType File
```

### 5.2 Edit the .env File

Open the `.env` file in Notepad:
```powershell
notepad .env
```

**Minimum Configuration (for Development/Testing):**

Add these lines:
```env
# Development Mode (uses mock data, no real FCCS connection needed)
FCCS_MOCK_MODE=true

# Database (SQLite for development - no setup needed)
DATABASE_URL=sqlite:///./fccs_agent.db

# Server Configuration
PORT=8080
HOST=localhost
```

**For Production (with real FCCS connection):**

```env
# FCCS Connection
FCCS_URL=https://your-instance.epm.us-frankfurt-1.ocp.oc-test.com
FCCS_USERNAME=your_username
FCCS_PASSWORD=your_password
FCCS_IDENTITY_DOMAIN=your_domain

# Database (PostgreSQL)
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/fccs_agent

# Server Configuration
PORT=8080
HOST=0.0.0.0
```

**Save the file** (Ctrl+S) and close Notepad.

---

## Step 6: Initialize Database (Optional)

### 6.1 For SQLite (Development)

No initialization needed! The database will be created automatically on first run.

### 6.2 For PostgreSQL (Production)

1. **Create the database:**
   ```powershell
   # Connect to PostgreSQL
   psql -U postgres
   ```
   
   Then in the PostgreSQL prompt:
   ```sql
   CREATE DATABASE fccs_agent;
   \q
   ```

2. **Initialize the database:**
   ```powershell
   python scripts\init_db.py
   ```

---

## Step 7: Verify Installation

### 7.1 Test Python Installation

```powershell
python -c "import sys; print(f'Python {sys.version}')"
```

### 7.2 Test Package Installation

```powershell
python -c "import fastapi; import mcp; print('All packages installed successfully!')"
```

### 7.3 Test Connection (if configured)

```powershell
python scripts\test_connection.py
```

---

## Step 8: Run the Server

### 8.1 Start MCP Server (for Claude Desktop)

**In a PowerShell window:**

```powershell
# Make sure you're in the project directory
cd C:\Users\YourUsername\Downloads\fccs-mcp-ag-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start MCP server
python -m cli.mcp_server
```

**Or use the batch file:**
```powershell
.\start-mcp-server.bat
```

The server is now running and ready to communicate with Claude Desktop via stdio.

### 8.2 Start Web API Server

**In a new PowerShell window:**

```powershell
# Navigate to project directory
cd C:\Users\YourUsername\Downloads\fccs-mcp-ag-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start web server
python -m web.server
```

**Or use the batch file:**
```powershell
.\start-server.bat
```

**You should see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:8080
```

**Test the server:**
- Open your browser
- Go to: http://localhost:8080
- You should see a health check response

### 8.3 Run Interactive CLI

```powershell
python -m cli.main
```

---

## Step 9: Configure Claude Desktop (Optional)

If you want to use the MCP server with Claude Desktop:

### 9.1 Open Claude Desktop Config File

```powershell
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

**If the file doesn't exist**, create it with this content:

```json
{
  "mcpServers": {
    "fccs-agent": {
      "command": "python",
      "args": ["-m", "cli.mcp_server"],
      "cwd": "C:\\Users\\YourUsername\\Downloads\\fccs-mcp-ag-server",
      "env": {
        "FCCS_MOCK_MODE": "true"
      }
    }
  }
}
```

**Important:** Replace `C:\\Users\\YourUsername\\Downloads\\fccs-mcp-ag-server` with your actual project path.

### 9.2 Update the Path

Use the full path to your project. To get it:
```powershell
pwd
```

Copy the output and use it in the config file (use double backslashes `\\`).

### 9.3 Restart Claude Desktop

1. Close Claude Desktop completely
2. Reopen it
3. The MCP server should now be available

---

## Troubleshooting

### Problem: "python: command not found"

**Solution:**
1. Reinstall Python
2. Make sure "Add Python to PATH" is checked during installation
3. Or use the full path: `C:\Python311\python.exe`

### Problem: "Execution Policy Error" when activating venv

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: "ModuleNotFoundError"

**Solution:**
1. Make sure virtual environment is activated (you should see `(venv)` in prompt)
2. Reinstall dependencies:
   ```powershell
   pip install -e .
   ```

### Problem: "Port 8080 already in use"

**Solution:**
1. Find what's using the port:
   ```powershell
   netstat -ano | findstr :8080
   ```
2. Kill the process (replace `<PID>` with the number from step 1):
   ```powershell
   taskkill /PID <PID> /F
   ```
3. Or change the port in `.env` file:
   ```env
   PORT=8081
   ```

### Problem: PostgreSQL Connection Failed

**Solution:**
1. Check if PostgreSQL service is running:
   ```powershell
   Get-Service postgresql*
   ```
2. Start the service if stopped:
   ```powershell
   Start-Service postgresql-x64-15
   ```
   (Replace `15` with your PostgreSQL version)
3. Verify connection string in `.env` file

### Problem: Git Clone Failed

**Solution:**
1. Check your internet connection
2. Verify the repository URL is correct
3. If using private repo, make sure you're authenticated:
   ```powershell
   git config --global credential.helper wincred
   ```

### Problem: "pip install -e ." Fails

**Solution:**
1. Make sure you're in the project directory
2. Check that `pyproject.toml` exists:
   ```powershell
   dir pyproject.toml
   ```
3. Try upgrading pip first:
   ```powershell
   python -m pip install --upgrade pip
   pip install -e .
   ```

---

## Quick Reference Commands

### Daily Startup

```powershell
# Navigate to project
cd C:\Users\YourUsername\Downloads\fccs-mcp-ag-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server (choose one)
python -m web.server          # Web API
python -m cli.mcp_server      # MCP Server
python -m cli.main            # Interactive CLI
```

### Useful Commands

```powershell
# Check Python version
python --version

# Check installed packages
pip list

# Update dependencies
pip install --upgrade -e .

# Check server status
# Open browser: http://localhost:8080

# View logs
# Check the terminal where server is running
```

---

## Next Steps

After successful installation:

1. **Read the README:** See `README.md` for API documentation
2. **Explore Tools:** Check available FCCS tools at http://localhost:8080/tools
3. **Test Connection:** Run `python scripts\test_connection.py`
4. **Configure Claude Desktop:** Follow Step 9 above
5. **Read Documentation:**
   - `WINDOWS_DEPLOYMENT.md` - Advanced deployment options
   - `GITHUB_SETUP.md` - Repository management
   - `CHATGPT_QUICK_START.md` - ChatGPT integration

---

## Support

If you encounter issues not covered in this guide:

1. Check the troubleshooting section above
2. Review `WINDOWS_DEPLOYMENT.md` for detailed information
3. Check GitHub Issues (if repository is public)
4. Review server logs for error messages

---

## Summary Checklist

- [ ] Python 3.10+ installed and verified
- [ ] Git installed and verified
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] `.env` file created and configured
- [ ] Database initialized (if using PostgreSQL)
- [ ] Installation verified
- [ ] Server started successfully
- [ ] Claude Desktop configured (optional)

**Congratulations! Your FCCS MCP Server is now installed and ready to use! 🎉**

