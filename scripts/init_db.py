"""Database initialization script for fccs_agent database (SQLite)."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine

from fccs_agent.config import FCCSConfig
from fccs_agent.services.feedback_service import Base, FeedbackService


def ensure_sqlite_directory(db_url: str) -> bool:
    """Ensure the directory for SQLite database file exists.

    Args:
        db_url: SQLite database URL (e.g., sqlite:///./data/fccs_agent.db)

    Returns:
        True if directory exists or was created, False on error
    """
    try:
        # Extract file path from SQLite URL
        # sqlite:///./data/fccs_agent.db -> ./data/fccs_agent.db
        if db_url.startswith("sqlite:///"):
            file_path = db_url[10:]  # Remove "sqlite:///"
        elif db_url.startswith("sqlite://"):
            file_path = db_url[9:]   # Remove "sqlite://"
        else:
            print(f"Error: Not a SQLite URL: {db_url}")
            return False

        # Get directory path
        dir_path = Path(file_path).parent

        if dir_path and str(dir_path) != ".":
            os.makedirs(dir_path, exist_ok=True)
            print(f"Ensured directory exists: {dir_path}")

        return True

    except Exception as e:
        print(f"Error creating directory: {e}")
        return False


def init_schema(db_url: str) -> bool:
    """Initialize the database schema (create tables).

    Args:
        db_url: Full database URL

    Returns:
        True if schema was initialized successfully, False on error
    """
    try:
        print("Initializing database schema...")
        service = FeedbackService(db_url)
        print("Database schema initialized successfully.")
        print("Created tables:")
        print("  - tool_executions")
        print("  - tool_metrics")
        return True
    except Exception as e:
        print(f"Error initializing schema: {e}")
        return False


def main():
    """Main function to initialize the database."""
    print("=" * 60)
    print("FCCS Agent Database Initialization (SQLite)")
    print("=" * 60)
    print()

    # Load configuration
    try:
        config = FCCSConfig()
        db_url = config.database_url
        print(f"Database URL: {db_url}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have a .env file or set DATABASE_URL environment variable.")
        sys.exit(1)

    # Ensure SQLite directory exists
    if db_url.startswith("sqlite://"):
        print("\nStep 1: Ensuring database directory exists...")
        if not ensure_sqlite_directory(db_url):
            sys.exit(1)

    # Initialize schema
    print("\nStep 2: Initializing database schema...")
    if not init_schema(db_url):
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)

    # Print database location for SQLite
    if db_url.startswith("sqlite:///"):
        file_path = db_url[10:]
        abs_path = Path(file_path).resolve()
        print(f"\nSQLite database location: {abs_path}")


if __name__ == "__main__":
    main()
