# Gmail MCP Server Setup

This guide will help you set up a Gmail MCP server for use with Cursor.

## Option 1: Using Official MCP Gmail Server (Recommended)

### Prerequisites
1. Node.js installed on your system
2. Gmail API credentials (OAuth 2.0)

### Setup Steps

1. **Enable Gmail API and Create Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download the credentials JSON file

2. **Set Environment Variables:**

   There are two ways to set environment variables in Windows:

   **Method A: Temporary (Current PowerShell Session Only)**
   
   Open PowerShell and run:
   ```powershell
   # Set the path to your Gmail credentials JSON file
   $env:GMAIL_CREDENTIALS_PATH = "C:\path\to\credentials.json"
   $env:GMAIL_TOKEN_PATH = "C:\path\to\token.json"
   ```
   
   ⚠️ **Note:** These will be lost when you close PowerShell. Use Method B for permanent setup.

   **Method B: Permanent (User-Level - Recommended)**
   
   Open PowerShell as Administrator and run:
   ```powershell
   # Set user-level environment variables (persists across sessions)
   [System.Environment]::SetEnvironmentVariable("GMAIL_CREDENTIALS_PATH", "C:\path\to\credentials.json", "User")
   [System.Environment]::SetEnvironmentVariable("GMAIL_TOKEN_PATH", "C:\path\to\token.json", "User")
   ```
   
   **Or use Windows GUI:**
   1. Press `Win + R`, type `sysdm.cpl`, press Enter
   2. Click "Environment Variables"
   3. Under "User variables", click "New"
   4. Add:
      - Variable name: `GMAIL_CREDENTIALS_PATH`
      - Variable value: `C:\path\to\credentials.json`
   5. Repeat for `GMAIL_TOKEN_PATH`

   **Verify the variables are set:**
   ```powershell
   # Check if variables are set
   $env:GMAIL_CREDENTIALS_PATH
   $env:GMAIL_TOKEN_PATH
   
   # Or check all environment variables
   Get-ChildItem Env: | Where-Object Name -like "GMAIL*"
   ```

   **Important:** After setting permanent variables, restart Cursor for them to take effect.

3. **Generate OAuth Token:**
   
   You need to generate an OAuth token using your credentials. See **GMAIL_TOKEN_GUIDE.md** for detailed instructions.
   
   **Quick method:**
   ```powershell
   # Install required packages
   pip install -r requirements-gmail.txt
   
   # Run the token generator
   python get-gmail-token.py
   ```
   
   This will:
   - Open a browser for you to sign in to Google
   - Ask for permission to access Gmail
   - Save the token to the file you specify
   
   **Note:** The token file will be created automatically during this process.

## Option 2: Using Python-based Gmail MCP Server

If the npm package doesn't work, you can use a Python-based implementation:

### Update `.cursor/gmail.mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": [
        "-m",
        "gmail_mcp_server"
      ],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "${GMAIL_CREDENTIALS_PATH}",
        "GMAIL_TOKEN_PATH": "${GMAIL_TOKEN_PATH}"
      }
    }
  }
}
```

### Install Python Gmail MCP Server:
```bash
pip install gmail-mcp-server
```

## Option 3: Custom Gmail MCP Server

You can also create a custom Gmail MCP server using the Gmail API. The configuration would look like:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": [
        "path/to/your/gmail_mcp_server.py"
      ],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "${GMAIL_CREDENTIALS_PATH}",
        "GMAIL_TOKEN_PATH": "${GMAIL_TOKEN_PATH}"
      }
    }
  }
}
```

## Configuration File Location

The Gmail MCP configuration is located at:
- `.cursor/gmail.mcp.json`

Cursor will automatically detect and load this configuration.

## Troubleshooting

1. **If the npm package doesn't exist:**
   - Try using Option 2 or 3 above
   - Check the [Model Context Protocol GitHub](https://github.com/modelcontextprotocol) for official Gmail servers

2. **Authentication Issues:**
   - Make sure you've enabled the Gmail API in Google Cloud Console
   - Verify your OAuth credentials are correct
   - Check that the token file path is writable

3. **Environment Variables:**
   - Use absolute paths for credential files
   - Ensure the paths exist and are accessible

## Testing the Connection

After setup, restart Cursor and the Gmail MCP server should be available. You can test it by asking Cursor to:
- Read emails from your Gmail
- Search for specific emails
- Send emails through Gmail

