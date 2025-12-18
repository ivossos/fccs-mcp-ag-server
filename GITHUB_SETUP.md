# GitHub Repository Setup Guide

This guide will help you create and configure the GitHub repository for the FCCS MCP Agentic Server.

## Prerequisites

- Git installed on your Windows machine
- GitHub account
- GitHub CLI (optional, but recommended) or access to GitHub web interface

## Step 1: Initialize Git Repository

If you haven't already initialized git in your project:

```powershell
# Navigate to project directory
cd C:\Users\ivoss\Downloads\Projetos\agentic\fccs-mcp-ag-server

# Initialize git repository
git init

# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: FCCS MCP Agentic Server"
```

## Step 2: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended)

```powershell
# Install GitHub CLI if not already installed
# Download from: https://cli.github.com/

# Authenticate
gh auth login

# Create repository
gh repo create fccs-mcp-ag-server `
  --public `
  --description "Oracle FCCS Agentic MCP Server using Google ADK" `
  --source=. `
  --remote=origin `
  --push
```

### Option B: Using GitHub Web Interface

1. **Go to GitHub:**
   - Visit [github.com](https://github.com)
   - Click the "+" icon in the top right
   - Select "New repository"

2. **Repository Settings:**
   - **Name:** `fccs-mcp-ag-server`
   - **Description:** `Oracle FCCS Agentic MCP Server using Google ADK`
   - **Visibility:** Public or Private (your choice)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. **Click "Create repository"**

4. **Connect local repository:**
   ```powershell
   # Add remote (replace YOUR_USERNAME with your GitHub username)
   git remote add origin https://github.com/YOUR_USERNAME/fccs-mcp-ag-server.git

   # Rename default branch to main (if needed)
   git branch -M main

   # Push to GitHub
   git push -u origin main
   ```

## Step 3: Verify Repository

```powershell
# Check remote configuration
git remote -v

# Verify files are pushed
git log --oneline
```

## Step 4: Configure Repository Settings

### On GitHub Web Interface:

1. **Go to repository settings:**
   - Navigate to your repository
   - Click "Settings" tab

2. **Configure Secrets (for CI/CD):**
   - Go to "Secrets and variables" > "Actions"
   - Add secrets if needed for automated deployments:
     - `FCCS_URL`
     - `FCCS_USERNAME`
     - `FCCS_PASSWORD`
     - `GOOGLE_API_KEY`
     - `DATABASE_URL`

3. **Configure Branch Protection (optional):**
   - Go to "Branches"
   - Add rule for `main` branch
   - Require pull request reviews (optional)

4. **Add Topics/Tags:**
   - Go to repository main page
   - Click the gear icon next to "About"
   - Add topics: `oracle-epm`, `fccs`, `mcp`, `python`, `fastapi`, `claude-desktop`

5. **Add Description:**
   - Update description if needed
   - Add website URL if applicable

## Step 5: Create Additional Files (Optional)

### LICENSE File

If you want to add a license:

```powershell
# Create MIT License file
@"
MIT License

Copyright (c) 2024 FCCS Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@ | Out-File -FilePath LICENSE -Encoding utf8
```

### CONTRIBUTING.md (Optional)

Create a contributing guide if you want to accept contributions.

## Step 6: Set Up GitHub Actions (Optional)

Create `.github/workflows/ci.yml` for continuous integration:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    
    - name: Run tests
      run: |
        pytest tests/
```

## Step 7: Create Release (Optional)

For version releases:

```powershell
# Tag a release
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0

# Or use GitHub CLI
gh release create v0.1.0 --title "v0.1.0" --notes "Initial release"
```

## Step 8: Verify Everything

1. **Check repository on GitHub:**
   - Visit your repository URL
   - Verify all files are present
   - Check README displays correctly

2. **Test cloning:**
   ```powershell
   # Clone to a different location to test
   cd C:\temp
   git clone https://github.com/YOUR_USERNAME/fccs-mcp-ag-server.git test-clone
   cd test-clone
   # Verify it works
   ```

## Common Commands

### Daily Workflow

```powershell
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

### Branch Management

```powershell
# Create feature branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### Tagging Releases

```powershell
# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push tags
git push origin v0.2.0

# List tags
git tag
```

## Troubleshooting

### Authentication Issues

**Error:** `fatal: could not read Username`

**Solution:**
```powershell
# Use personal access token instead of password
# Or configure credential helper
git config --global credential.helper wincred
```

### Large Files

**Error:** File too large for GitHub

**Solution:**
- Add to `.gitignore`
- Use Git LFS for large files:
  ```powershell
  git lfs install
  git lfs track "*.pdf"
  git add .gitattributes
  ```

### Merge Conflicts

**Solution:**
```powershell
# Pull latest changes
git pull origin main

# Resolve conflicts in files
# Then:
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

## Next Steps

- Set up GitHub Actions for CI/CD
- Configure branch protection rules
- Add collaborators
- Create issues and project board
- Set up automated releases

## Repository Checklist

- [x] Git repository initialized
- [x] .gitignore configured
- [x] README.md created
- [x] LICENSE file (optional)
- [x] GitHub repository created
- [x] Remote added and pushed
- [x] Repository settings configured
- [ ] GitHub Actions CI/CD (optional)
- [ ] Branch protection rules (optional)
- [ ] Release tags created (optional)










