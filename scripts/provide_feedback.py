#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive script to provide feedback on tool executions.
Helps boost RL confidence by rating recent tool executions.
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService
from fccs_agent.services.rl_service import init_rl_service, get_rl_service

def list_unrated_executions(limit=20):
    """List recent executions that haven't been rated yet."""
    feedback_service = FeedbackService(config.database_url)
    
    executions = feedback_service.get_recent_executions(limit=limit)
    unrated = [e for e in executions if e.get("user_rating") is None]
    
    return unrated

def provide_feedback_interactive():
    """Interactive feedback provider."""
    print("=" * 60)
    print("Provide Feedback to Improve RL Learning")
    print("=" * 60)
    print()
    
    feedback_service = FeedbackService(config.database_url)
    rl_service = init_rl_service(
        feedback_service=feedback_service,
        db_url=config.database_url,
        exploration_rate=config.rl_exploration_rate,
        learning_rate=config.rl_learning_rate,
        discount_factor=config.rl_discount_factor,
        min_samples=config.rl_min_samples
    )
    
    # Get unrated executions
    unrated = list_unrated_executions(limit=20)
    
    if not unrated:
        print("No unrated executions found. All recent executions have been rated!")
        print()
        print("Recent executions:")
        all_executions = feedback_service.get_recent_executions(limit=10)
        for e in all_executions:
            rating = e.get("user_rating", "Not rated")
            status = "SUCCESS" if e.get("success") else "FAILED"
            print(f"  ID {e['id']:4d}: {e['tool_name']:30s} {status:8s} Rating: {rating}")
        return
    
    print(f"Found {len(unrated)} unrated executions.\n")
    print("Recent unrated executions:")
    print("-" * 60)
    
    for i, execution in enumerate(unrated[:10], 1):
        status = "SUCCESS" if execution.get("success") else "FAILED"
        time_ms = execution.get("execution_time_ms", 0)
        time_str = f"{time_ms:.0f}ms" if time_ms < 1000 else f"{time_ms/1000:.1f}s"
        
        print(f"{i:2d}. ID {execution['id']:4d}: {execution['tool_name']:30s} {status:8s} ({time_str})")
    
    print()
    print("How to provide feedback:")
    print("-" * 60)
    print("1. Via API (recommended for automation):")
    print()
    print("   curl -X POST http://localhost:8080/feedback \\")
    print("     -H \"Content-Type: application/json\" \\")
    print("     -d '{")
    print("       \"execution_id\": <ID>, ")
    print("       \"rating\": <1-5>, ")
    print("       \"feedback\": \"Optional comment\"")
    print("     }'")
    print()
    print("2. Via Python script (see examples below):")
    print()
    print("3. Interactive mode (coming soon)")
    print()
    print("=" * 60)
    print("Example: Rate execution ID", unrated[0]['id'] if unrated else "N/A")
    print("=" * 60)
    print()
    
    if unrated:
        example_id = unrated[0]['id']
        example_tool = unrated[0]['tool_name']
        
        print(f"# Rate {example_tool} (ID: {example_id})")
        print()
        print("Python code:")
        print("```python")
        print("from fccs_agent.config import config")
        print("from fccs_agent.services.feedback_service import FeedbackService")
        print()
        print("feedback_service = FeedbackService(config.database_url)")
        print(f"feedback_service.add_user_feedback(")
        print(f"    execution_id={example_id},")
        print(f"    rating=5,  # 1-5 stars")
        print(f"    feedback=\"Great tool!\"  # Optional")
        print(")")
        print("```")
        print()
        print("cURL command:")
        print("```bash")
        print(f"curl -X POST http://localhost:8080/feedback \\")
        print(f"  -H \"Content-Type: application/json\" \\")
        print(f"  -d '{{")
        print(f"    \"execution_id\": {example_id},")
        print(f"    \"rating\": 5,")
        print(f"    \"feedback\": \"Great tool!\"")
        print(f"  }}'")
        print("```")
        print()

def rate_execution(execution_id, rating, feedback=None):
    """Rate a specific execution."""
    feedback_service = FeedbackService(config.database_url)
    
    if rating < 1 or rating > 5:
        print(f"ERROR: Rating must be between 1 and 5, got {rating}")
        return False
    
    try:
        feedback_service.add_user_feedback(
            execution_id=execution_id,
            rating=rating,
            feedback=feedback
        )
        print(f"SUCCESS: Rated execution {execution_id} with {rating} stars")
        
        # Update RL policy if RL service is available
        rl_service = get_rl_service()
        if rl_service:
            # Get the execution to update RL policy
            executions = feedback_service.get_recent_executions()
            execution_data = next((e for e in executions if e['id'] == execution_id), None)
            
            if execution_data:
                # Note: RL policy update happens automatically when tool is executed
                # This feedback will be used in the next execution
                print("Note: RL policy will be updated on next tool execution")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to rate execution {execution_id}: {e}")
        return False

def batch_rate_successful(limit=10, rating=5):
    """Rate all successful executions that haven't been rated."""
    feedback_service = FeedbackService(config.database_url)
    
    executions = feedback_service.get_recent_executions(limit=limit)
    successful_unrated = [
        e for e in executions 
        if e.get("success") and e.get("user_rating") is None
    ]
    
    if not successful_unrated:
        print("No successful unrated executions found.")
        return
    
    print(f"Rating {len(successful_unrated)} successful executions with {rating} stars...")
    
    rated_count = 0
    for execution in successful_unrated:
        if rate_execution(execution['id'], rating, "Auto-rated: successful execution"):
            rated_count += 1
    
    print(f"SUCCESS: Rated {rated_count} executions")
    print()
    print("RL system will learn from these positive ratings!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Provide feedback on tool executions")
    parser.add_argument("--list", action="store_true", help="List unrated executions")
    parser.add_argument("--rate", type=int, metavar="ID", help="Rate a specific execution ID")
    parser.add_argument("--stars", type=int, metavar="1-5", help="Rating (1-5 stars)")
    parser.add_argument("--comment", type=str, help="Optional feedback comment")
    parser.add_argument("--batch-rate", action="store_true", help="Rate all successful unrated executions")
    parser.add_argument("--limit", type=int, default=10, help="Limit for batch operations")
    
    args = parser.parse_args()
    
    if args.list:
        unrated = list_unrated_executions(limit=args.limit)
        print(f"Found {len(unrated)} unrated executions:")
        for e in unrated:
            status = "SUCCESS" if e.get("success") else "FAILED"
            print(f"  ID {e['id']:4d}: {e['tool_name']:30s} {status}")
    
    elif args.rate:
        if not args.stars:
            print("ERROR: --stars required when using --rate")
            sys.exit(1)
        rate_execution(args.rate, args.stars, args.comment)
    
    elif args.batch_rate:
        stars = args.stars if args.stars else 5
        batch_rate_successful(limit=args.limit, rating=stars)
    
    else:
        # Interactive mode
        provide_feedback_interactive()




