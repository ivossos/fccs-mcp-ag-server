# Deployment Checklist

Use this checklist to ensure a successful deployment on Windows.

## Pre-Deployment

### Environment Setup
- [ ] Python 3.10+ installed and in PATH
- [ ] Git installed (for version control)
- [ ] PostgreSQL installed (for production) OR SQLite ready (for development)
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -e .`)

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `FCCS_MOCK_MODE` set appropriately (true for dev, false for prod)
- [ ] `DATABASE_URL` configured correctly
- [ ] FCCS credentials set (if not in mock mode):
  - [ ] `FCCS_URL`
  - [ ] `FCCS_USERNAME`
  - [ ] `FCCS_PASSWORD`
- [ ] `GOOGLE_API_KEY` set (if using agent features)

### Database
- [ ] PostgreSQL service running (if using PostgreSQL)
- [ ] Database created (if using PostgreSQL)
- [ ] Database schema initialized (`python scripts/init_db.py`)
- [ ] Test connection successful

### Testing
- [ ] Connection test passed (`python scripts/test_connection.py`)
- [ ] MCP server starts without errors
- [ ] Web server starts without errors
- [ ] Health endpoint responds (`http://localhost:8080/`)
- [ ] Tools endpoint accessible (`http://localhost:8080/tools`)

## GitHub Repository Setup

### Initial Setup
- [ ] Git repository initialized (`git init`)
- [ ] `.gitignore` file configured
- [ ] Initial commit created
- [ ] GitHub repository created
- [ ] Remote added (`git remote add origin ...`)
- [ ] Code pushed to GitHub

### Repository Configuration
- [ ] README.md updated
- [ ] LICENSE file added (optional)
- [ ] Repository description set
- [ ] Topics/tags added
- [ ] Branch protection rules configured (optional)
- [ ] GitHub Actions CI/CD configured (optional)

## Production Deployment

### Security
- [ ] `.env` file not committed to git
- [ ] Secrets stored securely (environment variables or secret manager)
- [ ] Database credentials secured
- [ ] API keys secured
- [ ] Firewall rules configured (if needed)

### Monitoring
- [ ] Logging configured
- [ ] Error tracking set up (optional)
- [ ] Health check endpoint accessible
- [ ] Metrics endpoint accessible

### Service Configuration
- [ ] Windows Service installed (if using NSSM)
- [ ] Service starts automatically on boot
- [ ] Service runs with appropriate user permissions
- [ ] Log rotation configured

### Backup
- [ ] Database backup strategy in place
- [ ] Configuration backup strategy in place
- [ ] Recovery procedure documented

## Post-Deployment

### Verification
- [ ] Server responds to requests
- [ ] All tools accessible
- [ ] Database connections working
- [ ] FCCS connection working (if not in mock mode)
- [ ] Logs show no errors

### Documentation
- [ ] Deployment procedure documented
- [ ] Troubleshooting guide available
- [ ] Contact information for support
- [ ] Rollback procedure documented

### Maintenance
- [ ] Update schedule established
- [ ] Monitoring alerts configured
- [ ] Backup verification scheduled
- [ ] Security updates process defined

## Quick Commands Reference

```powershell
# Setup
.\setup-windows.bat

# Start servers
.\start-server.bat
.\start-mcp-server.bat

# Database
.\init-database.bat
python scripts\init_db.py

# Testing
python scripts\test_connection.py
python scripts\show_cache_status.py

# Git
git status
git add .
git commit -m "Description"
git push origin main
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Python not found | Reinstall Python, check "Add to PATH" |
| Virtual env activation fails | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Port in use | Change PORT in .env or stop conflicting service |
| Database connection fails | Check PostgreSQL service, verify DATABASE_URL |
| Module not found | Activate venv, run `pip install -e .` |
| Git authentication fails | Use personal access token or configure credential helper |

## Support

- See [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md) for detailed setup
- See [GITHUB_SETUP.md](GITHUB_SETUP.md) for repository configuration
- Check logs in application directory
- Review error messages in console output










