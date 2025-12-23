"""Fix NULL values in tool_metrics table."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.services.feedback_service import FeedbackService, ToolMetrics
from sqlalchemy import update


def fix_null_metrics():
    """Fix any NULL values in the tool_metrics table."""
    print("=" * 60)
    print("Fixing NULL values in tool_metrics table")
    print("=" * 60)
    print()

    try:
        config = load_config()
        service = FeedbackService(config.database_url)
        
        with service.Session() as session:
            # Update all NULL values to 0
            session.execute(
                update(ToolMetrics)
                .where(ToolMetrics.total_calls.is_(None))
                .values(total_calls=0)
            )
            session.execute(
                update(ToolMetrics)
                .where(ToolMetrics.success_count.is_(None))
                .values(success_count=0)
            )
            session.execute(
                update(ToolMetrics)
                .where(ToolMetrics.failure_count.is_(None))
                .values(failure_count=0)
            )
            session.execute(
                update(ToolMetrics)
                .where(ToolMetrics.avg_execution_time_ms.is_(None))
                .values(avg_execution_time_ms=0.0)
            )
            session.commit()
            
            # Count fixed records
            total = session.query(ToolMetrics).count()
            print(f"Checked {total} metrics records")
            print("All NULL values have been fixed (set to 0)")
            print()
            print("=" * 60)
            print("Database fix completed successfully!")
            print("=" * 60)
            
    except Exception as e:
        print(f"Error fixing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fix_null_metrics()
















