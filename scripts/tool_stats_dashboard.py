"""Tool Execution Statistics Dashboard - Streamlit web dashboard."""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.services.feedback_service import (
    init_feedback_service,
    get_feedback_service,
    FeedbackService
)
from fccs_agent.services.rl_service import (
    init_rl_service,
    get_rl_service
)


def init_dashboard():
    """Initialize dashboard, feedback service, and RL service."""
    try:
        config = load_config()
        feedback_service = init_feedback_service(config.database_url)
        
        # Initialize RL service if enabled
        rl_service = None
        if config.rl_enabled:
            try:
                rl_service = init_rl_service(
                    feedback_service,
                    config.database_url,
                    exploration_rate=config.rl_exploration_rate,
                    learning_rate=config.rl_learning_rate,
                    discount_factor=config.rl_discount_factor,
                    min_samples=config.rl_min_samples
                )
            except Exception as e:
                # RL service initialization is optional
                pass
        
        return feedback_service, rl_service, True
    except Exception as e:
        st.error(f"❌ Failed to initialize dashboard: {e}")
        return None, None, False


def format_time(ms: float) -> str:
    """Format milliseconds to human-readable time."""
    if ms < 1000:
        return f"{ms:.1f} ms"
    elif ms < 60000:
        return f"{ms/1000:.2f} s"
    else:
        return f"{ms/60000:.2f} min"


