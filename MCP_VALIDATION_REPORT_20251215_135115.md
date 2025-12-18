# MCP Server Validation Report

- Generated: 2025-12-15T13:51:28Z
- Python: `.\venv\Scripts\python.exe`
- Test Tool: `get_application_info`

| Test | Method | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- |
| List tools | tools/list | 0.006 | ✅ |  |
| Call tool: get_application_info | tools/call | 3.906 | ✅ |  |
| Call tool: get_rest_api_version | tools/call | 1.298 | ✅ |  |
| Call tool: get_dimensions | tools/call | 2.302 | ✅ |  |
| Call tool: list_jobs | tools/call | 0.678 | ✅ |  |

## List tools

- Method: `tools/list`
- Duration: 0.006s

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

## Call tool: get_application_info

- Method: `tools/call`
- Params: `{
  "name": "get_application_info",
  "arguments": {}
}`
- Duration: 3.906s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"status\": \"success\",\n  \"data\": {\n    \"links\": [\n      {\n        \"href\": \"https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443/HyperionPlanning/rest/v3/applications/\",\n        \"action\": \"GET\",\n        \"rel\": \"self\"\n      }\n    ],\n    \"items\": [\n      {\n        \"name\": \"Consol\",\n        \"type\": \"HP\",\n        \"dpEnabled\": false,\n        \"unicode\": true,\n        \"appStorage\": \"Multidim\",\n        \"appType\": \"FCCS\",\n        \"webBotDetails\": \"{\\\"channelId\\\":\\\"\\\",\\\"serviceUri\\\":\\\"\\\"}\",\n        \"helpServerUrl\": \"https://www.oracle.com\",\n        \"workpaceServerUrl\": \"https://venturisupply-venturisupply2024.epm.us-phoenix-1.ocs.oraclecloud.com:443\",\n        \"theme\": \"REDWOOD_ORACLE_R13\",\n        \"adminMode\": false,\n        \"hybrid\": true,\n        \"oglApplicationId\": \"\",\n        \"oglServerUrl\": \"https://guidedlearning.oracle.com\"\n      }\n    ],\n    \"type\": \"HP\"\n  },\n  \"rl_metadata\": {\n    \"confidence\": 0.6813
... [truncated] ...
```

## Call tool: get_rest_api_version

- Method: `tools/call`
- Params: `{
  "name": "get_rest_api_version",
  "arguments": {}
}`
- Duration: 1.298s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"status\": \"success\",\n  \"data\": {\n    \"version\": \"v3\",\n    \"note\": \"Version endpoint not available, using configured version\"\n  },\n  \"rl_metadata\": {\n    \"confidence\": 0.5494054631270707,\n    \"context_hash\": \"9866b834d3f42a4b158a3a9ea327f12c9443f661bb8b02fad57c272775190e2c\"\n  }\n}"
      }
    ],
    "isError": false
  }
}
```

## Call tool: get_dimensions

- Method: `tools/call`
- Params: `{
  "name": "get_dimensions",
  "arguments": {}
}`
- Duration: 2.302s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"status\": \"success\",\n  \"data\": {\n    \"items\": [\n      {\n        \"name\": \"Years\",\n        \"type\": \"Time\"\n      },\n      {\n        \"name\": \"Period\",\n        \"type\": \"Time\"\n      },\n      {\n        \"name\": \"Scenario\",\n        \"type\": \"Scenario\"\n      },\n      {\n        \"name\": \"View\",\n        \"type\": \"View\"\n      },\n      {\n        \"name\": \"Entity\",\n        \"type\": \"Entity\"\n      },\n      {\n        \"name\": \"Consolidation\",\n        \"type\": \"Consolidation\"\n      },\n      {\n        \"name\": \"Account\",\n        \"type\": \"Account\"\n      },\n      {\n        \"name\": \"ICP\",\n        \"type\": \"ICP\"\n      },\n      {\n        \"name\": \"Data Source\",\n        \"type\": \"Data Source\"\n      },\n      {\n        \"name\": \"Movement\",\n        \"type\": \"Movement\"\n      },\n      {\n        \"name\": \"Multi-GAAP\",\n        \"type\": \"Multi-GAAP\"\n      }\n    ],\n    \"note\": \"Standard FCCS dimensions (endpoint not available)\"\n  },\n  \"rl_metadat
... [truncated] ...
```

## Call tool: list_jobs

- Method: `tools/call`
- Params: `{
  "name": "list_jobs",
  "arguments": {}
}`
- Duration: 0.678s

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"status\": \"success\",\n  \"data\": {\n    \"items\": []\n  },\n  \"rl_metadata\": {\n    \"confidence\": 0.5595417728334021,\n    \"context_hash\": \"394893f61385befba420f6d6e12715aff54700c898b8b0717809ff7c56e92d5f\"\n  }\n}"
      }
    ],
    "isError": false
  }
}
```

