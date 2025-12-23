# RL Performance Dashboard Guide

## Overview

The RL Performance Dashboard (`rl_dashboard.py`) provides comprehensive visualization and analytics for the Reinforcement Learning system in the FCCS Agent. It displays learning metrics, tool performance, policy values, and successful sequences.

## Features

### 1. **Key Metrics Overview**
- Total Tools: Number of tools being tracked
- Average Success Rate: Overall tool success percentage
- Average User Rating: Mean user feedback rating
- Total Policies: Number of Q-learning policies stored
- Exploration Rate: Current exploration vs exploitation balance

### 2. **Tool Performance Analysis**
- **Success Rate Chart**: Top 15 tools ranked by success rate
- **Execution Time Chart**: Tools sorted by average execution time
- **Detailed Metrics Table**: Complete tool statistics including:
  - Total calls
  - Success rate
  - Average execution time
  - Average user rating

### 3. **RL Learning Statistics**
- **Exploration Statistics**:
  - Current exploration rate
  - Initial exploration rate
  - Total tool selections
- **Learning Progress**:
  - Update count (Q-learning updates)
  - Replay buffer size
- **Learning Metrics Summary**:
  - Reward statistics (mean, std, min, max)
  - TD error tracking
  - Episode reward trends
  - Exploration rate over time
- **Metric Trends**: Time-series visualization of learning metrics

### 4. **Successful Tool Sequences**
- Displays successful tool execution sequences (episodes)
- Shows reward values and outcomes
- Filterable by specific tool
- Helps identify effective tool chains

### 5. **RL Policy Explorer**
- View Q-values (action values) for specific tools
- Policy value distribution histograms
- Top policies by Q-value
- Context-based policy analysis

## Available RL Performance Tools

### Direct Service Access (Preferred)
When running locally with direct database access:

```python
from fccs_agent.services.rl_service import get_rl_service
from fccs_agent.services.feedback_service import get_feedback_service

rl_service = get_rl_service()
feedback_service = get_feedback_service()

# Get learning statistics
stats = rl_service.get_learning_stats()

# Get tool metrics
metrics = feedback_service.get_tool_metrics()

# Get successful sequences
episodes = rl_service.get_successful_sequences(limit=20)

# Get recent metrics
recent = rl_service.metrics_tracker.get_recent_metrics("reward", limit=100)

# Get exploration stats
exploration = rl_service.tool_selector.get_exploration_stats()
```

### API Endpoints (Web Server)
When accessing via HTTP API:

#### 1. **GET `/rl/metrics`**
Get overall RL performance metrics.

**Response:**
```json
{
  "rl_enabled": true,
  "tool_metrics": {
    "total_tools": 32,
    "avg_success_rate": 0.95,
    "avg_user_rating": 4.2
  },
  "policy_metrics": {
    "total_policies": 150,
    "avg_action_value": 8.5
  },
  "config": {
    "exploration_rate": 0.1,
    "learning_rate": 0.3,
    "discount_factor": 0.95,
    "min_samples": 3
  }
}
```

#### 2. **GET `/rl/policy/{tool_name}`**
Get RL policy for a specific tool.

**Response:**
```json
{
  "tool_name": "smart_retrieve",
  "policies": [
    {
      "context_hash": "abc123...",
      "action_value": 12.5,
      "visit_count": 45,
      "last_updated": "2025-01-15T10:30:00Z"
    }
  ],
  "total_contexts": 10
}
```

#### 3. **POST `/rl/recommendations`**
Get RL-based tool recommendations.

**Request:**
```json
{
  "query": "get financial data",
  "session_id": "session123",
  "previous_tool": "get_dimensions",
  "session_length": 2
}
```

**Response:**
```json
{
  "query": "get financial data",
  "recommendations": [
    {
      "tool_name": "smart_retrieve",
      "confidence": 0.95,
      "reason": "high success rate, RL policy favor",
      "metrics": {
        "success_rate": 0.98,
        "avg_rating": 4.5,
        "total_calls": 150
      }
    }
  ]
}
```

#### 4. **GET `/rl/episodes`**
Get successful tool sequences (episodes).

**Query Parameters:**
- `tool_name` (optional): Filter by tool
- `limit` (default: 20): Number of episodes to return

