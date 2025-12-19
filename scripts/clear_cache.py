"""Clear Python cache files to ensure fresh code is loaded."""

import os
import shutil
from pathlib import Path


def clear_pycache():
    """Remove all __pycache__ directories and .pyc files."""
    root = Path(__file__).parent.parent
    removed_dirs = 0
    removed_files = 0
    
    print("Clearing Python cache...")
    print(f"Searching in: {root}")
    print()
    
    # Remove __pycache__ directories
    for pycache_dir in root.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            print(f"  Removed: {pycache_dir}")
            removed_dirs += 1
        except Exception as e:
            print(f"  Error removing {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"  Removed: {pyc_file}")
            removed_files += 1
        except Exception as e:
            print(f"  Error removing {pyc_file}: {e}")
    
    print()
    print(f"Cache cleared: {removed_dirs} directories, {removed_files} files removed")
    print()
    print("You can now restart your MCP server to load the updated code.")


if __name__ == "__main__":
    clear_pycache()













