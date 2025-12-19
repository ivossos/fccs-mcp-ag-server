# Project Dependencies

Complete list of all dependencies for the FCCS MCP Server project.

## Core Dependencies (from pyproject.toml)

### Required Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-adk` | >=1.0.0 | Google Agent Development Kit (core agent framework) |
| `mcp` | >=1.0.0 | Model Context Protocol (for Claude Desktop integration) |
| `pydantic-settings` | >=2.0.0 | Configuration management with environment variables |
| `httpx` | >=0.27.0 | Async HTTP client for FCCS REST API calls |
| `sqlalchemy` | >=2.0.0 | ORM for PostgreSQL database operations |
| `psycopg[binary]` | >=3.1.0 | PostgreSQL database adapter |
| `python-docx` | >=1.1.0 | Word document generation |
| `fastapi` | >=0.115.0 | Web framework for REST API |
| `uvicorn` | >=0.32.0 | ASGI server for FastAPI |

### Development Dependencies (Optional)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.0.0 | Testing framework |
| `pytest-asyncio` | >=0.24.0 | Async test support |
| `pytest-cov` | >=5.0.0 | Test coverage reporting |

### Build System

| Package | Purpose |
|---------|---------|
| `hatchling` | Build backend for Python packaging |

## Additional Dependencies (Used in Scripts)

These are used in various scripts but not in core application:

| Package | Purpose | Used In |
|---------|---------|---------|
| `reportlab` | PDF generation | `scripts/generate_analysis_pdf.py` |
| `streamlit` | Web dashboard | `dashboard.py` |
| `pandas` | Data manipulation | `dashboard.py`, analysis scripts |
| `plotly` | Interactive charts | `dashboard.py` |

## System Dependencies (Docker)

From `Dockerfile`:

- `gcc` - C compiler (for building Python packages)
- `postgresql-client` - PostgreSQL client tools

## Python Version

- **Minimum:** Python 3.10
- **Recommended:** Python 3.11+

## Installation

### Install Core Dependencies

```bash
# Using pip
pip install -e .

# Or install specific groups
pip install -e ".[dev]"  # Include dev dependencies
```

### Install Additional Script Dependencies

```bash
# For PDF generation
pip install reportlab

# For dashboard
pip install streamlit pandas plotly
```

### Complete Installation

```bash
# Core dependencies
pip install -e .

# Script dependencies
pip install reportlab streamlit pandas plotly
```

## Dependency Tree

```
fccs-mcp-ag-server
├── google-adk (Agent framework)
├── mcp (MCP protocol)
├── pydantic-settings (Config)
├── httpx (HTTP client)
│   └── httpcore
│       └── h11, h2, sniffio
├── sqlalchemy (ORM)
│   └── greenlet, typing-extensions
├── psycopg[binary] (PostgreSQL)
├── python-docx (Word docs)
│   └── lxml
├── fastapi (Web framework)
│   ├── starlette
│   ├── pydantic
│   └── typing-extensions
└── uvicorn (ASGI server)
    ├── httptools
    ├── uvloop
    └── websockets
```

## Version Compatibility

### Tested Versions

- Python: 3.10, 3.11, 3.12
- PostgreSQL: 12+, 13, 14, 15, 16
- FastAPI: 0.115.0+
- SQLAlchemy: 2.0.0+

## Cloud Run Deployment

When deploying to Cloud Run, all dependencies are installed via:

```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .
```

This installs all dependencies from `pyproject.toml`.

## Generating requirements.txt (Optional)

If you need a `requirements.txt` file:

```bash
pip install pip-tools
pip-compile pyproject.toml
```

Or manually:

```bash
pip freeze > requirements.txt
```

## Dependency Updates

### Check for Updates

```bash
pip list --outdated
```

### Update All Dependencies

```bash
pip install --upgrade -e .
```

### Update Specific Package

```bash
pip install --upgrade package-name
```

## Security

### Check for Vulnerabilities

```bash
pip install safety
safety check
```

### Audit Dependencies

```bash
pip-audit
```

## Summary

**Total Core Dependencies:** 9  
**Total Dev Dependencies:** 3  
**Total Script Dependencies:** 4  
**System Dependencies:** 2  

**Total:** 18 packages (excluding transitive dependencies)











