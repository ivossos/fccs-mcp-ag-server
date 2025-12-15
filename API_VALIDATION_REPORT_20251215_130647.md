# API Validation Report

- Generated: 2025-12-15T13:06:57Z
- Base URL: `http://localhost:8080`
- curl: `curl`

| Test | Method | Path | Status | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Health check | GET | /health | 0 | 2.241 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2237 ms: Could not connect to server |
| List tools | GET | /tools | 0 | 2.244 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2243 ms: Could not connect to server |
| MCP tools/list | POST | /message | 0 | 2.227 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2227 ms: Could not connect to server |
| Execute tool | POST | /execute | 0 | 2.232 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2232 ms: Could not connect to server |

## Health check

- Request: `GET /health`
- Status: 0
- Duration: 2.241s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2237 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## List tools

- Request: `GET /tools`
- Status: 0
- Duration: 2.244s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2243 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## MCP tools/list

- Request: `POST /message`
- Status: 0
- Duration: 2.227s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2227 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## Execute tool

- Request: `POST /execute`
- Status: 0
- Duration: 2.232s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2232 ms: Could not connect to server

Response snippet:

```json
(no body)
```

