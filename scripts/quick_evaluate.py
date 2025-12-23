"""Quick script to evaluate recent tool executions."""

import sys
from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService

def main():
    """Show recent executions and allow quick evaluation."""
    print("=" * 70)
    print("Quick Evaluation Tool")
    print("=" * 70)
    print()
    
    try:
        feedback_service = FeedbackService(config.database_url)
    except Exception as e:
        print(f"ERROR: Could not connect to feedback service: {e}")
        print()
        print("Make sure:")
        print("  1. Database is running")
        print("  2. Database URL is correct in config")
        print("  3. Feedback service is initialized")
        return 1
    
    # Get recent executions
    print("Fetching recent executions...")
    executions = feedback_service.get_recent_executions(limit=20)
    
    if not executions:
        print("No executions found. Run some tools first!")
        return 0
    
    # Filter unrated executions
    unrated = [e for e in executions if e.get("user_rating") is None]
    rated = [e for e in executions if e.get("user_rating") is not None]
    
    print(f"\nFound {len(executions)} total executions")
    print(f"  - {len(unrated)} unrated (can be evaluated)")
    print(f"  - {len(rated)} already rated")
    print()
    
    if unrated:
        print("Unrated Executions (Ready for Evaluation):")
        print("-" * 70)
        for i, e in enumerate(unrated[:10], 1):
            status = "SUCCESS" if e.get("success") else "FAILED"
            tool_name = e.get("tool_name", "unknown")
            exec_id = e.get("id", "?")
            timestamp = e.get("created_at", "?")
            
            print(f"{i}. ID: {exec_id:4d} | {tool_name:30s} | {status:8s} | {timestamp}")
        
        if len(unrated) > 10:
            print(f"\n... and {len(unrated) - 10} more unrated executions")
        
        print()
        print("To evaluate, use one of these methods:")
        print()
        print("1. In Cursor/Claude chat:")
        print('   "Rate execution 123 with 5 stars"')
        print()
        print("2. Using Python:")
        print("   from fccs_agent.tools.feedback import submit_feedback")
        print("   await submit_feedback(execution_id=123, rating=5)")
        print()
        print("3. Using REST API:")
        print('   curl -X POST http://localhost:8080/feedback \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"execution_id": 123, "rating": 5}\'')
        print()
    else:
        print("All recent executions have been rated!")
        print()
    
    if rated:
        print("Recently Rated Executions:")
        print("-" * 70)
        for i, e in enumerate(rated[:5], 1):
            tool_name = e.get("tool_name", "unknown")
            exec_id = e.get("id", "?")
            rating = e.get("user_rating", "?")
            feedback = e.get("user_feedback", "")
            print(f"{i}. ID: {exec_id:4d} | {tool_name:30s} | {rating} stars | {feedback[:50]}")
        print()
    
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())



