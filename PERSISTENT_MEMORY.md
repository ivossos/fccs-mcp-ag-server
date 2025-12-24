# Persistent Memory in FCCS MCP Server

This project has **multiple layers of persistent memory** for different purposes:

## 1. SQLite Database (Primary Persistent Storage)

### Purpose
- **Tool execution tracking** for reinforcement learning
- **User feedback** collection
- **Performance metrics** aggregation
- **Session history** tracking

### Tables

#### `tool_executions`
Stores every tool execution:
- `id` - Unique execution ID
- `session_id` - Session identifier
- `tool_name` - Which tool was called
- `arguments` - Tool arguments (JSON)
- `result` - Tool result (JSON)
- `success` - Boolean success flag
- `error_message` - Error details if failed
- `execution_time_ms` - Performance metric
- `created_at` - Timestamp
- `user_rating` - User feedback (1-5 scale)
- `user_feedback` - User comments

#### `tool_metrics`
Aggregated metrics per tool:
- `tool_name` - Tool identifier
- `total_calls` - Total executions
- `success_count` - Successful executions
- `failure_count` - Failed executions
- `avg_execution_time_ms` - Average performance
- `avg_user_rating` - Average user rating
- `last_updated` - Last update timestamp

### Configuration
Set via `DATABASE_URL` environment variable:
```bash
DATABASE_URL=sqlite:///./data/fccs_agent.db
```

### Database Location
The SQLite database file is stored at `./data/fccs_agent.db` by default.

### Initialization
```bash
python scripts/init_db.py
```

### Usage
- **Automatic**: Every tool execution is logged automatically
- **API Endpoints**:
  - `GET /metrics` - Get tool metrics
  - `GET /executions` - Get recent executions
  - `POST /feedback` - Submit user feedback

## 2. Local File Cache (Dimension Members)

### Purpose
- **Fast access** to dimension members (Entity, Account, etc.)
- **Reduces API calls** to FCCS
- **Offline capability** for metadata

### Location
```
.cache/
  members/
    Consol_Entity.json
    Consol_Account.json
    Consol_Period.json
    ...
```

### How It Works
1. **First call**: Fetches from FCCS API → Saves to JSON cache
2. **Subsequent calls**: Loads from local cache (instant)
3. **Fallback**: If JSON cache missing, tries CSV files in project root

### CSV Fallback
- `Ravi_ExportedMetadata_Entity.csv` - Entity dimension
- `Ravi_ExportedMetadata_Account.csv` - Account dimension

### Cache Management
```python
from fccs_agent.utils.cache import (
    load_members_from_cache,
    save_members_to_cache
)
```

## 3. Session Memory (Runtime)

### Purpose
- **Session tracking** across tool calls
- **Context preservation** within a conversation
- **Execution timing** tracking

### Implementation
- Stored in memory during runtime
- Session ID passed with each tool call
- Linked to database via `session_id` in `tool_executions`

## 4. Configuration Memory (.env file)

### Purpose
- **Persistent configuration** across restarts
- **Credentials** (encrypted in production)
- **Feature flags** and settings

### Location
`.env` file in project root

### Key Variables
```bash
# FCCS Connection
FCCS_URL=https://your-instance.epm.ocs.oraclecloud.com
FCCS_USERNAME=your_username
FCCS_PASSWORD=your_password
FCCS_MOCK_MODE=false

# Database
DATABASE_URL=sqlite:///./data/fccs_agent.db

# Google API (optional)
GOOGLE_API_KEY=your_key
MODEL_ID=gemini-2.0-flash

# Server
PORT=8080
```

## Memory Flow Diagram

```
User Request
    ↓
ChatGPT/Custom GPT
    ↓
Web Server (FastAPI)
    ↓
┌─────────────────────────────────────┐
│  Tool Execution                     │
│  ┌───────────────────────────────┐  │
│  │ 1. Check Local Cache          │  │ → .cache/members/*.json
│  │ 2. If missing, call FCCS API  │  │ → Save to cache
│  │ 3. Execute tool               │  │
│  │ 4. Log to Database           │  │ → SQLite
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
Response to User
```

## Benefits of Persistent Memory

### 1. **Performance**
- Local cache eliminates repeated API calls
- Database queries are fast with indexes
- Reduces latency for common operations

### 2. **Learning & Improvement**
- Track which tools are used most
- Identify performance bottlenecks
- Collect user feedback for improvement
- Enable reinforcement learning

### 3. **Reliability**
- Cache provides offline capability
- Database preserves execution history
- Can recover from API failures

### 4. **Analytics**
- Query execution patterns
- Measure tool performance
- Track user satisfaction
- Identify optimization opportunities

## Accessing Persistent Memory

### View Tool Metrics
```bash
curl http://localhost:8080/metrics
```

### View Recent Executions
```bash
curl http://localhost:8080/executions?limit=10
```

### Submit Feedback
```bash
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": 123,
    "rating": 5,
    "feedback": "Great tool!"
  }'
```

### Check Cache Status
```bash
python scripts/show_cache_status.py
```

## Cloud Run Deployment

When deployed to Cloud Run:

1. **Database**: SQLite file stored in a persistent volume
   ```bash
   DATABASE_URL=sqlite:///./data/fccs_agent.db
   ```
   Note: For Cloud Run, consider mounting a Cloud Storage bucket for persistence.

2. **Cache**: Ephemeral (resets on restart)
   - Consider using Cloud Storage for persistent cache
   - Or use database for cache storage

3. **Configuration**: Use Secret Manager
   ```bash
   gcloud secrets create FCCS_URL --data-file=-
   gcloud run services update fccs-mcp-server \
     --set-secrets="FCCS_URL=FCCS_URL:latest"
   ```

## Summary

| Storage Type | Purpose | Persistence | Location |
|-------------|---------|-------------|----------|
| SQLite | Tool execution history, metrics, feedback | Permanent | ./data/fccs_agent.db |
| Local Cache | Dimension members, metadata | File system | `.cache/` directory |
| CSV Files | Fallback metadata source | File system | Project root |
| .env File | Configuration | File system | Project root |
| Session Memory | Runtime session tracking | Temporary | In-memory |

All persistent memory is **automatically managed** - you don't need to manually interact with it unless you want to query metrics or clear cache.

## 5. Business Rules & Defaults (Documentation Memory)

### Purpose
- **Business logic defaults** for FCCS operations
- **Convention documentation** for consistent behavior
- **System preferences** that guide tool usage

### Entity Member Default

**Rule:** When an entity member is omitted or not provided, use **"FCCS_Total Geography"** as the default.

**Examples:**
- `smart_retrieve(account="FCCS_Net Income")` → Uses `entity="FCCS_Total Geography"` by default
- `export_data_slice()` without entity → Should default to `"FCCS_Total Geography"`
- Any tool that accepts an `entity` parameter should default to `"FCCS_Total Geography"` if not specified

**Implementation:**
- Already implemented in `smart_retrieve()` function (see `fccs_agent/tools/data.py`)
- Should be applied consistently across all tools that accept entity parameters

**Rationale:**
- "FCCS_Total Geography" represents the consolidated/aggregated view across all entities
- Most common use case for financial reporting and analysis
- Provides meaningful default for high-level queries











