# How to Provide Feedback to Improve RL Learning 🎯

The RL (Reinforcement Learning) system learns from your feedback to improve tool selection and recommendations. Here are all the ways you can provide feedback.

## Why Feedback Matters

- **Improves RL Confidence**: Higher ratings boost confidence scores (target: 75-85%)
- **Better Tool Selection**: System learns which tools work best for your use cases
- **Faster Learning**: With learning rate 0.3, each rating has immediate impact
- **Personalization**: System adapts to your preferences and workflows

## Rating Scale

- **5 stars**: Excellent - Tool worked perfectly, use this approach
- **4 stars**: Good - Tool worked well, minor improvements possible
- **3 stars**: Average - Tool worked but could be better
- **2 stars**: Poor - Tool had issues but partially worked
- **1 star**: Bad - Tool failed or produced incorrect results

## Methods to Provide Feedback

### Method 1: Via MCP Tools (Claude/Cursor - Easiest!) ⭐

**Best for**: Providing feedback directly in Claude Desktop or Cursor chat

After any tool execution, the result now includes an `execution_id` field. You can immediately rate it using the `submit_feedback` tool!

**Example workflow in Claude/Cursor**:

1. **Execute a tool** (e.g., `smart_retrieve`):
   ```
   Tool result: {
     "status": "success",
     "data": {...},
     "execution_id": 567  ← This is included automatically!
   }
   ```

2. **Rate the execution** using `submit_feedback`:
   ```
   Use submit_feedback with:
   - execution_id: 567
   - rating: 5
   - feedback: "Perfect results!"
   ```

**Available MCP Feedback Tools**:

- **`submit_feedback`**: Rate a tool execution (1-5 stars)
  - `execution_id`: From the tool result
  - `rating`: 1-5 stars
  - `feedback`: Optional comment

- **`get_recent_executions`**: Find executions to rate
  - `tool_name`: Optional filter
  - `limit`: Number of results (default: 10)

**Example in Claude/Cursor chat**:
```
You: "Get dimensions for the application"
Claude: [Executes get_dimensions, gets execution_id: 568]

You: "Rate that execution 5 stars, it worked perfectly"
Claude: [Calls submit_feedback with execution_id: 568, rating: 5]
```

**Benefits**:
- ✅ No need to remember execution IDs
- ✅ Can provide feedback immediately after execution
- ✅ Works seamlessly in Claude Desktop and Cursor
- ✅ Helps RL system learn in real-time

### Method 2: Via REST API (Recommended for Automation)

**Endpoint**: `POST /feedback`

**Request Body**:
```json
{
  "execution_id": 123,
  "rating": 5,
  "feedback": "Great tool! Generated exactly what I needed."
}
```

**Example with cURL**:
```bash
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": 123,
    "rating": 5,
    "feedback": "Perfect results!"
  }'
```

**Example with Python**:
```python
import requests

response = requests.post(
    "http://localhost:8080/feedback",
    json={
        "execution_id": 123,
        "rating": 5,
        "feedback": "Great tool!"
    }
)
print(response.json())
```

### Method 3: Using the Feedback Script

**List unrated executions**:
```bash
python provide_feedback.py --list
```

**Rate a specific execution**:
```bash
python provide_feedback.py --rate 123 --stars 5 --comment "Excellent tool!"
```

**Auto-rate all successful executions**:
```bash
python provide_feedback.py --batch-rate --stars 5
```

**Interactive mode** (shows examples):
```bash
python provide_feedback.py
```

### Method 4: Direct Python API

```python
from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService

# Initialize service
feedback_service = FeedbackService(config.database_url)

# Rate an execution
feedback_service.add_user_feedback(
    execution_id=123,
    rating=5,  # 1-5 stars
    feedback="Great tool!"  # Optional comment
)
```

### Method 5: Find Execution IDs

**Get recent executions**:
```bash
curl http://localhost:8080/executions?limit=20
```

**Via Python**:
```python
from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService

feedback_service = FeedbackService(config.database_url)
executions = feedback_service.get_recent_executions(limit=20)

for e in executions:
    print(f"ID: {e['id']}, Tool: {e['tool_name']}, Success: {e['success']}, Rating: {e.get('user_rating', 'Not rated')}")
```

## Best Practices

### ✅ Do:
- **Rate successful executions highly** (4-5 stars) to reinforce good behavior
- **Rate failures low** (1-2 stars) to discourage bad patterns
- **Provide specific feedback** in comments when possible
- **Rate consistently** - the more feedback, the better the learning

### ❌ Don't:
- Don't rate randomly - be consistent with your criteria
- Don't skip rating successful tools - they need positive reinforcement
- Don't rate based on speed alone - consider accuracy and usefulness

## Impact on RL Learning

### Reward Calculation

The RL system calculates rewards based on:
- **Success**: +10.0 (success) / -5.0 (failure)
- **User Rating**: (rating - 3) × 2.0 (range: -4 to +4)
- **Performance**: -0.1 × (time_ms / 1000)
- **Efficiency Bonus**: +2.0 (if faster than average)

**Example**:
- Successful execution with 5-star rating: ~+16 reward
- Failed execution with 1-star rating: ~-9 reward

### Confidence Boost

With current settings:
- **Learning Rate**: 0.3 (3x faster learning)
- **Discount Factor**: 0.95 (values future rewards)
- **Min Samples**: 3 (early RL activation)

**Expected Impact**:
- 5-star rating on successful tool: +0.3 to +0.5 confidence boost
- 10 positive ratings: ~5-10% confidence increase
- 50 positive ratings: ~15-25% confidence increase

## Monitoring Feedback Impact

**Check RL status**:
```bash
python check_rl_status.py
```

**View metrics**:
```bash
curl http://localhost:8080/metrics
```

**Dashboard**:
```bash
streamlit run tool_stats_dashboard.py
```

## Quick Start: Boost RL Confidence

**Option 1: Rate recent successful executions**
```bash
# List unrated executions
python provide_feedback.py --list

# Rate them (replace ID with actual execution ID)
python provide_feedback.py --rate <ID> --stars 5
```

**Option 2: Auto-rate all successful executions**
```bash
python provide_feedback.py --batch-rate --stars 5
```

**Option 3: Bootstrap with synthetic data**
```bash
python boost_rl_confidence.py
```

## Example Workflow

1. **Execute a tool** (via MCP, API, or dashboard)
2. **Check execution ID** from response or logs
3. **Rate the execution**:
   ```bash
   python provide_feedback.py --rate <ID> --stars 5
   ```
4. **Monitor improvement**:
   ```bash
   python check_rl_status.py
   ```

## Troubleshooting

### "Execution ID not found"
- Check that the execution exists: `python provide_feedback.py --list`
- Verify the ID is correct

### "Feedback not updating RL"
- RL policy updates happen on next tool execution
- Check RL status: `python check_rl_status.py`
- Ensure RL is enabled: Check `.env` file for `RL_ENABLED=true`

### "Ratings not showing in metrics"
- Metrics update automatically after feedback
- Check: `curl http://localhost:8080/metrics`
- Wait a few seconds and refresh

## Summary

**Easiest way to provide feedback** (Claude/Cursor):
```
After any tool execution, use submit_feedback with the execution_id from the result:
- execution_id: (from tool result)
- rating: 5
- feedback: "Great tool!"
```

**Via command line**:
```bash
# Auto-rate all successful executions
python provide_feedback.py --batch-rate --stars 5
```

**For automation**:
```bash
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{"execution_id": 123, "rating": 5}'
```

🎯 **Goal**: Rate 10-20 successful executions to boost RL confidence from 64% to 75%+!

