"""Interactive tool to evaluate recent tool executions."""

import sys
from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService

def get_rating_input(prompt: str) -> int:
    """Get rating from user (1-5)."""
    while True:
        try:
            rating = input(prompt).strip()
            if not rating:
                return None
            rating = int(rating)
            if 1 <= rating <= 5:
                return rating
            print("Rating must be between 1 and 5. Try again.")
        except ValueError:
            print("Please enter a number between 1 and 5.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None

def main():
    """Interactive evaluation tool."""
    print("=" * 70)
    print("Interactive Evaluation Tool")
    print("=" * 70)
    print()
    
    try:
        feedback_service = FeedbackService(config.database_url)
    except Exception as e:
        print(f"ERROR: Could not connect to feedback service: {e}")
        return 1
    
    # Get recent unrated executions
    print("Fetching recent unrated executions...")
    all_executions = feedback_service.get_recent_executions(limit=50)
    unrated = [e for e in all_executions if e.get("user_rating") is None]
    
    if not unrated:
        print("\nNo unrated executions found!")
        print("Run some tools first, then come back to evaluate them.")
        return 0
    
    print(f"\nFound {len(unrated)} unrated executions ready for evaluation")
    print()
    
    # Show unrated executions
    print("Unrated Executions:")
    print("-" * 70)
    for i, e in enumerate(unrated[:20], 1):
        status = "✓" if e.get("success") else "✗"
        tool_name = e.get("tool_name", "unknown")
        exec_id = e.get("id", "?")
        timestamp = str(e.get("created_at", "?"))[:19]  # Remove microseconds
        
        # Show brief result preview if available
        result_preview = ""
        result = e.get("result", {})
        if isinstance(result, dict):
            if "status" in result:
                result_preview = f" | Status: {result['status']}"
            elif "data" in result:
                result_preview = " | Has data"
        
        print(f"{i:2d}. ID: {exec_id:4d} | {status} {tool_name:28s} | {timestamp}{result_preview}")
    
    if len(unrated) > 20:
        print(f"\n... and {len(unrated) - 20} more (showing first 20)")
    
    print()
    print("Options:")
    print("  1. Rate a specific execution by ID")
    print("  2. Rate multiple executions (batch)")
    print("  3. Auto-rate all successful executions with 5 stars")
    print("  4. Exit")
    print()
    
    choice = input("Choose an option (1-4): ").strip()
    
    if choice == "1":
        # Rate single execution
        exec_id_str = input("\nEnter execution ID to rate: ").strip()
        try:
            exec_id = int(exec_id_str)
            execution = next((e for e in unrated if e.get("id") == exec_id), None)
            
            if not execution:
                print(f"Execution {exec_id} not found in unrated list.")
                return 1
            
            print(f"\nExecution Details:")
            print(f"  ID: {exec_id}")
            print(f"  Tool: {execution.get('tool_name')}")
            print(f"  Status: {'SUCCESS' if execution.get('success') else 'FAILED'}")
            print(f"  Time: {execution.get('created_at')}")
            print()
            
            rating = get_rating_input("Enter rating (1-5 stars): ")
            if rating is None:
                return 0
            
            feedback_text = input("Optional feedback (press Enter to skip): ").strip()
            if not feedback_text:
                feedback_text = None
            
            # Submit feedback
            try:
                feedback_service.add_user_feedback(
                    execution_id=exec_id,
                    rating=rating,
                    feedback=feedback_text
                )
                print(f"\n✓ Successfully rated execution {exec_id} with {rating} stars!")
                if feedback_text:
                    print(f"  Feedback: {feedback_text}")
            except Exception as e:
                print(f"\n✗ Error rating execution: {e}")
                return 1
        
        except ValueError:
            print("Invalid execution ID. Must be a number.")
            return 1
    
    elif choice == "2":
        # Batch rate
        print("\nBatch Rating Mode")
        print("Enter execution IDs separated by commas, or 'all' for all unrated")
        exec_ids_str = input("Execution IDs: ").strip()
        
        if exec_ids_str.lower() == "all":
            exec_ids = [e.get("id") for e in unrated]
        else:
            try:
                exec_ids = [int(x.strip()) for x in exec_ids_str.split(",")]
            except ValueError:
                print("Invalid format. Use comma-separated numbers or 'all'")
                return 1
        
        rating = get_rating_input("Enter rating for all (1-5 stars): ")
        if rating is None:
            return 0
        
        feedback_text = input("Optional feedback for all (press Enter to skip): ").strip()
        if not feedback_text:
            feedback_text = None
        
        print(f"\nRating {len(exec_ids)} executions with {rating} stars...")
        success_count = 0
        
        for exec_id in exec_ids:
            try:
                feedback_service.add_user_feedback(
                    execution_id=exec_id,
                    rating=rating,
                    feedback=feedback_text
                )
                success_count += 1
            except Exception as e:
                print(f"  ✗ Failed to rate {exec_id}: {e}")
        
        print(f"\n✓ Successfully rated {success_count}/{len(exec_ids)} executions!")
    
    elif choice == "3":
        # Auto-rate successful
        successful = [e for e in unrated if e.get("success")]
        if not successful:
            print("\nNo successful unrated executions found.")
            return 0
        
        print(f"\nFound {len(successful)} successful unrated executions")
        confirm = input(f"Rate all {len(successful)} with 5 stars? (yes/no): ").strip().lower()
        
        if confirm in ["yes", "y"]:
            print("\nRating successful executions...")
            success_count = 0
            
            for e in successful:
                try:
                    feedback_service.add_user_feedback(
                        execution_id=e.get("id"),
                        rating=5,
                        feedback="Auto-rated: successful execution"
                    )
                    success_count += 1
                except Exception as e:
                    pass  # Skip errors
            
            print(f"\n✓ Successfully rated {success_count} executions with 5 stars!")
            print("RL system will learn from these positive ratings!")
        else:
            print("Cancelled.")
    
    elif choice == "4":
        print("Exiting...")
        return 0
    
    else:
        print("Invalid choice.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)



