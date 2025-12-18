# API Validation Report

- Generated: 2025-12-15T13:25:54Z
- Base URL: `http://localhost:8080`
- curl: `curl`

| Test | Method | Path | Status | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Health check | GET | /health | 200 | 0.209 | ✅ |  |
| List tools | GET | /tools | 200 | 0.224 | ✅ |  |
| MCP tools/list | POST | /message | 200 | 0.226 | ✅ |  |
| Execute tool | POST | /execute | 200 | 1.568 | ✅ |  |

## Health check

- Request: `GET /health`
- Status: 200
- Duration: 0.209s
- curl exit code: 0

Response snippet:

```json
{
  "status": "healthy",
  "mock_mode": false
}
```

## List tools

- Request: `GET /tools`
- Status: 200
- Duration: 0.224s
- curl exit code: 0

Response snippet:

```json
{
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
        "required": [
          "job_id"
        ]
      }
    },
    {
      "name": "run_business_rule",
      "des
... [truncated] ...
```

## MCP tools/list

- Request: `POST /message`
- Status: 200
- Duration: 0.226s
- curl exit code: 0

Response snippet:

```json
{
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
        "required": [
          "job_id"
        ]
      }
    },
    {
      "name": "run_business_rule",
      "des
... [truncated] ...
```

## Execute tool

- Request: `POST /execute`
- Status: 200
- Duration: 1.568s
- curl exit code: 0

Response snippet:

```json
{
  "status": "success",
  "data": {
    "links": [
      {
        "href": "https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443/HyperionPlanning/rest/v3/applications/",
        "action": "GET",
        "rel": "self"
      }
    ],
    "items": [
      {
        "name": "Consol",
        "type": "HP",
        "dpEnabled": false,
        "unicode": true,
        "appStorage": "Multidim",
        "appType": "FCCS",
        "webBotDetails": "{\"channelId\":\"\",\"serviceUri\":\"\"}",
        "helpServerUrl": "https://www.oracle.com",
        "workpaceServerUrl": "https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443",
        "theme": "REDWOOD_ORACLE_R13",
        "adminMode": false,
        "hybrid": true,
        "oglApplicationId": "",
        "oglServerUrl": "https://guidedlearning.oracle.com"
      }
    ],
    "type": "HP"
  },
  "error": null
}
```

