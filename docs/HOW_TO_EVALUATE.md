# How to Evaluate Tool Executions (RLE System) 🎯

## Quick Answer: YES, You CAN Evaluate!

The RLE (Reinforcement Learning from Execution) system **DOES** provide evaluation options. Here's how to use them:

## Method 1: Direct Evaluation After Tool Execution (Easiest!)

When any tool executes, the result includes an `execution_id`. You can immediately evaluate it:

### In Cursor/Claude Chat:

1. **After a tool runs**, you'll see a result like:
   ```json
   {
     "status": "success",
     "data": {...},
     "execution_id": 123  ← This is your evaluation key!
   }
   ```

2. **Simply ask to evaluate it**:
   ```
   "Rate that execution 5 stars, it worked perfectly"
   ```
   or
   ```
   "Evaluate that with 4 stars and feedback: 'Good results but took a bit long'"
   ```

3. **The AI will automatically use `submit_feedback`** with:
   - `execution_id`: 123 (from the result)
   - `rating`: 5 (or whatever you specify)
   - `feedback`: (optional) your comment

## Method 2: Find Recent Executions to Evaluate

If you want to evaluate past executions:

### Ask the AI:
```
"Show me recent tool executions I can evaluate"
```
or
```
"Get the last 10 executions for smart_retrieve tool"
```

The AI will use `get_recent_executions` to show you:
- Execution IDs
- Tool names
- Success status
- Whether they've been rated

Then you can say:
```
"Rate execution 123 with 5 stars"
```

## Method 3: Explicit Tool Call (Advanced)

You can also explicitly call the tools:

### Submit Feedback:
```json
{
  "tool": "submit_feedback",
  "arguments": {
    "execution_id": 123,
    "rating": 5,
    "feedback": "Perfect results!"
  }
}
```

### Get Recent Executions:
```json
{
  "tool": "get_recent_executions",
  "arguments": {
    "tool_name": "smart_retrieve",  // optional
    "limit": 10  // optional, default 10
  }
}
```

## Verification

To verify the evaluation tools are available, run:
```bash
python verify_feedback_tools.py
```

This will confirm:
- ✅ `submit_feedback` is available
- ✅ `get_recent_executions` is available
- ✅ Both tools are properly configured

## Rating Scale

- **5 stars**: Excellent - Tool worked perfectly, use this approach
- **4 stars**: Good - Tool worked well, minor improvements possible  
- **3 stars**: Average - Tool worked but could be better
- **2 stars**: Poor - Tool had issues but partially worked
- **1 star**: Bad - Tool failed or produced incorrect results

## Why Evaluation Matters

- **Improves RL Confidence**: Higher ratings boost confidence scores (target: 75-85%)
- **Better Tool Selection**: System learns which tools work best for your use cases
- **Faster Learning**: With learning rate 0.3, each rating has immediate impact
- **Personalization**: System adapts to your preferences and workflows

## Troubleshooting

### "I don't see execution_id in results"
- Check if the feedback service is initialized (should see "Feedback service initialized" in logs)
- Verify database connection is working
- Check that `after_tool_callback` is being called

### "submit_feedback tool not found"
- Run `python verify_feedback_tools.py` to check tool registration
- Restart the MCP server if needed
- Check that `fccs_agent/tools/feedback.py` is properly imported

### "Feedback service not available"
- Check database connection string in config
- Ensure PostgreSQL is running (if using database)
- Check logs for initialization errors

## Quick Test

Try this sequence:

1. **Execute a tool**: "Get application info"
2. **Check for execution_id** in the result
3. **Evaluate it**: "Rate that execution 5 stars"
4. **Verify**: "Show me recent executions" (should show your rating)

If all steps work, your evaluation system is fully functional! ✅



