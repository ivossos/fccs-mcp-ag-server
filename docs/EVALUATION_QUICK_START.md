# Evaluation Quick Start Guide 🎯

## ✅ Confirmed: Evaluation System Works!

The RLE (Reinforcement Learning from Execution) evaluation system is **fully functional** and ready to use.

## 🚀 Quick Start (3 Ways)

### Method 1: Natural Language in Cursor/Claude (Easiest!)

After any tool runs, just say:
```
"Rate that execution 5 stars
"Evaluate that with 4 stars and feedback: 'Good results'"
"Rate execution 724 with 5 stars"
```

### Method 2: Interactive Script

Run the interactive helper:
```bash
python interactive_evaluate.py
```

This shows you all unrated executions and lets you:
- Rate individual executions
- Batch rate multiple executions
- Auto-rate all successful executions

### Method 3: Quick View Script

See what needs evaluation:
```bash
python quick_evaluate.py
```

Shows unrated executions with their IDs so you can rate them.

## 📋 Available Tools

### 1. `submit_feedback`
Rate a tool execution (1-5 stars)

**Parameters:**
- `execution_id` (required): From tool result
- `rating` (required): 1-5 stars
- `feedback` (optional): Text comment

**Example:**
```python
await submit_feedback(execution_id=724, rating=5, feedback="Perfect!")
```

### 2. `get_recent_executions`
Find executions that can be rated

**Parameters:**
- `tool_name` (optional): Filter by tool
- `limit` (optional): Number of results (default: 10)

**Example:**
```python
await get_recent_executions(tool_name="smart_retrieve", limit=20)
```

## ✅ Verification

To verify everything works:
```bash
python verify_feedback_tools.py    # Check tools are registered
python test_evaluation_flow.py     # Test complete flow
```

## 📊 Current Status

- ✅ **32 tools** available
- ✅ **2 evaluation tools** registered (`submit_feedback`, `get_recent_executions`)
- ✅ **Tool execution** includes `execution_id` automatically
- ✅ **Feedback persistence** working correctly
- ✅ **RL learning** active and ready

## 💡 Pro Tips

1. **Rate successful executions highly** (4-5 stars) to reinforce good behavior
2. **Rate failures low** (1-2 stars) to discourage bad patterns
3. **Provide specific feedback** when possible - it helps the system learn
4. **Rate consistently** - the more feedback, the better the learning

## 🔍 Finding Execution IDs

Every tool result includes an `execution_id`:
```json
{
  "status": "success",
  "data": {...},
  "execution_id": 724  ← Use this to rate!
}
```

If you missed it, use `get_recent_executions` to find past executions.

## 🎯 Rating Scale

- **5 stars**: Excellent - Perfect results
- **4 stars**: Good - Minor improvements possible
- **3 stars**: Average - Could be better
- **2 stars**: Poor - Had issues
- **1 star**: Bad - Failed or incorrect

## 📚 More Information

- `HOW_TO_EVALUATE.md` - Detailed guide
- `FEEDBACK_GUIDE.md` - Complete feedback documentation
- `FEEDBACK_MCP_INTEGRATION.md` - MCP integration details

## 🐛 Troubleshooting

**Problem**: Don't see `execution_id` in results
- **Solution**: Check feedback service is initialized (should see "Feedback service initialized" in logs)

**Problem**: `submit_feedback` tool not found
- **Solution**: Run `python verify_feedback_tools.py` to check registration

**Problem**: Feedback not saving
- **Solution**: Check database connection and logs

---

**Ready to evaluate?** Just ask in Cursor/Claude: *"Show me recent executions to evaluate"* or *"Rate that execution 5 stars"*!