**Response:**
```json
{
  "episodes": [
    {
      "session_id": "session123",
      "tool_sequence": ["get_dimensions", "get_members", "smart_retrieve"],
      "episode_reward": 25.5,
      "outcome": "success",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### 5. **GET `/metrics`**
Get tool execution metrics.

**Query Parameters:**
- `tool_name` (optional): Filter by specific tool

**Response:**
```json
{
  "metrics": [
    {
      "tool_name": "smart_retrieve",
      "total_calls": 150,
      "success_rate": 0.98,
      "avg_execution_time_ms": 450.5,
      "avg_user_rating": 4.5
    }
  ]
}
```

#### 6. **GET `/executions`**
Get recent tool executions.

**Query Parameters:**
- `tool_name` (optional): Filter by tool
- `limit` (default: 50): Number of executions

**Response:**
```json
{
  "executions": [
    {
      "id": 123,
      "session_id": "session123",
      "tool_name": "smart_retrieve",
      "success": true,
      "execution_time_ms": 450.5,
      "user_rating": 5,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

## Running the Dashboard

### Prerequisites
```bash
pip install streamlit pandas plotly requests
```

### Start the Dashboard
```bash
streamlit run rl_dashboard.py
```

### Configuration
- **API Mode**: Set `API_BASE_URL` in sidebar (default: `http://localhost:8080`)
- **Direct Mode**: Automatically detects local services if available
- **Auto-refresh**: Configure refresh interval in sidebar

## RL Service Methods

### Learning Statistics
```python
rl_service.get_learning_stats()
# Returns: {
#   "update_count": 1000,
#   "replay_buffer_size": 5000,
#   "exploration_stats": {...},
#   "reward_stats": {...},
#   "td_error_stats": {...}
# }
```

### Tool Recommendations
```python
rl_service.get_tool_recommendations(
    user_query="get account data",
    previous_tool="get_dimensions",
    session_length=2
)
```

### Successful Sequences
```python
rl_service.get_successful_sequences(
    tool_name="smart_retrieve",  # optional
    limit=20
)
```

### Sequence Recommendations
```python
rl_service.get_sequence_recommendations(
    recent_tools=["get_dimensions", "get_members"],
    available_tools=["smart_retrieve", "export_data_slice"],
    top_k=5
)
```

### Exploration Statistics
```python
rl_service.tool_selector.get_exploration_stats()
# Returns: {
#   "current_exploration_rate": 0.08,
#   "initial_exploration_rate": 0.1,
#   "total_selections": 500,
#   "tool_selection_counts": {...}
# }
```

### Metrics Tracking
```python
# Get recent metrics
rl_service.metrics_tracker.get_recent_metrics("reward", limit=100)

# Get metric summary
rl_service.metrics_tracker.get_metric_summary("reward", window_size=100)
# Returns: {
#   "count": 100,
#   "mean": 8.5,
#   "std": 2.3,
#   "min": 2.0,
#   "max": 15.0,
#   "latest": 9.2
# }
```

## Key Metrics Explained

### Reward Function
- **Success**: +10 (success) / -5 (failure)
- **User Rating**: (rating - 3) × 2 (range: -4 to +4)
- **Performance**: -0.1 × (time_ms / 1000)
- **Efficiency Bonus**: +2 if execution < 80% of average
- **Total Range**: Approximately -9 to +16

### Q-Learning Policy
- **Update Rule**: `Q(s,a) = Q(s,a) + α × [reward + γ × max(Q(s',a')) - Q(s,a)]`
- **Learning Rate (α)**: 0.3 (default)
- **Discount Factor (γ)**: 0.95 (default)
- **Exploration Rate (ε)**: 0.1 (default), decays over time

### Exploration vs Exploitation
- **Epsilon-Greedy**: 10% exploration, 90% exploitation (initially)
- **UCB**: Upper Confidence Bound for intelligent exploration
- **Decay**: Exploration rate decreases over time (0.995 per selection)

## Database Tables

### `rl_policy`
Stores Q-values for (tool, context) pairs:
- `tool_name`: Tool identifier
- `context_hash`: Context hash (SHA256)
- `action_value`: Q-value
- `visit_count`: Number of times this action was taken
- `last_updated`: Timestamp

### `rl_episodes`
Stores complete session sequences:
- `session_id`: Session identifier
- `tool_sequence`: JSON array of tool names
- `episode_reward`: Total reward for episode
- `outcome`: "success", "partial", or "failure"

### `rl_metrics`
Tracks learning metrics over time:
- `metric_name`: Name of metric (reward, td_error, etc.)
- `metric_value`: Value
- `extra_data`: Additional context (JSON)
- `timestamp`: When recorded

### `rl_tool_sequences`
N-gram sequences for pattern learning:
- `sequence_key`: Tool sequence (e.g., "tool1->tool2->tool3")
- `count`: Number of occurrences
- `avg_reward`: Average reward
- `success_rate`: Success percentage

## Troubleshooting

### Dashboard shows "RL service not available"
1. Check `RL_ENABLED=true` in `.env`
2. Verify `DATABASE_URL` is configured
3. Ensure services are initialized before dashboard starts

### No metrics displayed
- Wait for some tool executions to occur
- Check that feedback service is logging executions
- Verify database connectivity

### API mode not working
- Ensure web server is running (`python -m web.server`)
- Check API_BASE_URL is correct
- Verify CORS settings if accessing from different origin

## Best Practices

1. **Monitor Exploration Rate**: Should decrease over time as system learns
2. **Track Reward Trends**: Increasing rewards indicate learning
3. **Analyze Sequences**: Identify successful tool chains
4. **Review Policy Values**: High Q-values indicate good tool-context matches
5. **User Feedback**: Encourage users to rate tool executions (1-5 stars)

## Related Files

- `fccs_agent/services/rl_service.py`: Core RL service implementation
- `fccs_agent/services/feedback_service.py`: Feedback tracking
- `web/server.py`: API endpoints
- `dashboard.py`: Main FCCS performance dashboard
- `rl_dashboard.py`: RL performance dashboard

