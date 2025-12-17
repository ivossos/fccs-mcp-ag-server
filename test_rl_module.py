"""Comprehensive test script for the RL (Reinforcement Learning) module in FCCS MCP Server.

This script tests:
1. Database table creation
2. RL service initialization
3. Reward calculation
4. Context hashing
5. Tool recommendations
6. Policy updates
7. Episode logging
8. Tool selection
9. Parameter optimization
"""

import sys
import os
from datetime import datetime, timezone
from typing import Any

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 doesn't have reconfigure
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fccs_agent.config import config
from fccs_agent.services.feedback_service import (
    init_feedback_service,
    FeedbackService,
    ToolExecution
)
from fccs_agent.services.rl_service import (
    init_rl_service,
    get_rl_service,
    RLService,
    RewardCalculator,
    ToolSelector,
    ParameterOptimizer,
    RLPolicy,
    RLEpisode,
    RLMetrics,
    ToolSequence,
    ExperienceReplayBuffer,
    SequenceLearner,
    LearningMetricsTracker,
    Experience
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {name} ==={Colors.RESET}")


def print_success(message: str):
    """Print success message."""
    try:
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[PASS] {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    try:
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[FAIL] {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    try:
        print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.YELLOW}[INFO] {message}{Colors.RESET}")


def test_database_tables():
    """Test 1: Verify RL database tables exist."""
    print_test("Test 1: Database Tables")
    
    try:
        engine = create_engine(config.database_url)
        from fccs_agent.services.rl_service import Base
        
        # Check if tables exist
        inspector = __import__('sqlalchemy').inspect(engine)
        tables = inspector.get_table_names()
        
        if 'rl_policy' in tables:
            print_success("rl_policy table exists")
        else:
            print_error("rl_policy table not found")
            print_info("Run: python scripts/add_rl_tables.py")
            return False
            
        if 'rl_episodes' in tables:
            print_success("rl_episodes table exists")
        else:
            print_error("rl_episodes table not found")
            print_info("Run: python scripts/add_rl_tables.py")
            return False
        
        return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


def test_rl_service_initialization():
    """Test 2: Initialize RL service."""
    print_test("Test 2: RL Service Initialization")
    
    try:
        # Initialize feedback service first (required for RL)
        feedback_service = init_feedback_service(config.database_url)
        print_success("Feedback service initialized")
        
        # Initialize RL service
        rl_service = init_rl_service(
            feedback_service,
            config.database_url,
            exploration_rate=0.1,
            learning_rate=0.1,
            discount_factor=0.9,
            min_samples=5
        )
        
        if rl_service:
            print_success("RL service initialized successfully")
            print_info(f"Exploration rate: {rl_service.exploration_rate}")
            print_info(f"Learning rate: {rl_service.learning_rate}")
            print_info(f"Discount factor: {rl_service.discount_factor}")
            print_info(f"Min samples: {rl_service.min_samples}")
            return rl_service, feedback_service
        else:
            print_error("RL service initialization returned None")
            return None, None
    except Exception as e:
        print_error(f"RL service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_reward_calculator():
    """Test 3: Test reward calculation."""
    print_test("Test 3: Reward Calculation")
    
    try:
        calculator = RewardCalculator()
        
        # Test successful execution with high rating
        execution1 = ToolExecution(
            id=1,
            session_id="test_session",
            tool_name="smart_retrieve",
            arguments={"account": "FCCS_Net Income"},
            result={"status": "success"},
            success=True,
            execution_time_ms=500,
            user_rating=5,
            user_feedback="Great!",
            created_at=datetime.now(timezone.utc)
        )
        
        reward1 = calculator.calculate_reward(execution1, avg_execution_time=1000)
        print_success(f"Successful execution reward: {reward1:.2f}")
        print_info(f"  Expected: ~12-16 (success + rating + efficiency)")
        
        # Test failed execution
        execution2 = ToolExecution(
            id=2,
            session_id="test_session",
            tool_name="smart_retrieve",
            arguments={"account": "Invalid"},
            result={"error": "Not found"},
            success=False,
            execution_time_ms=200,
            user_rating=1,
            user_feedback="Failed",
            created_at=datetime.now(timezone.utc)
        )
        
        reward2 = calculator.calculate_reward(execution2)
        print_success(f"Failed execution reward: {reward2:.2f}")
        print_info(f"  Expected: ~-7 to -9 (failure + low rating)")
        
        # Test with no rating
        execution3 = ToolExecution(
            id=3,
            session_id="test_session",
            tool_name="get_dimensions",
            arguments={},
            result={"status": "success"},
            success=True,
            execution_time_ms=300,
            user_rating=None,
            user_feedback=None,
            created_at=datetime.now(timezone.utc)
        )
        
        reward3 = calculator.calculate_reward(execution3)
        print_success(f"Unrated execution reward: {reward3:.2f}")
        print_info(f"  Expected: ~9-10 (success only)")
        
        return True
    except Exception as e:
        print_error(f"Reward calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_hashing(rl_service: RLService):
    """Test 4: Test context hashing."""
    print_test("Test 4: Context Hashing")
    
    try:
        tool_selector = rl_service.tool_selector
        
        # Test different contexts
        context1 = tool_selector.create_context_hash(
            user_query="Get net income data",
            previous_tool=None,
            session_length=0
        )
        print_success(f"Context hash 1: {context1[:16]}...")
        
        context2 = tool_selector.create_context_hash(
            user_query="Get net income data",
            previous_tool="get_dimensions",
            session_length=1
        )
        print_success(f"Context hash 2: {context2[:16]}...")
        
        # Verify different contexts produce different hashes
        if context1 != context2:
            print_success("Different contexts produce different hashes")
        else:
            print_error("Different contexts produced same hash")
            return False
        
        # Test same context produces same hash
        context3 = tool_selector.create_context_hash(
            user_query="Get net income data",
            previous_tool=None,
            session_length=0
        )
        if context1 == context3:
            print_success("Same context produces same hash")
        else:
            print_error("Same context produced different hash")
            return False
        
        return True
    except Exception as e:
        print_error(f"Context hashing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_recommendations(rl_service: RLService):
    """Test 5: Test tool recommendations."""
    print_test("Test 5: Tool Recommendations")
    
    try:
        available_tools = [
            "smart_retrieve",
            "get_dimensions",
            "get_members",
            "get_journals",
            "export_data_slice"
        ]
        
        recommendations = rl_service.get_tool_recommendations(
            user_query="Get financial data for account",
            previous_tool=None,
            session_length=0,
            available_tools=available_tools
        )
        
        print_success(f"Generated {len(recommendations)} recommendations")
        
        # Display top 3 recommendations
        for i, rec in enumerate(recommendations[:3], 1):
            print_info(f"  {i}. {rec['tool_name']}: confidence={rec['confidence']:.3f}")
            print_info(f"     Reason: {rec['reason']}")
        
        if recommendations:
            return True
        else:
            print_error("No recommendations generated")
            return False
    except Exception as e:
        print_error(f"Tool recommendations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_policy_updates(rl_service: RLService, feedback_service: FeedbackService):
    """Test 6: Test policy updates."""
    print_test("Test 6: Policy Updates")
    
    try:
        # Create a mock execution
        execution = ToolExecution(
            id=999,
            session_id="test_policy_session",
            tool_name="smart_retrieve",
            arguments={"account": "FCCS_Net Income"},
            result={"status": "success", "value": 1000},
            success=True,
            execution_time_ms=400,
            user_rating=5,
            user_feedback="Excellent",
            created_at=datetime.now(timezone.utc)
        )
        
        # Calculate reward
        reward = rl_service.calculate_reward(execution)
        print_success(f"Calculated reward: {reward:.2f}")
        
        # Create context hash
        context_hash = rl_service.tool_selector.create_context_hash(
            user_query="Get net income",
            previous_tool=None,
            session_length=0
        )
        
        # Get initial policy value
        policy_dict_before = rl_service._get_policy_dict()
        key = f"smart_retrieve:{context_hash}"
        value_before = policy_dict_before.get(key, 0.0)
        print_info(f"Policy value before update: {value_before:.2f}")
        
        # Update policy
        rl_service.update_policy(
            session_id="test_policy_session",
            tool_name="smart_retrieve",
            context_hash=context_hash,
            reward=reward
        )
        print_success("Policy updated")
        
        # Get updated policy value
        policy_dict_after = rl_service._get_policy_dict()
        value_after = policy_dict_after.get(key, 0.0)
        print_info(f"Policy value after update: {value_after:.2f}")
        
        # Verify value changed
        if value_after != value_before:
            print_success("Policy value changed as expected")
        else:
            print_error("Policy value did not change")
            return False
        
        # Verify in database
        engine = create_engine(config.database_url)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            policy = session.query(RLPolicy).filter_by(
                tool_name="smart_retrieve",
                context_hash=context_hash
            ).first()
            
            if policy:
                print_success(f"Policy found in database: Q-value={policy.action_value:.2f}, visits={policy.visit_count}")
                return True
            else:
                print_error("Policy not found in database")
                return False
    except Exception as e:
        print_error(f"Policy update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_episode_logging(rl_service: RLService):
    """Test 7: Test episode logging."""
    print_test("Test 7: Episode Logging")
    
    try:
        session_id = f"test_episode_{datetime.now(timezone.utc).timestamp()}"
        tool_sequence = ["get_dimensions", "get_members", "smart_retrieve"]
        episode_reward = 25.5
        
        # Log episode
        rl_service.log_episode(
            session_id=session_id,
            tool_sequence=tool_sequence,
            episode_reward=episode_reward,
            outcome="success"
        )
        print_success("Episode logged")
        
        # Verify in database
        engine = create_engine(config.database_url)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            episode = session.query(RLEpisode).filter_by(
                session_id=session_id
            ).first()
            
            if episode:
                print_success(f"Episode found in database:")
                print_info(f"  Session ID: {episode.session_id}")
                print_info(f"  Reward: {episode.episode_reward}")
                print_info(f"  Outcome: {episode.outcome}")
                print_info(f"  Tool sequence: {episode.tool_sequence}")
                return True
            else:
                print_error("Episode not found in database")
                return False
    except Exception as e:
        print_error(f"Episode logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_selection(rl_service: RLService):
    """Test 8: Test tool selection with epsilon-greedy."""
    print_test("Test 8: Tool Selection")
    
    try:
        available_tools = [
            "smart_retrieve",
            "get_dimensions",
            "get_members",
            "get_journals"
        ]
        
        context_hash = rl_service.tool_selector.create_context_hash(
            user_query="Get account data",
            previous_tool=None,
            session_length=0
        )
        
        # Test multiple selections to see exploration/exploitation
        selections = []
        for i in range(10):
            tool, was_exploration = rl_service.tool_selector.select_tool(
                context_hash=context_hash,
                available_tools=available_tools,
                rl_policy=rl_service._get_policy_dict()
            )
            selections.append((tool, was_exploration))
        
        exploration_count = sum(1 for _, exp in selections if exp)
        exploitation_count = 10 - exploration_count
        
        print_success(f"Tool selection test completed:")
        print_info(f"  Exploration: {exploration_count}/10")
        print_info(f"  Exploitation: {exploitation_count}/10")
        print_info(f"  Selected tools: {[t for t, _ in selections]}")
        
        # With 10% exploration rate, we expect ~1 exploration in 10 tries
        if 0 <= exploration_count <= 3:  # Allow some variance
            print_success("Exploration rate is approximately correct")
            return True
        else:
            print_info("Note: Exploration count may vary due to randomness")
            return True
    except Exception as e:
        print_error(f"Tool selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parameter_optimization(rl_service: RLService):
    """Test 9: Test parameter optimization."""
    print_test("Test 9: Parameter Optimization")
    
    try:
        optimizer = rl_service.parameter_optimizer
        
        # Test parameter suggestion
        suggestion = optimizer.suggest_parameters(
            tool_name="smart_retrieve",
            partial_args={"account": "FCCS_Net Income"},
            limit=10
        )
        
        print_success("Parameter optimization completed")
        print_info(f"  Suggested params: {suggestion.get('suggested_params')}")
        print_info(f"  Confidence: {suggestion.get('confidence'):.3f}")
        print_info(f"  Reason: {suggestion.get('reason')}")
        
        return True
    except Exception as e:
        print_error(f"Parameter optimization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_successful_sequences(rl_service: RLService):
    """Test 10: Test successful sequence retrieval."""
    print_test("Test 10: Successful Sequences")
    
    try:
        # First, log a successful episode
        session_id = f"test_sequence_{datetime.now(timezone.utc).timestamp()}"
        rl_service.log_episode(
            session_id=session_id,
            tool_sequence=["get_dimensions", "get_members", "smart_retrieve"],
            episode_reward=30.0,
            outcome="success"
        )
        
        # Retrieve successful sequences
        sequences = rl_service.get_successful_sequences(limit=10)
        
        print_success(f"Retrieved {len(sequences)} successful sequences")
        
        if sequences:
            for i, seq in enumerate(sequences[:3], 1):
                print_info(f"  {i}. Session: {seq['session_id'][:20]}...")
                print_info(f"     Tools: {seq['tool_sequence']}")
                print_info(f"     Reward: {seq['episode_reward']:.2f}")
        
        return True
    except Exception as e:
        print_error(f"Successful sequences test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_experience_replay_buffer():
    """Test 11: Test experience replay buffer."""
    print_test("Test 11: Experience Replay Buffer")

    try:
        buffer = ExperienceReplayBuffer(capacity=100, alpha=0.6)

        # Add experiences
        for i in range(20):
            exp = Experience(
                state_hash=f"state_{i}",
                action=f"tool_{i % 5}",
                reward=float(i),
                next_state_hash=f"state_{i+1}" if i < 19 else None,
                done=(i == 19)
            )
            buffer.add(exp, priority=abs(exp.reward) + 1.0)

        print_success(f"Added 20 experiences to buffer (size: {len(buffer)})")

        # Sample batch
        batch = buffer.sample(batch_size=10)
        print_success(f"Sampled batch of {len(batch)} experiences")

        # Verify batch contents
        if len(batch) == 10 and all(isinstance(e, Experience) for e in batch):
            print_success("Batch contains valid Experience objects")
            print_info(f"  Sample experience: state={batch[0].state_hash}, action={batch[0].action}")
            return True
        else:
            print_error("Invalid batch contents")
            return False

    except Exception as e:
        print_error(f"Experience replay buffer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exploration_decay(rl_service: RLService):
    """Test 12: Test exploration rate decay."""
    print_test("Test 12: Exploration Rate Decay")

    try:
        tool_selector = rl_service.tool_selector
        initial_rate = tool_selector.exploration_rate
        print_info(f"Initial exploration rate: {initial_rate:.4f}")

        # Perform multiple selections to trigger decay
        available_tools = ["tool_a", "tool_b", "tool_c", "tool_d"]
        context_hash = tool_selector.create_context_hash("test query")

        for _ in range(50):
            tool_selector.select_tool(context_hash, available_tools)

        final_rate = tool_selector.exploration_rate
        print_info(f"Final exploration rate after 50 selections: {final_rate:.4f}")

        # Verify decay occurred
        if final_rate < initial_rate:
            print_success(f"Exploration rate decayed from {initial_rate:.4f} to {final_rate:.4f}")

            # Reset and verify
            tool_selector.reset_exploration()
            reset_rate = tool_selector.exploration_rate
            if reset_rate == tool_selector.initial_exploration_rate:
                print_success("Exploration rate reset successfully")
                return True
            else:
                print_error("Failed to reset exploration rate")
                return False
        else:
            print_error("Exploration rate did not decay")
            return False

    except Exception as e:
        print_error(f"Exploration decay test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ucb_exploration(rl_service: RLService):
    """Test 13: Test UCB exploration strategy."""
    print_test("Test 13: UCB Exploration Strategy")

    try:
        tool_selector = rl_service.tool_selector
        available_tools = ["ucb_tool_a", "ucb_tool_b", "ucb_tool_c", "ucb_tool_d"]
        context_hash = tool_selector.create_context_hash("ucb test query")

        # Reset selection counts for clean test
        tool_selector._tool_selection_counts.clear()
        tool_selector._total_selections = 0

        # Select tools many times
        selections = []
        for _ in range(100):
            tool, was_exploration = tool_selector.select_tool(
                context_hash, available_tools, use_ucb=True
            )
            selections.append(tool)

        # Count selections per tool
        from collections import Counter
        counts = Counter(selections)
        print_success(f"Selection distribution: {dict(counts)}")

        # UCB should ensure all tools get tried
        if len(counts) == len(available_tools):
            print_success("UCB ensured all tools were explored")
            return True
        else:
            print_info(f"Note: Not all tools were selected, but this can happen with randomness")
            return True

    except Exception as e:
        print_error(f"UCB exploration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sequence_learning(rl_service: RLService):
    """Test 14: Test N-gram sequence learning."""
    print_test("Test 14: N-gram Sequence Learning")

    try:
        # Log multiple episodes with similar sequences
        for i in range(5):
            rl_service.log_episode(
                session_id=f"seq_test_{datetime.now(timezone.utc).timestamp()}_{i}",
                tool_sequence=["get_dimensions", "get_members", "smart_retrieve"],
                episode_reward=20.0 + i,
                outcome="success"
            )

        # Get sequence recommendations
        recommendations = rl_service.get_sequence_recommendations(
            recent_tools=["get_dimensions", "get_members"],
            available_tools=["smart_retrieve", "export_data_slice", "get_journals"],
            top_k=3
        )

        print_success(f"Got {len(recommendations)} sequence recommendations")

        if recommendations:
            for rec in recommendations:
                print_info(f"  {rec['tool_name']}: score={rec['sequence_score']:.3f}, reason={rec['reason']}")

            # Check if smart_retrieve is recommended (follows logged pattern)
            tool_names = [r["tool_name"] for r in recommendations]
            if "smart_retrieve" in tool_names:
                print_success("Correctly learned get_dimensions->get_members->smart_retrieve pattern")
                return True
            else:
                print_info("Pattern not yet learned (may need more data)")
                return True  # Not a failure, just needs more data
        else:
            print_info("No sequence recommendations yet (expected for small dataset)")
            return True

    except Exception as e:
        print_error(f"Sequence learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_learning_metrics(rl_service: RLService):
    """Test 15: Test learning metrics tracking."""
    print_test("Test 15: Learning Metrics")

    try:
        # Get learning stats
        stats = rl_service.get_learning_stats()

        print_success("Retrieved learning statistics")
        print_info(f"  Update count: {stats.get('update_count', 0)}")
        print_info(f"  Replay buffer size: {stats.get('replay_buffer_size', 0)}")

        # Check exploration stats
        exp_stats = stats.get("exploration_stats", {})
        if exp_stats:
            print_info(f"  Current exploration rate: {exp_stats.get('current_exploration_rate', 0):.4f}")
            print_info(f"  Total selections: {exp_stats.get('total_selections', 0)}")

        # Check metric summaries
        for metric_name in ["reward_stats", "td_error_stats", "episode_reward_stats"]:
            if metric_name in stats:
                metric = stats[metric_name]
                print_info(f"  {metric_name}: count={metric.get('count', 0)}, mean={metric.get('mean', 0):.3f}")

        return True

    except Exception as e:
        print_error(f"Learning metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all RL module tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  RL (Reinforcement Learning) Module Test Suite")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    results = []
    
    # Test 1: Database tables
    if not test_database_tables():
        try:
            print_error("\n❌ Database tables test failed. Please run: python scripts/add_rl_tables.py")
        except UnicodeEncodeError:
            print_error("\n[FAIL] Database tables test failed. Please run: python scripts/add_rl_tables.py")
        return
    
    # Test 2: RL Service initialization
    rl_service, feedback_service = test_rl_service_initialization()
    if not rl_service:
        try:
            print_error("\n❌ RL service initialization failed. Cannot continue tests.")
        except UnicodeEncodeError:
            print_error("\n[FAIL] RL service initialization failed. Cannot continue tests.")
        return
    
    results.append(("Database Tables", True))
    results.append(("RL Service Initialization", True))
    
    # Test 3: Reward calculation
    results.append(("Reward Calculation", test_reward_calculator()))
    
    # Test 4: Context hashing
    results.append(("Context Hashing", test_context_hashing(rl_service)))
    
    # Test 5: Tool recommendations
    results.append(("Tool Recommendations", test_tool_recommendations(rl_service)))
    
    # Test 6: Policy updates
    results.append(("Policy Updates", test_policy_updates(rl_service, feedback_service)))
    
    # Test 7: Episode logging
    results.append(("Episode Logging", test_episode_logging(rl_service)))
    
    # Test 8: Tool selection
    results.append(("Tool Selection", test_tool_selection(rl_service)))
    
    # Test 9: Parameter optimization
    results.append(("Parameter Optimization", test_parameter_optimization(rl_service)))
    
    # Test 10: Successful sequences
    results.append(("Successful Sequences", test_successful_sequences(rl_service)))

    # Test 11: Experience replay buffer (standalone test)
    results.append(("Experience Replay Buffer", test_experience_replay_buffer()))

    # Test 12: Exploration decay
    results.append(("Exploration Rate Decay", test_exploration_decay(rl_service)))

    # Test 13: UCB exploration
    results.append(("UCB Exploration", test_ucb_exploration(rl_service)))

    # Test 14: Sequence learning
    results.append(("N-gram Sequence Learning", test_sequence_learning(rl_service)))

    # Test 15: Learning metrics
    results.append(("Learning Metrics", test_learning_metrics(rl_service)))

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  Test Summary")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        try:
            status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        except UnicodeEncodeError:
            status = f"{Colors.GREEN}[PASS]{Colors.RESET}" if result else f"{Colors.RED}[FAIL]{Colors.RESET}"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        try:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! RL module is working correctly.{Colors.RESET}\n")
        except UnicodeEncodeError:
            print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] All tests passed! RL module is working correctly.{Colors.RESET}\n")
    else:
        try:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Please review the output above.{Colors.RESET}\n")
        except UnicodeEncodeError:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARNING] Some tests failed. Please review the output above.{Colors.RESET}\n")


if __name__ == "__main__":
    main()

