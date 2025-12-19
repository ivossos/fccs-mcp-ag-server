#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick script to check the current status of the RL algorithm.
Shows learning statistics, confidence scores, and performance metrics.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from fccs_agent.config import config
from fccs_agent.services.feedback_service import FeedbackService
from fccs_agent.services.rl_service import init_rl_service, get_rl_service

def check_rl_status():
    """Check and display current RL algorithm status."""
    print("Checking RL Algorithm Status...\n")
    
    # Initialize services
    feedback_service = FeedbackService(config.database_url)
    rl_service = init_rl_service(
        feedback_service=feedback_service,
        db_url=config.database_url,
        exploration_rate=config.rl_exploration_rate,
        learning_rate=config.rl_learning_rate,
        discount_factor=config.rl_discount_factor,
        min_samples=config.rl_min_samples
    )
    
    # Get learning statistics
    print("=" * 60)
    print("RL LEARNING STATISTICS")
    print("=" * 60)
    
    stats = rl_service.get_learning_stats()
    
    if stats:
        print(f"\nPolicy Updates: {stats.get('update_count', 0)}")
        print(f"Replay Buffer Size: {stats.get('replay_buffer_size', 0)}")
        
        # Exploration stats
        exploration_stats = stats.get('exploration_stats', {})
        if exploration_stats:
            print(f"\nExploration Statistics:")
            print(f"   • Current Exploration Rate: {exploration_stats.get('current_exploration_rate', 0):.3f}")
            print(f"   • Total Selections: {exploration_stats.get('total_selections', 0)}")
            print(f"   • Tool Selection Counts: {len(exploration_stats.get('tool_selection_counts', {}))} tools")
        
        # Metric summaries
        print(f"\nMetric Summaries (last 100):")
        for metric_name in ["reward", "td_error", "episode_reward", "exploration_rate"]:
            metric_key = f"{metric_name}_stats"
            if metric_key in stats:
                metric_stats = stats[metric_key]
                if metric_stats.get("count", 0) > 0:
                    print(f"   • {metric_name.replace('_', ' ').title()}:")
                    print(f"     - Count: {metric_stats.get('count', 0)}")
                    print(f"     - Mean: {metric_stats.get('mean', 0):.3f}")
                    print(f"     - Latest: {metric_stats.get('latest', 0):.3f}")
    else:
        print("WARNING: No learning statistics available yet.")
    
    # Get policy statistics
    print("\n" + "=" * 60)
    print("RL POLICY STATISTICS")
    print("=" * 60)
    
    policy_dict = rl_service._get_policy_dict()
    total_policies = len(policy_dict)
    
    if total_policies > 0:
        avg_action_value = sum(policy_dict.values()) / total_policies
        positive_policies = sum(1 for v in policy_dict.values() if v > 0)
        
        print(f"\nTotal Policies: {total_policies}")
        print(f"Average Q-Value (Action Value): {avg_action_value:.3f}")
        print(f"Positive Q-Values: {positive_policies} ({positive_policies/total_policies*100:.1f}%)")
        
        # Group by tool and calculate average confidence
        tool_confidences = {}
        tool_q_values = {}
        
        for key, action_value in policy_dict.items():
            if ":" in key:
                tool_name, context = key.split(":", 1)
                confidence = rl_service.get_tool_confidence(tool_name, context)
                
                if tool_name not in tool_confidences:
                    tool_confidences[tool_name] = []
                    tool_q_values[tool_name] = []
                
                tool_confidences[tool_name].append(confidence)
                tool_q_values[tool_name].append(action_value)
        
        # Calculate averages per tool
        tool_avg_confidences = {
            tool: sum(confs) / len(confs) 
            for tool, confs in tool_confidences.items()
        }
        tool_avg_q_values = {
            tool: sum(qs) / len(qs)
            for tool, qs in tool_q_values.items()
        }
        
        if tool_avg_confidences:
            print(f"\nTop 10 Tools by RL Confidence:")
            sorted_tools = sorted(tool_avg_confidences.items(), key=lambda x: x[1], reverse=True)
            for i, (tool_name, confidence) in enumerate(sorted_tools[:10], 1):
                avg_q = tool_avg_q_values.get(tool_name, 0)
                status = "[OK]" if confidence > 0.75 else "[LEARNING]" if confidence > 0.5 else "[LOW]"
                print(f"   {i:2d}. {status} {tool_name:35s} {confidence*100:5.1f}% (Q: {avg_q:+.2f})")
            
            overall_avg_confidence = sum(tool_avg_confidences.values()) / len(tool_avg_confidences) * 100
            print(f"\nOverall Average RL Confidence: {overall_avg_confidence:.1f}%")
            
            # Confidence interpretation
            if overall_avg_confidence >= 75:
                print("   Status: Excellent - System is well-trained!")
            elif overall_avg_confidence >= 60:
                print("   Status: Good - System is learning well")
            elif overall_avg_confidence >= 50:
                print("   Status: Learning - System needs more positive feedback")
            else:
                print("   Status: Early Stage - System needs more training data")
    else:
        print("\nWARNING: No policies learned yet. The RL system needs more tool executions.")
    
    # Get tool metrics from feedback service
    print("\n" + "=" * 60)
    print("TOOL PERFORMANCE METRICS")
    print("=" * 60)
    
    tool_metrics = feedback_service.get_tool_metrics()
    
    if tool_metrics:
        total_tools = len(tool_metrics)
        avg_success_rate = sum(m.get("success_rate", 0) for m in tool_metrics) / total_tools if total_tools > 0 else 0
        avg_rating = sum(m.get("avg_user_rating", 0) or 0 for m in tool_metrics) / total_tools if total_tools > 0 else 0
        
        print(f"\nTotal Tools Tracked: {total_tools}")
        print(f"Average Success Rate: {avg_success_rate*100:.1f}%")
        print(f"Average User Rating: {avg_rating:.2f}/5.0")
        
        # Show top performing tools
        sorted_by_success = sorted(tool_metrics, key=lambda x: x.get("success_rate", 0), reverse=True)
        print(f"\nTop 5 Tools by Success Rate:")
        for i, metric in enumerate(sorted_by_success[:5], 1):
            tool_name = metric.get("tool_name", "unknown")
            success_rate = metric.get("success_rate", 0) * 100
            rating = metric.get("avg_user_rating", 0) or 0
            calls = metric.get("total_calls", 0)
            print(f"   {i}. {tool_name:35s} {success_rate:5.1f}% success, {rating:.1f} stars ({calls} calls)")
    else:
        print("\nWARNING: No tool metrics available yet.")
    
    # Configuration
    print("\n" + "=" * 60)
    print("RL CONFIGURATION")
    print("=" * 60)
    
    print(f"\nCurrent Settings:")
    print(f"   • RL Enabled: {config.rl_enabled}")
    print(f"   • Learning Rate (α): {config.rl_learning_rate}")
    print(f"   • Discount Factor (γ): {config.rl_discount_factor}")
    print(f"   • Exploration Rate (ε): {config.rl_exploration_rate}")
    print(f"   • Min Samples: {config.rl_min_samples}")
    
    print("\n" + "=" * 60)
    print("Status Check Complete!")
    print("=" * 60)
    print("\nTips:")
    print("   • Run 'python boost_rl_confidence.py' to bootstrap with synthetic data")
    print("   • Use the dashboard: 'streamlit run tool_stats_dashboard.py'")
    print("   • Provide feedback (ratings) on tool executions to improve learning")
    print()


if __name__ == "__main__":
    try:
        check_rl_status()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

