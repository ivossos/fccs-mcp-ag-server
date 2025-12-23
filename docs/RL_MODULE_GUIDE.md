# Reinforcement Learning Module Guide

## Overview

The Reinforcement Learning (RL) module enhances the FCCS Agent by learning from tool execution history to improve tool selection, parameter optimization, and overall agent performance over time.

## Features

- **Intelligent Tool Selection**: Recommends tools based on historical success rates, user ratings, and execution patterns
- **Context-Aware Learning**: Learns which tools work best in different contexts (user queries, previous tools, session state)
- **Parameter Optimization**: Suggests optimal parameters based on successful historical executions
- **Sequence Learning**: Identifies successful tool sequences for common workflows
- **Epsilon-Greedy Exploration**: Balances exploitation of known good tools with exploration of alternatives

## Quick Start

### 1. Initialize Database Tables

Run the migration script to create RL tables:

```bash
python scripts/add_rl_tables.py
```

This creates two tables:
- `rl_policy`: Stores Q-values (action values) for tool-context pairs
- `rl_episodes`: Tracks complete sessions for sequence learning

### 2. Enable RL in Configuration

RL is enabled by default. Configure via environment variables:

```bash
# Enable/disable RL (default: true)
RL_ENABLED=true

# Exploration rate - probability of trying random tools (default: 0.1 = 10%)
RL_EXPLORATION_RATE=0.1

# Learning rate - how fast to update Q-values (default: 0.1)
RL_LEARNING_RATE=0.1

# Discount factor for future rewards (default: 0.9)
RL_DISCOUNT_FACTOR=0.9

# Minimum samples before using RL recommendations (default: 5)
RL_MIN_SAMPLES=5
```

### 3. Use RL-Enhanced Tool Execution

The agent automatically uses RL when enabled. You can also explicitly use RL-enhanced execution:

```python
from fccs_agent.agent import execute_tool_with_rl

result = await execute_tool_with_rl(
    tool_name="smart_retrieve",
    arguments={"account": "FCCS_Net Income"},
    session_id="user123",
    user_query="Get net income for Q1"
)

# Result includes RL recommendations
print(result.get("rl_recommendations"))
```

## How It Works

### Reward Calculation

The RL module calculates rewards from tool executions using multiple factors:

- **Success Reward**: +10 for successful execution, -5 for failure
- **User Rating**: (rating - 3) × 2 (normalized to -4 to +4)
- **Performance Penalty**: -0.1 × (execution_time_ms / 1000)
- **Efficiency Bonus**: +2 if execution time < 80% of average

**Total Reward Range**: Approximately -9 to +16

### Policy Learning

The module uses Q-learning to update action values:

```
Q(s,a) = Q(s,a) + α × [reward - Q(s,a)]
```

Where:
- `s` = state (context hash)
- `a` = action (tool name)
- `α` = learning rate
- `reward` = calculated reward from execution

### Tool Selection

Tools are selected using epsilon-greedy strategy:

1. **Exploration (10%)**: Random tool selection to discover new patterns
2. **Exploitation (90%)**: Select tool with highest expected reward (Q-value)

### Context Representation

Context is hashed from:
- User query keywords
- Previous tool in sequence
- Session length (number of tools executed)

This allows the RL module to learn context-specific tool preferences.

## API Endpoints

### Get RL Metrics

```bash
GET /rl/metrics
```

Returns overall RL performance metrics, tool statistics, and configuration.

### Get Tool Policy

```bash
GET /rl/policy/{tool_name}
```

Returns current RL policy (Q-values) for a specific tool across different contexts.

### Get Recommendations

```bash
POST /rl/recommendations
Content-Type: application/json

{
  "query": "Get financial data for Q1",
  "session_id": "user123",
  "previous_tool": "get_dimensions",
  "session_length": 2
}
```

Returns ranked list of recommended tools with confidence scores.

### Get Successful Sequences

```bash
GET /rl/episodes?tool_name=smart_retrieve&limit=10
```

Returns successful tool sequences for pattern learning.

### Execute with RL

```bash
POST /execute/rl
Content-Type: application/json

{
  "tool_name": "smart_retrieve",
  "arguments": {"account": "FCCS_Net Income"},
  "session_id": "user123",
  "user_query": "Get net income"
}
```

Executes tool with RL-enhanced recommendations included in response.

### Finalize Session

```bash
POST /sessions/{session_id}/finalize?outcome=success
```

Finalizes a session and logs episode for sequence learning.

## Monitoring

### View RL Metrics

```python
from fccs_agent.services.rl_service import get_rl_service

rl_service = get_rl_service()
if rl_service:
    # Get recommendations
    recommendations = rl_service.get_tool_recommendations(
        user_query="Get financial data",
        previous_tool="get_dimensions",
        session_length=1
    )
    print(recommendations)
```

### Check Policy Values

```python
from fccs_agent.services.rl_service import get_rl_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fccs_agent.services.rl_service import RLPolicy
from fccs_agent.config import config

rl_service = get_rl_service()
engine = create_engine(config.database_url)
Session = sessionmaker(bind=engine)

with Session() as session:
    policies = session.query(RLPolicy).filter_by(
        tool_name="smart_retrieve"
    ).all()
    for policy in policies:
        print(f"Context: {policy.context_hash}, Q-value: {policy.action_value}")
```

## Best Practices

1. **Collect Feedback**: The RL module learns faster with user ratings. Encourage users to provide feedback.

2. **Monitor Exploration**: Start with higher exploration rate (0.2-0.3) when deploying, then reduce to 0.1 after learning period.

3. **Session Finalization**: Always finalize sessions to enable sequence learning:
   ```python
   from fccs_agent.agent import finalize_session
   finalize_session(session_id, outcome="success")
   ```

4. **Minimum Samples**: Ensure tools have at least `RL_MIN_SAMPLES` executions before relying on RL recommendations.

5. **Context Quality**: Provide meaningful user queries for better context-aware recommendations.

## Troubleshooting

### RL Service Not Initialized

**Issue**: RL recommendations not available

**Solution**: 
- Check `RL_ENABLED=true` in environment
- Ensure feedback service is initialized (RL depends on it)
- Check database connection

### No Recommendations

**Issue**: Empty or poor recommendations

**Solution**:
- Ensure tools have been executed at least `RL_MIN_SAMPLES` times
- Check that feedback service is logging executions
- Verify database tables exist (`python scripts/add_rl_tables.py`)

### Policy Not Updating

**Issue**: Q-values not changing after executions

**Solution**:
- Check that `after_tool_callback` is being called
- Verify execution_id is being returned
- Check database connection and permissions
- Review error logs for RL update failures

## Architecture

```
┌─────────────────┐
│   Agent Layer   │
│  (agent.py)     │
└────────┬────────┘
         │
         ├───► Tool Execution
         │
         ▼
┌─────────────────┐
│ Feedback Service│
│ (Logs Executions)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RL Service    │
│  (rl_service.py)│
└────────┬────────┘
         │
         ├───► Reward Calculation
         ├───► Policy Update (Q-learning)
         ├───► Tool Selection
         └───► Sequence Learning
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│  (rl_policy,    │
│  rl_episodes)    │
└─────────────────┘
```

## Future Enhancements

- Deep RL with neural networks for complex policies
- Multi-agent RL for learning from multiple users
- Transfer learning across FCCS instances
- Explainable AI for recommendation reasoning
- Federated learning for privacy-preserving learning

## References

- Implementation Plan: `RL_IMPLEMENTATION_PLAN.md`
- Feedback Service: `fccs_agent/services/feedback_service.py`
- RL Service: `fccs_agent/services/rl_service.py`

