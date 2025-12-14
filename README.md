# FCCS MCP Agentic Server

Oracle EPM Cloud Financial Consolidation and Close (FCCS) agentic server using Google ADK with MCP support.

## Features

- **25+ FCCS Tools**: Full coverage of Oracle FCCS REST API
- **Dual Mode**: MCP server (Claude Desktop) + Web API (FastAPI)
- **Memory & Feedback**: PostgreSQL persistence with RL tracking
- **Mock Mode**: Development without real FCCS connection
- **Bilingual**: English and Portuguese support

## Quick Start

### Windows (Recommended)

**Automated Setup:**
```powershell
.\setup-windows.bat
```

This will:
- Create virtual environment
- Install all dependencies
- Create `.env` file from template
- Guide you through configuration

**Manual Setup:**
1. Create virtual environment: `python -m venv venv`
2. Activate: `.\venv\Scripts\Activate.ps1`
3. Install: `pip install -e .`
4. Configure: Copy `.env.example` to `.env` and edit
5. Initialize database: `python scripts\init_db.py` (if using PostgreSQL)

**Quick Commands:**
- Start web server: `.\start-server.bat`
- Start MCP server: `.\start-mcp-server.bat`
- Install dependencies: `.\install-dependencies.bat`
- Initialize database: `.\init-database.bat`

See [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md) for detailed Windows setup guide.

### Linux/Mac

**1. Install Dependencies:**
```bash
pip install -e .
```

**2. Configure Environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

**3. Run:**

**MCP Server (for Claude Desktop):**
```bash
python -m cli.mcp_server
```

**Web Server (for API access):**
```bash
python -m web.server
```

**Interactive CLI:**
```bash
python -m cli.main
```

## Claude Desktop Configuration

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

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

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/tools` | GET | List available tools |
| `/execute` | POST | Execute a tool |
| `/tools/{name}` | POST | Call specific tool |
| `/feedback` | POST | Submit user feedback |
| `/metrics` | GET | Get tool metrics |

## Available Tools

### Application
- `get_application_info` - FCCS application details
- `get_rest_api_version` - API version info

### Jobs
- `list_jobs` - List recent jobs
- `get_job_status` - Job status by ID
- `run_business_rule` - Execute business rules
- `run_data_rule` - Execute data load rules

### Dimensions
- `get_dimensions` - List all dimensions
- `get_members` - Get dimension members
- `get_dimension_hierarchy` - Build hierarchy tree

### Journals
- `get_journals` - List journals
- `get_journal_details` - Journal details
- `perform_journal_action` - Approve, reject, post
- `update_journal_period` - Update period
- `export_journals` / `import_journals`

### Data
- `export_data_slice` - Export grid data
- `smart_retrieve` - Smart data retrieval
- `copy_data` / `clear_data`

### Reports
- `generate_report` - Generate FCCS reports
- `get_report_job_status` - Async report status

### Consolidation
- `export_consolidation_rulesets` / `import_consolidation_rulesets`
- `validate_metadata`
- `generate_intercompany_matching_report`
- `import_supplementation_data`
- `deploy_form_template`

## Architecture

```
fccs-mcp-ag-server/
├── fccs_agent/           # Main package
│   ├── agent.py          # Agent orchestration
│   ├── config.py         # Configuration
│   ├── client/           # FCCS HTTP client
│   ├── tools/            # 25+ tool modules
│   └── services/         # Feedback service
├── cli/                  # CLI & MCP server
│   ├── main.py           # Interactive CLI
│   └── mcp_server.py     # MCP stdio server
└── web/                  # FastAPI server
    └── server.py
```

## Deployment

### Windows

See [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md) for complete Windows deployment guide including:
- Prerequisites installation
- Automated setup scripts
- Windows Service configuration
- Troubleshooting

### Docker

```bash
docker build -t fccs-agent .
docker run -p 8080:8080 --env-file .env fccs-agent
```

### Google Cloud Run

```bash
gcloud run deploy fccs-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FCCS_MOCK_MODE=true
```

See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for detailed Cloud Run deployment.

## Feedback System

The agent tracks tool executions for reinforcement learning:

- **Automatic**: Execution time, success/failure, errors
- **User Feedback**: 1-5 rating via `/feedback` endpoint
- **Metrics**: Aggregated stats via `/metrics` endpoint

## Documentation

- [Windows Deployment Guide](WINDOWS_DEPLOYMENT.md) - Complete Windows setup
- [GitHub Setup Guide](GITHUB_SETUP.md) - Repository setup and configuration
- [Quick Deploy](QUICK_DEPLOY.md) - Google Cloud Run deployment
- [ChatGPT Quick Start](CHATGPT_QUICK_START.md) - ChatGPT integration
- [Dashboard Quick Start](DASHBOARD_QUICKSTART.md) - Performance dashboard

## License

MIT
