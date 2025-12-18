# API Validation Report

- Generated: 2025-12-15T13:30:59Z
- Base URL: `http://localhost:8080`
- curl: `curl`

| Test | Method | Path | Status | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Root | GET | / | 200 | 0.221 | ✅ |  |
| Health check | GET | /health | 200 | 0.217 | ✅ |  |
| List tools | GET | /tools | 200 | 0.219 | ✅ |  |
| MCP tools/list | POST | /message | 200 | 0.214 | ✅ |  |
| Call tool via /tools/{tool_name} | POST | /tools/get_application_info | 200 | 1.816 | ✅ |  |
| Execute tool | POST | /execute | 200 | 0.965 | ✅ |  |
| Execute tool with RL | POST | /execute/rl | 200 | 0.840 | ✅ |  |
| Metrics | GET | /metrics?tool_name=get_application_info | 200 | 0.242 | ✅ |  |
| Executions | GET | /executions?tool_name=get_application_info&limit=5 | 200 | 0.231 | ✅ |  |
| Feedback | POST | /feedback | 200 | 0.223 | ✅ |  |
| RL metrics | GET | /rl/metrics | 200 | 0.221 | ✅ |  |
| RL policy for tool | GET | /rl/policy/get_application_info | 200 | 0.468 | ✅ |  |
| RL recommendations | POST | /rl/recommendations | 200 | 0.235 | ✅ |  |
| RL episodes | GET | /rl/episodes?tool_name=get_application_info&limit=5 | 500 | 0.300 | ❌ |  |
| Finalize session | POST | /sessions/validation-script/finalize?outcome=success | 200 | 0.228 | ✅ |  |
| OpenAPI schema | GET | /openapi.json | 200 | 0.258 | ✅ |  |

## Root

- Request: `GET /`
- Status: 200
- Duration: 0.221s
- curl exit code: 0

Response snippet:

```json
{
  "name": "FCCS Agent API",
  "version": "0.1.0",
  "status": "healthy",
  "mock_mode": false
}
```

## Health check

- Request: `GET /health`
- Status: 200
- Duration: 0.217s
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
- Duration: 0.219s
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
- Duration: 0.214s
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

## Call tool via /tools/{tool_name}

- Request: `POST /tools/get_application_info`
- Status: 200
- Duration: 1.816s
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

## Execute tool

- Request: `POST /execute`
- Status: 200
- Duration: 0.965s
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

## Execute tool with RL

- Request: `POST /execute/rl`
- Status: 200
- Duration: 0.840s
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

## Metrics

- Request: `GET /metrics?tool_name=get_application_info`
- Status: 200
- Duration: 0.242s
- curl exit code: 0

Response snippet:

```json
{
  "metrics": [
    {
      "tool_name": "get_application_info",
      "total_calls": 10,
      "success_rate": 1.0,
      "avg_execution_time_ms": 672.3205804824829,
      "avg_user_rating": null
    }
  ]
}
```

## Executions

- Request: `GET /executions?tool_name=get_application_info&limit=5`
- Status: 200
- Duration: 0.231s
- curl exit code: 0

Response snippet:

```json
{
  "executions": [
    {
      "id": 173,
      "session_id": "validation-script",
      "tool_name": "get_application_info",
      "success": true,
      "execution_time_ms": 352.9646396636963,
      "user_rating": null,
      "created_at": "2025-12-15T13:30:55.929917"
    },
    {
      "id": 172,
      "session_id": "validation-script",
      "tool_name": "get_application_info",
      "success": true,
      "execution_time_ms": 375.9145736694336,
      "user_rating": null,
      "created_at": "2025-12-15T13:30:54.897130"
    },
    {
      "id": 171,
      "session_id": "validation-script",
      "tool_name": "get_application_info",
      "success": true,
      "execution_time_ms": 1246.9604015350342,
      "user_rating": null,
      "created_at": "2025-12-15T13:30:53.902807"
    },
    {
      "id": 170,
      "session_id": "validation-script",
      "tool_name": "get_application_info",
      "success": true,
      "execution_time_ms": 916.40305519104,
      "user_rating": null,
      "created_at": "2025-12-15T13:25:54.161737"
    },
    {
      "id": 85,
      "session_id": "default",
      "tool_name": "get_application_info",
      "success": true,
      
... [truncated] ...
```

## Feedback

- Request: `POST /feedback`
- Status: 200
- Duration: 0.223s
- curl exit code: 0

Response snippet:

```json
{
  "status": "success"
}
```

## RL metrics