def run_dashboard():
    """Run the Streamlit dashboard."""
    st.set_page_config(
        page_title="Tool Execution Statistics",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Tool Execution Statistics Dashboard")
    st.markdown("Oracle FCCS Agentic MCP Server - Tool Performance Analytics")
    st.markdown("---")
    
    # Initialize feedback service and RL service
    feedback_service, rl_service, connected = init_dashboard()
    
    if not connected or not feedback_service:
        st.error("❌ Failed to connect to database")
        st.info("""
        Please check:
        1. Your `.env` file has correct `DATABASE_URL`
        2. Database has been initialized: `python scripts/init_db.py`
        """)
        st.stop()
    
    st.success("✅ Connected to database")
    
    # Show RL status
    if rl_service:
        st.info("🤖 Reinforcement Learning Engine: **Enabled**")
    else:
        st.warning("⚠️ Reinforcement Learning Engine: **Disabled** (Set RL_ENABLED=true in .env to enable)")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Tool filter
        all_metrics = feedback_service.get_tool_metrics()
        tool_names = [m["tool_name"] for m in all_metrics]
        tool_names.insert(0, "All Tools")
        selected_tool = st.selectbox("Filter by Tool", tool_names)
        
        # Time range filter
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
            index=3
        )
        
        # Limit for recent executions
        execution_limit = st.slider("Recent Executions Limit", 10, 200, 50)
        
        st.markdown("---")
        st.header("ℹ️ Info")
        st.info("""
        This dashboard shows:
        - Tool execution metrics
        - Success rates
        - Performance statistics
        - Recent executions
        - RL scoring & learning metrics
        """)
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Get metrics
    tool_filter = None if selected_tool == "All Tools" else selected_tool
    metrics = feedback_service.get_tool_metrics(tool_filter)
    
    if not metrics:
        st.warning("⚠️ No tool execution data available yet.")
        st.info("""
        Tool executions will appear here once tools are used.
        Try executing some FCCS tools to see statistics.
        """)
        st.stop()
    
    # Calculate aggregate statistics
    total_tools = len(metrics)
    total_calls = sum(m.get("total_calls", 0) for m in metrics)
    total_success = sum(m.get("total_calls", 0) * m.get("success_rate", 0) for m in metrics)
    overall_success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0
    avg_execution_time = sum(m.get("avg_execution_time_ms", 0) for m in metrics) / total_tools if total_tools > 0 else 0
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tools", total_tools)
    
    with col2:
        st.metric("Total Executions", f"{total_calls:,}")
    
    with col3:
        st.metric(
            "Overall Success Rate",
            f"{overall_success_rate:.1f}%",
            delta=f"{overall_success_rate - 95:.1f}%" if overall_success_rate >= 95 else None
        )
    
    with col4:
        st.metric("Avg Execution Time", format_time(avg_execution_time))
    
    st.markdown("---")
    
    # Tool Metrics Table and Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Tool Performance Overview")
        
        # Prepare data for visualization
        df_metrics = pd.DataFrame(metrics)
        df_metrics = df_metrics.sort_values("total_calls", ascending=False)
        
        # Bar chart: Total calls per tool
        fig_calls = px.bar(
            df_metrics.head(15),
            x="tool_name",
            y="total_calls",
            title="Total Executions by Tool (Top 15)",
            labels={"tool_name": "Tool", "total_calls": "Total Calls"},
            color="total_calls",
            color_continuous_scale="Blues"
        )
        fig_calls.update_layout(
            height=400,
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig_calls, use_container_width=True)
    
    with col2:
        st.subheader("✅ Success Rate by Tool")
        
        # Bar chart: Success rate per tool
        df_metrics_success = df_metrics.copy()
        df_metrics_success["success_rate_pct"] = df_metrics_success["success_rate"] * 100
        
        fig_success = px.bar(
            df_metrics_success.head(15),
            x="tool_name",
            y="success_rate_pct",
            title="Success Rate by Tool (Top 15)",
            labels={"tool_name": "Tool", "success_rate_pct": "Success Rate (%)"},
            color="success_rate_pct",
            color_continuous_scale="Greens",
            range_y=[0, 100]
        )
        fig_success.update_layout(
            height=400,
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig_success, use_container_width=True)
    
    st.markdown("---")
    
    # Performance Metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏱️ Average Execution Time")
        
        df_metrics_time = df_metrics.copy()
        df_metrics_time = df_metrics_time[df_metrics_time["avg_execution_time_ms"] > 0]
        df_metrics_time = df_metrics_time.sort_values("avg_execution_time_ms", ascending=False)
        
        if len(df_metrics_time) > 0:
            fig_time = px.bar(
                df_metrics_time.head(15),
                x="tool_name",
                y="avg_execution_time_ms",
                title="Average Execution Time by Tool (Top 15)",
                labels={"tool_name": "Tool", "avg_execution_time_ms": "Time (ms)"},
                color="avg_execution_time_ms",
                color_continuous_scale="Oranges"
            )
            fig_time.update_layout(
                height=400,
                xaxis_tickangle=-45,
                showlegend=False
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No execution time data available")
    
    with col2:
        st.subheader("📈 Tool Usage Distribution")
        
        # Pie chart: Distribution of tool calls
        fig_pie = px.pie(
            df_metrics.head(10),
            values="total_calls",
            names="tool_name",
            title="Tool Usage Distribution (Top 10)"
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed Metrics Table
    st.subheader("📋 Detailed Tool Metrics")
    
    # Prepare table data
    df_table = pd.DataFrame(metrics)
    df_table = df_table.sort_values("total_calls", ascending=False)
    df_table["success_rate_pct"] = (df_table["success_rate"] * 100).round(2)
    df_table["success_count"] = (df_table["total_calls"] * df_table["success_rate"]).round(0).astype(int)
    df_table["failure_count"] = df_table["total_calls"] - df_table["success_count"]
    
    # Format columns for display
    display_df = df_table[[
        "tool_name",
        "total_calls",
        "success_count",
        "failure_count",
        "success_rate_pct",
        "avg_execution_time_ms"
    ]].copy()
    
    display_df.columns = [
        "Tool Name",
        "Total Calls",
        "Success Count",
        "Failure Count",
        "Success Rate (%)",
        "Avg Time (ms)"
    ]
    
    # Format the dataframe
    styled_df = display_df.style.format({
        "Success Rate (%)": "{:.2f}%",
        "Avg Time (ms)": "{:.2f}"
    })
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Recent Executions
    st.subheader("🕐 Recent Tool Executions")
    
    tool_filter_exec = None if selected_tool == "All Tools" else selected_tool
    recent_executions = feedback_service.get_recent_executions(tool_filter_exec, execution_limit)
    
    if recent_executions:
        df_executions = pd.DataFrame(recent_executions)
        df_executions["created_at"] = pd.to_datetime(df_executions["created_at"])
        df_executions = df_executions.sort_values("created_at", ascending=False)
        
        # Format execution time
        df_executions["execution_time_formatted"] = df_executions["execution_time_ms"].apply(format_time)
        
        # Display table
        display_exec_df = df_executions[[
            "tool_name",
            "success",
            "execution_time_formatted",
            "user_rating",
            "created_at"
        ]].copy()
        
        display_exec_df.columns = [
            "Tool",
            "Success",
            "Execution Time",
            "User Rating",
            "Timestamp"
        ]
        
        # Format success column
        display_exec_df["Success"] = display_exec_df["Success"].apply(
            lambda x: "✅" if x else "❌"
        )
        
        # Format timestamp
        display_exec_df["Timestamp"] = display_exec_df["Timestamp"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "N/A"
        )
        
        st.dataframe(
            display_exec_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Timeline chart
        st.subheader("📅 Execution Timeline")
        df_timeline = df_executions.copy()
        df_timeline["hour"] = df_timeline["created_at"].dt.floor("H")
        timeline_counts = df_timeline.groupby("hour").size().reset_index(name="count")
        
        fig_timeline = px.line(
            timeline_counts,
            x="hour",
            y="count",
            title="Tool Executions Over Time",
            labels={"hour": "Time", "count": "Number of Executions"},
            markers=True
        )
        fig_timeline.update_layout(height=300)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No recent executions found")
    
    # RL Scoring Section
    if rl_service:
        st.markdown("---")
        st.subheader("🤖 Reinforcement Learning Scoring & Metrics")
        
        try:
            # Get RL policy data
            policy_dict = rl_service._get_policy_dict()
            learning_stats = rl_service.get_learning_stats()
            
            # Extract tool-level action values
            tool_action_values = {}
            for key, action_value in policy_dict.items():
                if ":" in key:
                    tool_name, context_hash = key.split(":", 1)
                    if tool_name not in tool_action_values:
                        tool_action_values[tool_name] = []
                    tool_action_values[tool_name].append(action_value)
            
            # Calculate average action values per tool
            tool_avg_actions = {
                tool: sum(values) / len(values) if values else 0.0
                for tool, values in tool_action_values.items()
            }
            
            # Get tool metrics for comparison
            tool_metrics_dict = {m["tool_name"]: m for m in metrics}
            
            # Combine metrics with RL scores
            rl_data = []
            for tool_name in set(list(tool_avg_actions.keys()) + list(tool_metrics_dict.keys())):
                avg_action = tool_avg_actions.get(tool_name, 0.0)
                tool_metric = tool_metrics_dict.get(tool_name, {})
                
                # Calculate RL confidence
                context_hash = "default"  # Use default context for display
                confidence = rl_service.get_tool_confidence(tool_name, context_hash)
                
                rl_data.append({
                    "tool_name": tool_name,
                    "action_value": avg_action,
                    "confidence": confidence * 100,  # Convert to percentage
                    "total_calls": tool_metric.get("total_calls", 0),
                    "success_rate": tool_metric.get("success_rate", 0) * 100
                })
            
            if rl_data:
                df_rl = pd.DataFrame(rl_data)
                df_rl = df_rl.sort_values("action_value", ascending=False)
                
                # RL Key Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_action_value = df_rl["action_value"].mean()
                    st.metric("Avg Action Value (Q)", f"{avg_action_value:.3f}")
                
                with col2:
                    max_action_value = df_rl["action_value"].max()
                    st.metric("Max Action Value", f"{max_action_value:.3f}")
                
                with col3:
                    avg_confidence = df_rl["confidence"].mean()
                    st.metric("Avg RL Confidence", f"{avg_confidence:.1f}%")
                
                with col4:
                    update_count = learning_stats.get("update_count", 0)
                    st.metric("Policy Updates", f"{update_count:,}")
                
                st.markdown("---")
                
                # RL Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 RL Action Values (Q-values) by Tool")
                    df_rl_top = df_rl.head(15).copy()
                    df_rl_top = df_rl_top.sort_values("action_value", ascending=True)
                    
                    fig_rl = px.bar(
                        df_rl_top,
                        x="action_value",
                        y="tool_name",
                        orientation="h",
                        title="RL Action Values (Top 15 Tools)",
                        labels={"action_value": "Action Value (Q)", "tool_name": "Tool"},
                        color="action_value",
                        color_continuous_scale="Viridis"
                    )
                    fig_rl.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_rl, use_container_width=True)
                
                with col2:
                    st.subheader("💡 RL Confidence Scores by Tool")
                    df_rl_conf = df_rl.head(15).copy()
                    df_rl_conf = df_rl_conf.sort_values("confidence", ascending=True)
                    
                    fig_conf = px.bar(
                        df_rl_conf,
                        x="confidence",
                        y="tool_name",
                        orientation="h",
                        title="RL Confidence Scores (Top 15 Tools)",
                        labels={"confidence": "Confidence (%)", "tool_name": "Tool"},
                        color="confidence",
                        color_continuous_scale="Plasma",
                        range_x=[0, 100]
                    )
                    fig_conf.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_conf, use_container_width=True)
                
                st.markdown("---")
                
                # Learning Statistics
                st.subheader("📊 RL Learning Statistics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Exploration stats
                    exploration_stats = learning_stats.get("exploration_stats", {})
                    st.markdown("**Exploration Statistics**")
                    st.json({
                        "Current Exploration Rate": f"{exploration_stats.get('current_rate', 0):.3f}",
                        "Total Explorations": exploration_stats.get("total_explorations", 0),
                        "Total Exploitations": exploration_stats.get("total_exploitations", 0),
                        "Exploration Ratio": f"{exploration_stats.get('exploration_ratio', 0):.2%}"
                    })
                
                with col2:
                    # Learning metrics
                    st.markdown("**Learning Metrics**")
                    metrics_display = {
                        "Replay Buffer Size": learning_stats.get("replay_buffer_size", 0),
                        "Policy Updates": learning_stats.get("update_count", 0)
                    }
                    
                    # Add metric summaries if available
                    for metric_name in ["reward", "td_error", "episode_reward"]:
                        metric_key = f"{metric_name}_stats"
                        if metric_key in learning_stats:
                            stats = learning_stats[metric_key]
                            if stats.get("count", 0) > 0:
                                metrics_display[f"{metric_name.title()} (avg)"] = f"{stats.get('mean', 0):.3f}"
                    
                    st.json(metrics_display)
                
                st.markdown("---")
                
                # RL Tool Scoring Table
                st.subheader("📋 RL Tool Scoring Table")
                
                display_rl_df = df_rl[[
                    "tool_name",
                    "action_value",
                    "confidence",
                    "total_calls",
                    "success_rate"
                ]].copy()
                
                display_rl_df.columns = [
                    "Tool Name",
                    "Action Value (Q)",
                    "RL Confidence (%)",
                    "Total Calls",
                    "Success Rate (%)"
                ]
                
                styled_rl_df = display_rl_df.style.format({
                    "Action Value (Q)": "{:.3f}",
                    "RL Confidence (%)": "{:.1f}%",
                    "Success Rate (%)": "{:.2f}%"
                })
                
                st.dataframe(
                    styled_rl_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Episode Rewards
                try:
                    recent_episodes = rl_service.get_successful_sequences(limit=10)
                    if recent_episodes:
                        st.markdown("---")
                        st.subheader("🏆 Recent Successful Episodes")
                        
                        df_episodes = pd.DataFrame(recent_episodes)
                        df_episodes["created_at"] = pd.to_datetime(df_episodes["created_at"])
                        df_episodes = df_episodes.sort_values("episode_reward", ascending=False)
                        
                        # Format tool sequence
                        df_episodes["tool_sequence_str"] = df_episodes["tool_sequence"].apply(
                            lambda x: " → ".join(x) if isinstance(x, list) else str(x)
                        )
                        
                        display_episodes_df = df_episodes[[
                            "session_id",
                            "tool_sequence_str",
                            "episode_reward",
                            "created_at"
                        ]].copy()
                        
                        display_episodes_df.columns = [
                            "Session ID",
                            "Tool Sequence",
                            "Episode Reward",
                            "Created At"
                        ]
                        
                        display_episodes_df["Created At"] = display_episodes_df["Created At"].apply(
                            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "N/A"
                        )
                        
                        st.dataframe(
                            display_episodes_df,
                            use_container_width=True,
                            hide_index=True
                        )
                except Exception as e:
                    pass  # Episodes might not be available yet
                    
            else:
                st.info("🤖 No RL policy data available yet. RL will start learning as tools are executed.")
        
        except Exception as e:
            st.warning(f"⚠️ Could not load RL metrics: {e}")
            st.info("RL service may still be initializing or no learning data is available yet.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Tool Execution Statistics Dashboard** | Data from SQLite Database")


if __name__ == "__main__":
    run_dashboard()


