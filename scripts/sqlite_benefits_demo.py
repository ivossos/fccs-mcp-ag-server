"""Demonstration of SQLite benefits for the FCCS Agent project."""

import asyncio
import time
import os
from fccs_agent.config import config
from fccs_agent.agent import initialize_agent, execute_tool
from fccs_agent.services.cache_service import get_cache_service

async def run_demo():
    print("=" * 60)
    print("FCCS Agent: SQLite Benefits Demonstration")
    print("=" * 60)
    print()

    # Ensure we use SQLite for the demo if not already configured
    if not config.database_url.startswith("sqlite://"):
        os.environ["DATABASE_URL"] = "sqlite:///./demo_cache.db"
        print(f"Temporary database for demo: {os.environ['DATABASE_URL']}")

    # 1. Initialization
    print("1. Initializing Agent...")
    await initialize_agent()
    cache = get_cache_service()
    if not cache:
        print("Error: Cache service not initialized!")
        return

    # 2. API Caching Demo
    print("\n2. API Response Caching Demo")
    print("-" * 30)
    
    # First call (simulated or real API)
    print("First call to get_members('Account')...")
    start = time.time()
    result1 = await execute_tool("get_members", {"dimension_name": "Account"})
    end = time.time()
    print(f"Time taken: {end - start:.4f}s (Source: {result1.get('source', 'unknown')})")
    
    # Second call (should be from cache)
    print("\nSecond call to get_members('Account') (should be cached)...")
    start = time.time()
    result2 = await execute_tool("get_members", {"dimension_name": "Account"})
    end = time.time()
    print(f"Time taken: {end - start:.4f}s (Source: {result2.get('source', 'unknown')})")
    
    if result2.get("source") == "cache":
        print("Success! Data retrieved from local SQLite cache.")

    # 3. Local Metadata Querying Demo
    print("\n3. Local Metadata Querying Demo (SQL power)")
    print("-" * 30)
    print("Searching for members containing 'Income' in the local cache...")
    
    # Let's ingest some sample data if cache is empty
    cache.update_member("Account", "FCCS_Net Income", {"Alias": "Lucro Líquido", "Account Type": "Revenue"})
    cache.update_member("Account", "FCCS_Operating Income", {"Alias": "Lucro Operacional", "Account Type": "Revenue"})
    
    local_result = await execute_tool("query_local_metadata", {
        "dimension": "Account",
        "member_filter": "%Income%"
    })
    
    print(f"Found {local_result.get('count')} members locally:")
    for item in local_result.get("data", []):
        print(f" - {item['member']} (Alias: {item['properties'].get('Alias')})")

    # 4. Persistence Demo
    print("\n4. Persistence & Analysis Demo")
    print("-" * 30)
    print("SQLite stores execution history for Reinforcement Learning (RL).")
    
    history_result = await execute_tool("get_recent_executions", {"limit": 5})
    print(f"Recent executions stored in SQLite: {len(history_result.get('data', []))}")
    for exec_info in history_result.get("data", []):
        print(f" - Tool: {exec_info['tool_name']}, Time: {exec_info['execution_time_ms']:.2f}ms, Success: {exec_info['success']}")

    print("\n" + "=" * 60)
    print("Conclusion: SQLite helps by providing:")
    print("1. Sub-millisecond data retrieval via Caching")
    print("2. Advanced SQL querying over local metadata")
    print("3. Persistent storage for Reinforcement Learning & Auditing")
    print("4. Zero-latency metadata lookups during tool selection")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_demo())

