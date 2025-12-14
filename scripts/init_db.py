"""Database initialization script for fccs_agent database."""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from fccs_agent.config import FCCSConfig
from fccs_agent.services.feedback_service import Base, FeedbackService


def create_postgres_database_if_not_exists(db_url: str) -> bool:
    """Create the PostgreSQL database if it doesn't exist.
    
    Args:
        db_url: Full database URL including database name
        
    Returns:
        True if database was created or already exists, False on error
    """
    try:
        # Ensure we're using psycopg driver (psycopg3)
        if db_url.startswith("postgresql+psycopg://"):
            url_with_driver = db_url
        elif db_url.startswith("postgresql://"):
            # Convert to use psycopg3
            url_with_driver = db_url.replace("postgresql://", "postgresql+psycopg://")
        else:
            print(f"Error: Unsupported database URL format: {db_url}")
            print("Expected format: postgresql+psycopg://user:password@host:port/database")
            return False
        
        # Split to get base URL and database name
        parts = url_with_driver.split("/")
        if len(parts) < 4:
            print(f"Error: Invalid database URL format: {db_url}")
            return False
        
        base_url = "/".join(parts[:-1])  # Everything except the database name
        database_name = parts[-1].split("?")[0]  # Remove query parameters if any
        
        # Connect to postgres database to create the target database
        # Keep the psycopg driver for the admin connection
        admin_url = f"{base_url}/postgres"
        print(f"Connecting to PostgreSQL server to create database '{database_name}'...")
        
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": database_name}
            )
            exists = result.fetchone() is not None
            
            if exists:
                print(f"Database '{database_name}' already exists.")
            else:
                # Create the database
                conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                print(f"Database '{database_name}' created successfully.")
        
        admin_engine.dispose()
        return True
        
    except OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. The connection credentials are correct")
        print("  3. The user has permission to create databases")
        return False
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def init_schema(db_url: str) -> bool:
    """Initialize the database schema (create tables).
    
    Args:
        db_url: Full database URL including database name
        
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
    print("FCCS Agent Database Initialization")
    print("=" * 60)
    print()
    
    # Load configuration
    try:
        config = FCCSConfig()
        db_url = config.database_url
        # Mask password in display
        if "@" in db_url:
            display_url = db_url.split("@")[1]
        else:
            display_url = "***"
        print(f"Database URL: {display_url}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have a .env file or set DATABASE_URL environment variable.")
        sys.exit(1)
    
    # Check if SQLite is being used
    if db_url.startswith("sqlite://"):
        print("\n" + "!" * 60)
        print("WARNING: SQLite database detected!")
        print("!" * 60)
        print("\nThis script is designed for PostgreSQL database setup.")
        print(f"Current DATABASE_URL: {db_url}")
        print("\nTo use PostgreSQL, update your .env file or DATABASE_URL environment variable:")
        print("  DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/fccs_agent")
        print("\nFor SQLite, the database file will be created automatically when the")
        print("application starts. No initialization script is needed.")
        print("\nIf you want to proceed with SQLite schema initialization anyway, it will")
        print("be created automatically when FeedbackService initializes.")
        response = input("\nDo you want to continue with SQLite? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Exiting. Please update DATABASE_URL to use PostgreSQL.")
            sys.exit(1)
        # For SQLite, just initialize schema (database file will be created automatically)
        print("\nInitializing SQLite database schema...")
        if not init_schema(db_url):
            sys.exit(1)
        print("\n" + "=" * 60)
        print("SQLite database initialization completed!")
        print("=" * 60)
        return
    
    # Step 1: Create PostgreSQL database if it doesn't exist
    print("\nStep 1: Checking PostgreSQL database existence...")
    if not create_postgres_database_if_not_exists(db_url):
        sys.exit(1)
    
    # Step 2: Initialize schema
    print("\nStep 2: Initializing database schema...")
    if not init_schema(db_url):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("PostgreSQL database initialization completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

