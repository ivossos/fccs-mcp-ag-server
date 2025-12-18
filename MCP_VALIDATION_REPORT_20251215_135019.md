# MCP Server Validation Report

- Generated: 2025-12-15T13:50:31Z
- Python: `.\venv\Scripts\python.exe`
- Test Tool: `get_application_info`

| Test | Method | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- |
| List tools | tools/list | 0.007 | ✅ |  |
| Call tool | tools/call | 4.999 | ✅ |  |

## List tools

- Method: `tools/list`
- Duration: 0.007s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_application_info",
        "description": "Get information about the FCCS application / Obter informacoes sobre a aplicacao FCCS",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      },
      {
        "name": "get_rest_api_version",
        "description": "Get the REST API version / Obter a versao da API REST",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      },
      {
        "name": "list_jobs",
        "description": "List recent jobs in the FCCS application / Listar jobs recentes na aplicacao FCCS",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      },
      {
        "name": "get_job_status",
        "description": "Get the status of a specific job / Obter o status de um job especifico",
        "inputSchema": {
          "type": "object",
          "properties": {
            "job_id": {
              "type": "string",
              "description": "The ID of the job to check / O ID do job para verificar"
            }
          },

... [truncated] ...
```

## Call tool

- Method: `tools/call`
- Params: `{
  "name": "get_application_info",
  "arguments": {}
}`
- Duration: 4.999s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"status\": \"success\",\n  \"data\": {\n    \"links\": [\n      {\n        \"href\": \"https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443/HyperionPlanning/rest/v3/applications/\",\n        \"action\": \"GET\",\n        \"rel\": \"self\"\n      }\n    ],\n    \"items\": [\n      {\n        \"name\": \"Consol\",\n        \"type\": \"HP\",\n        \"dpEnabled\": false,\n        \"unicode\": true,\n        \"appStorage\": \"Multidim\",\n        \"appType\": \"FCCS\",\n        \"webBotDetails\": \"{\\\"channelId\\\":\\\"\\\",\\\"serviceUri\\\":\\\"\\\"}\",\n        \"helpServerUrl\": \"https://www.oracle.com\",\n        \"workpaceServerUrl\": \"https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443\",\n        \"theme\": \"REDWOOD_ORACLE_R13\",\n        \"adminMode\": false,\n        \"hybrid\": true,\n        \"oglApplicationId\": \"\",\n        \"oglServerUrl\": \"https://guidedlearning.oracle.com\"\n      }\n    ],\n    \"type\": \"HP\"\n  },\n  \"rl_metadata\": {\n    \"confidence\": 0.6406
... [truncated] ...
```

