# GitHub Repository Setup Script
# This script helps you create and push to a GitHub repository

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "[ERROR] Git is not installed" -ForegroundColor Red
    Write-Host "Install from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Git is installed" -ForegroundColor Green
Write-Host ""

# Check current branch
$currentBranch = git branch --show-current
if (-not $currentBranch) {
    Write-Host "Setting default branch to 'main'..." -ForegroundColor Yellow
    git branch -M main
    $currentBranch = "main"
}

Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan
Write-Host ""

# Check if remote already exists
$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Host "[INFO] Remote 'origin' already exists: $remoteExists" -ForegroundColor Yellow
    Write-Host ""
    $useExisting = Read-Host "Do you want to use this remote? (Y/n)"
    if ($useExisting -eq "n" -or $useExisting -eq "N") {
        git remote remove origin
        $remoteExists = $null
    }
}

if (-not $remoteExists) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Create GitHub Repository First" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Go to: https://github.com/new" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Repository settings:" -ForegroundColor Yellow
    Write-Host "   - Name: fccs-mcp-ag-server" -ForegroundColor White
    Write-Host "   - Description: Oracle FCCS Agentic MCP Server using Google ADK" -ForegroundColor White
    Write-Host "   - Visibility: Public or Private (your choice)" -ForegroundColor White
    Write-Host "   - DO NOT initialize with README, .gitignore, or license" -ForegroundColor Red
    Write-Host ""
    Write-Host "3. Click 'Create repository'" -ForegroundColor Yellow
    Write-Host ""
    
    $githubUsername = Read-Host "Enter your GitHub username"
    $repoName = Read-Host "Enter repository name (default: fccs-mcp-ag-server)" 
    if ([string]::IsNullOrWhiteSpace($repoName)) {
        $repoName = "fccs-mcp-ag-server"
    }
    
    $isPrivate = Read-Host "Is the repository private? (y/N)"
    $protocol = Read-Host "Use HTTPS or SSH? (HTTPS/SSH, default: HTTPS)"
    if ([string]::IsNullOrWhiteSpace($protocol)) {
        $protocol = "HTTPS"
    }
    
    if ($protocol -eq "HTTPS" -or $protocol -eq "https") {
        $remoteUrl = "https://github.com/$githubUsername/$repoName.git"
    } else {
        $remoteUrl = "git@github.com:$githubUsername/$repoName.git"
    }
    
    Write-Host ""
    Write-Host "Adding remote: $remoteUrl" -ForegroundColor Green
    git remote add origin $remoteUrl
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to add remote" -ForegroundColor Red
        exit 1
    }
}

# Rename branch to main if needed
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch to 'main'..." -ForegroundColor Yellow
    git branch -M main
}

# Check if there are commits to push
$commitsToPush = git log origin/$currentBranch..$currentBranch 2>$null
if (-not $commitsToPush) {
    $localCommits = git log --oneline -1
    Write-Host "[INFO] No commits to push (or remote doesn't exist yet)" -ForegroundColor Yellow
    Write-Host "Local commit: $localCommits" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to Push" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Remote URL: $(git remote get-url origin)" -ForegroundColor Cyan
Write-Host "Branch: $currentBranch" -ForegroundColor Cyan
Write-Host ""

$push = Read-Host "Push to GitHub now? (Y/n)"
if ($push -ne "n" -and $push -ne "N") {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    git push -u origin $currentBranch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Success! Repository pushed to GitHub" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        $repoUrl = git remote get-url origin
        $repoUrl = $repoUrl -replace '\.git$', ''
        $repoUrl = $repoUrl -replace 'git@github\.com:', 'https://github.com/'
        $repoUrl = $repoUrl -replace '^https://github\.com/', 'https://github.com/'
        Write-Host "Repository URL: $repoUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Visit your repository on GitHub" -ForegroundColor White
        Write-Host "2. Add repository description and topics" -ForegroundColor White
        Write-Host "3. Configure branch protection (optional)" -ForegroundColor White
        Write-Host "4. Set up GitHub Actions (optional)" -ForegroundColor White
        Write-Host ""
        Write-Host "See GITHUB_SETUP.md for more details" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "1. Authentication required - use personal access token" -ForegroundColor White
        Write-Host "2. Repository doesn't exist - create it on GitHub first" -ForegroundColor White
        Write-Host "3. Network issues - check your internet connection" -ForegroundColor White
        Write-Host ""
        Write-Host "To configure credentials:" -ForegroundColor Yellow
        Write-Host "  git config --global credential.helper wincred" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "To push manually, run:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor White
}

Write-Host ""











