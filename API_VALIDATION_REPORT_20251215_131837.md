# API Validation Report

- Generated: 2025-12-15T13:18:46Z
- Base URL: `http://localhost:8080`
- curl: `curl`

| Test | Method | Path | Status | Duration (s) | Success | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Health check | GET | /health | 0 | 2.230 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2230 ms: Could not connect to server |
| List tools | GET | /tools | 0 | 2.243 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2243 ms: Could not connect to server |
| MCP tools/list | POST | /message | 0 | 2.249 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2248 ms: Could not connect to server |
| Execute tool | POST | /execute | 0 | 2.255 | ❌ | curl: (7) Failed to connect to localhost port 8080 after 2255 ms: Could not connect to server |

## Health check

- Request: `GET /health`
- Status: 0
- Duration: 2.230s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2230 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## List tools

- Request: `GET /tools`
- Status: 0
- Duration: 2.243s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2243 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## MCP tools/list

- Request: `POST /message`
- Status: 0
- Duration: 2.249s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2248 ms: Could not connect to server

Response snippet:

```json
(no body)
```

## Execute tool

- Request: `POST /execute`
- Status: 0
- Duration: 2.255s
- curl exit code: 7
- Error: curl: (7) Failed to connect to localhost port 8080 after 2255 ms: Could not connect to server

Response snippet:

```json
(no body)
```

