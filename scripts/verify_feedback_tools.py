"""Verify that feedback/evaluation tools are available in the MCP server."""

import sys
import json
from fccs_agent.agent import get_tool_definitions

def main():
    """Check if feedback tools are available."""
    print("=" * 70)
    print("Verifying Feedback/Evaluation Tools Availability")
    print("=" * 70)
    print()
    
    # Get all tool definitions
    all_tools = get_tool_definitions()
    
    # Find feedback tools - check both name and description
    feedback_tools = []
    for t in all_tools:
        name_lower = t["name"].lower()
        desc_lower = t.get("description", "").lower()
        if ("feedback" in name_lower or "evaluate" in name_lower or 
            "feedback" in desc_lower or "evaluate" in desc_lower or
            "rate" in desc_lower or "rating" in desc_lower):
            feedback_tools.append(t)
    
    # Also explicitly check for known feedback tool names
    known_feedback_tools = ["submit_feedback", "get_recent_executions"]
    for tool_name in known_feedback_tools:
        tool = next((t for t in all_tools if t["name"] == tool_name), None)
        if tool and tool not in feedback_tools:
            feedback_tools.append(tool)
    
    print(f"Total tools available: {len(all_tools)}")
    print(f"Feedback/evaluation tools found: {len(feedback_tools)}")
    print()
    
    if not feedback_tools:
        print("ERROR: No feedback tools found!")
        print()
        print("Expected tools:")
        print("  - submit_feedback")
        print("  - get_recent_executions")
        return 1
    
    print("SUCCESS: Feedback tools found:")
    print()
    
    for tool in feedback_tools:
        print(f"  - {tool['name']}")
        print(f"     Description: {tool['description']}")
        
        # Show required parameters
        required = tool.get('inputSchema', {}).get('required', [])
        if required:
            print(f"     Required params: {', '.join(required)}")
        
        # Show all parameters
        properties = tool.get('inputSchema', {}).get('properties', {})
        if properties:
            print(f"     Parameters:")
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'unknown')
                param_desc = param_info.get('description', '')
                is_required = param_name in required
                req_marker = " (required)" if is_required else ""
                print(f"       - {param_name} ({param_type}){req_marker}")
                if param_desc:
                    print(f"         {param_desc}")
        print()
    
    # Check if tools are properly registered
    tool_names = [t["name"] for t in all_tools]
    
    expected_tools = ["submit_feedback", "get_recent_executions"]
    missing_tools = [t for t in expected_tools if t not in tool_names]
    
    if missing_tools:
        print(f"WARNING: Missing expected tools: {', '.join(missing_tools)}")
        return 1
    
    print("=" * 70)
    print("SUCCESS: All feedback tools are properly registered!")
    print("=" * 70)
    print()
    print("How to use:")
    print()
    print("1. After any tool execution, check the result for 'execution_id'")
    print("2. Use submit_feedback tool with:")
    print("   - execution_id: <from tool result>")
    print("   - rating: 1-5 (5 = excellent, 1 = poor)")
    print("   - feedback: (optional) text comment")
    print()
    print("3. To find executions to rate, use get_recent_executions:")
    print("   - tool_name: (optional) filter by tool")
    print("   - limit: (optional) number of results (default: 10)")
    print()
    print("Example in Cursor/Claude:")
    print('  "Rate the last smart_retrieve execution 5 stars"')
    print('  or')
    print('  "Show me recent executions I can evaluate"')
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

