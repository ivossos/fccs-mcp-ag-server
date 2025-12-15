"""Add RL-specific tables to the database.

Run: python scripts/add_rl_tables.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fccs_agent.config import config
from fccs_agent.services.rl_service import Base, RLPolicy, RLEpisode
from sqlalchemy import create_engine

def add_rl_tables():
    """Create RL tables in the database."""
    print(f"Connecting to database: {config.database_url.split('@')[-1] if '@' in config.database_url else 'local'}")
    
    try:
        engine = create_engine(config.database_url)
        
        # Create tables
        print("Creating RL tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Successfully created RL tables:")
        print("   - rl_policy")
        print("   - rl_episodes")
        print("\nRL module is ready to use!")
        
    except Exception as e:
        print(f"❌ Error creating RL tables: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    add_rl_tables()