- Request: `GET /rl/metrics`
- Status: 200
- Duration: 0.221s
- curl exit code: 0

Response snippet:

```json
{
  "rl_enabled": true,
  "tool_metrics": {
    "total_tools": 9,
    "avg_success_rate": 0.573,
    "avg_user_rating": 0.0
  },
  "policy_metrics": {
    "total_policies": 4,
    "avg_action_value": 1.093
  },
  "config": {
    "exploration_rate": 0.1,
    "learning_rate": 0.1,
    "discount_factor": 0.9,
    "min_samples": 5
  }
}
```

## RL policy for tool

- Request: `GET /rl/policy/get_application_info`
- Status: 200
- Duration: 0.468s
- curl exit code: 0

Response snippet:

```json
{
  "tool_name": "get_application_info",
  "policies": [
    {
      "context_hash": "2d9e57e30054a469b0eecf1f1da55b845c4973af99e52ea92586d2b4eedf9f09",
      "action_value": 0.9908359694480897,
      "visit_count": 1,
      "last_updated": "2025-12-15T13:25:54.552747"
    },
    {
      "context_hash": "9866b834d3f42a4b158a3a9ea327f12c9443f661bb8b02fad57c272775190e2c",
      "action_value": 0.9875303959846496,
      "visit_count": 1,
      "last_updated": "2025-12-15T13:30:54.213010"
    },
    {
      "context_hash": "c1cf9060674b6966462ae52bc6a9a64aab65b939847ba6d9663e210a41d78767",
      "action_value": 1.1962408542633056,
      "visit_count": 1,
      "last_updated": "2025-12-15T13:30:55.268533"
    },
    {
      "context_hash": "f66e46b12835258eb1436a3c52f8e8220c66dbfce077d8592427f7d07d0f5c65",
      "action_value": 1.196470353603363,
      "visit_count": 1,
      "last_updated": "2025-12-15T13:30:56.188562"
    }
  ],
  "total_contexts": 4
}
```

## RL recommendations

- Request: `POST /rl/recommendations`
- Status: 200
- Duration: 0.235s
- curl exit code: 0

Response snippet:

```json
{
  "query": "validate endpoints",
  "recommendations": [
    {
      "tool_name": "get_application_info",
      "confidence": 0.85,
      "reason": "high success rate, fast execution, sufficient samples",
      "metrics": {
        "success_rate": 1.0,
        "avg_rating": null,
        "total_calls": 10
      }
    },
    {
      "tool_name": "test_tool",
      "confidence": 0.8,
      "reason": "high success rate, fast execution",
      "metrics": {
        "success_rate": 1.0,
        "avg_rating": null,
        "total_calls": 4
      }
    },
    {
      "tool_name": "list_jobs",
      "confidence": 0.8,
      "reason": "high success rate, fast execution",
      "metrics": {
        "success_rate": 1.0,
        "avg_rating": null,
        "total_calls": 2
      }
    },
    {
      "tool_name": "get_dimensions",
      "confidence": 0.75,
      "reason": "high success rate, sufficient samples",
      "metrics": {
        "success_rate": 1.0,
        "avg_rating": null,
        "total_calls": 5
      }
    },
    {
      "tool_name": "smart_retrieve",
      "confidence": 0.65,
      "reason": "fast execution, sufficient samples",
      "metrics": {
        "
... [truncated] ...
```

## RL episodes

- Request: `GET /rl/episodes?tool_name=get_application_info&limit=5`
- Status: 500
- Duration: 0.300s
- curl exit code: 0

Response snippet:

```json
Internal Server Error
```

## Finalize session

- Request: `POST /sessions/validation-script/finalize?outcome=success`
- Status: 200
- Duration: 0.228s
- curl exit code: 0

Response snippet:

```json
{
  "status": "success",
  "session_id": "validation-script",
  "outcome": "success"
}
```

## OpenAPI schema

- Request: `GET /openapi.json`
- Status: 200
- Duration: 0.258s
- curl exit code: 0

Response snippet:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "FCCS Agent API",
    "description": "Oracle FCCS Agentic MCP Server API",
    "version": "0.1.0"
  },
  "paths": {
    "/": {
      "get": {
        "summary": "Root",
        "description": "Health check endpoint.",
        "operationId": "root__get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/health": {
      "get": {
        "summary": "Health",
        "description": "Health check endpoint.",
        "operationId": "health_health_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/tools": {
      "get": {
        "summary": "List Tools",
        "description": "List available FCCS tools.",
        "operationId": "list_tools_tools_get",
        "responses": {
          "200": {
            "descri
... [truncated] ...
```

