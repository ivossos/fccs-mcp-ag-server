# How to Restart the MCP Server

## Manual Restart Commands

### Option 1: Using Python Module (Recommended)
```bash
python -m cli.mcp_server
```

### Option 2: Direct Python Execution
```bash
python cli/mcp_server.py
```

## Steps to Restart

1. **Stop the current server** (if running):
   - Press `Ctrl+C` in the terminal where it's running
   - Or close the terminal window

2. **Clear cache** (optional but recommended):
   ```bash
   python scripts/clear_cache.py
   ```

3. **Start the server**:
   ```bash
   python -m cli.mcp_server
   ```

## For Claude Desktop Users

If you're using Claude Desktop with MCP integration:

1. **Close Claude Desktop completely**
2. **Restart Claude Desktop**
3. The MCP server will automatically start when Claude Desktop connects

## Verify It's Working

After restarting, you can test with:
```bash
python scripts/test_connection.py
```

Or test the feedback service:
```bash
python scripts/test_feedback_service.py
```

## Troubleshooting

If you see import errors or the old code is still running:

1. Clear all Python cache:
   ```bash
   python scripts/clear_cache.py
   ```

2. Make sure you're in the project directory:
   ```bash
   cd C:\Users\ivoss\Downloads\Projetos\agentic\fccs-mcp-ag-server
   ```

3. Verify the fix is in place:
   ```bash
   python -c "from fccs_agent.services.feedback_service import FeedbackService; print('Fix loaded successfully')"
   ```


