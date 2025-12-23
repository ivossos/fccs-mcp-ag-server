# Python Scripts Quick Start Guide 🐍

## ✅ Status: Python Scripts Are Ready to Run!

Your environment is configured and ready to execute Python scripts.

## 🚀 Quick Ways to Run Python Scripts

### Method 1: Direct Python Command (Simplest)
```bash
python script_name.py
```

### Method 2: Using Helper Scripts

**PowerShell:**
```powershell
.\run_python_script.ps1 script_name.py
.\run_python_script.ps1 script_name.py arg1 arg2
```

**Command Prompt (Batch):**
```cmd
run_python_script.bat script_name.py
run_python_script.bat script_name.py arg1 arg2
```

### Method 3: Activate Virtual Environment First
```powershell
# PowerShell
.\venv\Scripts\Activate.ps1
python script_name.py
```

```cmd
# Command Prompt
venv\Scripts\activate.bat
python script_name.py
```

## 📋 Current Environment

- **Python Version:** 3.13.5
- **Python Location:** `C:\Python313\python.exe`
- **Virtual Environment:** Available at `venv\`
- **Dependencies:** Installed and working

## ✅ Verified Working Modules

- ✓ `fccs_agent` - Main agent module
- ✓ `httpx` (0.28.1) - HTTP client
- ✓ `SQLAlchemy` (2.0.45) - Database ORM

## 📝 Example Scripts Available

Here are some Python scripts you can run:

### Analysis Scripts
- `find_net_income_variance.py` - Find entities with Net Income variance >20%
- `comprehensive_entity_analysis_2024_html.py` - Generate entity analysis report
- `comprehensive_fy25_analysis_mcp_html.py` - FY25 comprehensive analysis

### Utility Scripts
- `test_python_execution.py` - Test Python environment
- `verify_feedback_tools.py` - Verify feedback system
- `quick_evaluate.py` - Quick evaluation helper
- `interactive_evaluate.py` - Interactive evaluation tool

### Dashboard Scripts
- `tool_stats_dashboard.py` - Tool statistics dashboard
- `dashboard.py` - Main dashboard

## 🔧 Troubleshooting

### Issue: "Python is not recognized"
**Solution:** 
- Ensure Python is installed and in PATH
- Check with: `python --version`
- If not found, reinstall Python and check "Add Python to PATH"

### Issue: "Module not found"
**Solution:**
- Activate virtual environment: `venv\Scripts\activate.bat`
- Install dependencies: `pip install -e .`
- Or run setup: `setup-windows.bat`

### Issue: "Permission denied" (PowerShell)
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Encoding errors
**Solution:**
- Scripts use UTF-8 encoding
- If you see encoding errors, ensure your terminal supports UTF-8
- Or use Command Prompt instead of PowerShell

## 📚 More Information

- **Setup Guide:** `WINDOWS_QUICK_START.md`
- **Deployment:** `WINDOWS_DEPLOYMENT.md`
- **Dependencies:** `pyproject.toml`

## 🎯 Quick Test

Test your Python setup:
```bash
python test_python_execution.py
```

This will verify:
- Python version
- Module imports
- Environment configuration

---

**Ready to run scripts?** Just use: `python script_name.py` 🚀



