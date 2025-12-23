"""RL Performance Dashboard - Streamlit dashboard for Reinforcement Learning metrics."""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, List, Any
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.services.feedback_service import (
    get_feedback_service,
    init_feedback_service
)
from fccs_agent.services.rl_service import (
    get_rl_service,
    init_rl_service
)
from fccs_agent.agent import get_tool_definitions, get_client, get_app_name, initialize_agent
from fccs_agent.utils.cache import load_members_from_cache

# Configuration
API_BASE_URL = "http://localhost:8080"  # Default, can be overridden


def fetch_rl_metrics() -> dict:
    """Fetch RL metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/rl/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}


def fetch_tool_metrics() -> list:
    """Fetch tool metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("metrics", [])
    except Exception:
        pass
    return []


def fetch_rl_episodes(tool_name: Optional[str] = None, limit: int = 20) -> list:
    """Fetch RL episodes from API."""
    try:
        params = {"limit": limit}
        if tool_name:
            params["tool_name"] = tool_name
        response = requests.get(f"{API_BASE_URL}/rl/episodes", params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("episodes", [])
    except Exception:
        pass
    return []


def fetch_rl_policy(tool_name: str) -> dict:
    """Fetch RL policy for a specific tool."""
    try:
        response = requests.get(f"{API_BASE_URL}/rl/policy/{tool_name}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}


def run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, try to use nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            except ImportError:
                # Fallback: create new event loop in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def get_tool_node_analysis(
    tool_name: str,
    tool_metrics: List[Dict],
    rl_service: Any,
    feedback_service: Any,
    tool_definitions: List[Dict]
) -> Dict[str, Any]:
    """Get comprehensive analysis for a tool node."""
    analysis = {
        "tool_name": tool_name,
        "performance": {},
        "rl_metrics": {},
        "usage_info": {},
        "relationships": {},
        "best_practices": []
    }
    
    # Find tool definition
    tool_def = next((t for t in tool_definitions if t.get("name") == tool_name), None)
    if tool_def:
        analysis["usage_info"]["description"] = tool_def.get("description", "")
        analysis["usage_info"]["parameters"] = tool_def.get("inputSchema", {}).get("properties", {})
        analysis["usage_info"]["required_params"] = tool_def.get("inputSchema", {}).get("required", [])
    
    # Performance metrics
    tool_metric = next((m for m in tool_metrics if m.get("tool_name") == tool_name), None)
    if tool_metric:
        analysis["performance"] = {
            "total_calls": tool_metric.get("total_calls", 0),
            "success_rate": tool_metric.get("success_rate", 0),
            "failure_count": int(tool_metric.get("total_calls", 0) * (1 - tool_metric.get("success_rate", 0))),
            "avg_execution_time_ms": tool_metric.get("avg_execution_time_ms", 0),
            "avg_user_rating": tool_metric.get("avg_user_rating")
        }
        
        # Get recent executions
        if feedback_service:
            try:
                recent_execs = feedback_service.get_recent_executions(tool_name, limit=10)
                if recent_execs:
                    exec_times = [e.get("execution_time_ms", 0) for e in recent_execs if e.get("execution_time_ms")]
                    if exec_times:
                        analysis["performance"]["min_execution_time"] = min(exec_times)
                        analysis["performance"]["max_execution_time"] = max(exec_times)
                    ratings = [e.get("user_rating") for e in recent_execs if e.get("user_rating")]
                    if ratings:
                        analysis["performance"]["rating_distribution"] = {
                            "1": ratings.count(1),
                            "2": ratings.count(2),
                            "3": ratings.count(3),
                            "4": ratings.count(4),
                            "5": ratings.count(5)
                        }
            except Exception:
                pass
    
    # RL metrics
    if rl_service:
        try:
            policy_dict = rl_service._get_policy_dict()
            tool_policies = {k: v for k, v in policy_dict.items() if k.startswith(f"{tool_name}:")}
            
            if tool_policies:
                q_values = list(tool_policies.values())
                analysis["rl_metrics"] = {
                    "avg_q_value": sum(q_values) / len(q_values) if q_values else 0,
                    "max_q_value": max(q_values) if q_values else 0,
                    "min_q_value": min(q_values) if q_values else 0,
                    "context_count": len(tool_policies)
                }
                
                # Get confidence
                context_hash = "default"
                confidence = rl_service.get_tool_confidence(tool_name, context_hash)
                analysis["rl_metrics"]["confidence"] = confidence * 100
        except Exception:
            pass
    
    # Relationships - find tools commonly used before/after
    if feedback_service:
        try:
            all_executions = feedback_service.get_recent_executions(limit=1000)
            sequences = []
            current_seq = []
            prev_tool = None
            
            for exec in all_executions:
                exec_tool = exec.get("tool_name")
                if exec_tool == tool_name:
                    if prev_tool:
                        sequences.append({"before": prev_tool, "after": None})
                    current_seq.append(exec_tool)
                elif current_seq:
                    sequences[-1]["after"] = exec_tool if sequences else None
                    current_seq = []
                prev_tool = exec_tool
            
            # Count relationships
            before_tools = {}
            after_tools = {}
            for seq in sequences:
                if seq.get("before"):
                    before_tools[seq["before"]] = before_tools.get(seq["before"], 0) + 1
                if seq.get("after"):
                    after_tools[seq["after"]] = after_tools.get(seq["after"], 0) + 1
            
            analysis["relationships"]["common_before"] = sorted(before_tools.items(), key=lambda x: x[1], reverse=True)[:5]
            analysis["relationships"]["common_after"] = sorted(after_tools.items(), key=lambda x: x[1], reverse=True)[:5]
        except Exception:
            pass
    
    # Best practices
    if tool_name.startswith("get_"):
        analysis["best_practices"].append("Use this tool to retrieve information from FCCS")
    elif tool_name.startswith("run_") or tool_name.startswith("execute_"):
        analysis["best_practices"].append("This tool performs an action - ensure prerequisites are met")
    elif "export" in tool_name.lower():
        analysis["best_practices"].append("Use for data export operations")
    elif "import" in tool_name.lower():
        analysis["best_practices"].append("Use for data import operations - verify data format first")
    
    if analysis["performance"].get("avg_execution_time_ms", 0) > 5000:
        analysis["best_practices"].append("This tool has longer execution times - consider running asynchronously")
    
    if analysis["performance"].get("success_rate", 1) < 0.8:
        analysis["best_practices"].append("⚠️ Lower success rate detected - review error logs for common issues")
    
    return analysis


def get_dimension_node_analysis(
    dimension_name: str,
    member_name: Optional[str],
    config: Any
) -> Dict[str, Any]:
    """Get comprehensive analysis for a dimension node."""
    analysis = {
        "dimension_name": dimension_name,
        "member_name": member_name,
        "hierarchy": {},
        "usage_stats": {},
        "metadata": {},
        "relationships": {}
    }
    
    try:
        # Try to get dimension hierarchy
        client = get_client()
        app_name = get_app_name() or "Consol"
        
        # Load from cache first
        cache_data = load_members_from_cache(app_name, dimension_name)
        if cache_data:
            items = cache_data.get("items", [])
            
            # Build hierarchy
            node_map = {}
            for item in items:
                name = item.get("name") or item.get("memberName")
                parent = item.get("parent") or item.get("parentName")
                if name:
                    node_map[name] = {
                        "name": name,
                        "parent": parent,
                        "children": [],
                        "description": item.get("description", ""),
                        "aliases": item.get("aliases", [])
                    }
            
            # Link children
            for name, node in node_map.items():
                if node["parent"] and node["parent"] in node_map:
                    node_map[node["parent"]]["children"].append(name)
            
            # Find specific member if requested
            if member_name and member_name in node_map:
                member_node = node_map[member_name]
                analysis["hierarchy"] = {
                    "parent": member_node["parent"],
                    "children": member_node["children"],
                    "sibling_count": len([n for n in node_map.values() if n["parent"] == member_node["parent"]]) - 1,
                    "descendant_count": len(member_node["children"])
                }
                analysis["metadata"] = {
                    "description": member_node["description"],
                    "aliases": member_node["aliases"]
                }
            
            # Dimension-level stats
            analysis["hierarchy"]["total_members"] = len(node_map)
            root_nodes = [n for n in node_map.values() if not n["parent"]]
            analysis["hierarchy"]["root_count"] = len(root_nodes)
            
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis


def get_entity_node_analysis(
    entity_name: str,
    config: Any
) -> Dict[str, Any]:
    """Get comprehensive analysis for an entity node."""
    analysis = {
        "entity_name": entity_name,
        "hierarchy": {},
        "performance_data": {},
        "usage_patterns": {}
    }
    
    try:
        # Load entity hierarchy from cache
        app_name = get_app_name() or "Consol"
        cache_data = load_members_from_cache(app_name, "Entity")
        
        if cache_data:
            items = cache_data.get("items", [])
            entity_map = {}
            
            for item in items:
                name = item.get("name") or item.get("memberName")
                parent = item.get("parent") or item.get("parentName")
                if name:
                    entity_map[name] = {
                        "name": name,
                        "parent": parent,
                        "children": []
                    }
            
            # Link children
            for name, entity in entity_map.items():
                if entity["parent"] and entity["parent"] in entity_map:
                    entity_map[entity["parent"]]["children"].append(name)
            
            # Find entity
            if entity_name in entity_map:
                entity_node = entity_map[entity_name]
                analysis["hierarchy"] = {
                    "parent": entity_node["parent"],
                    "children": entity_node["children"],
                    "sibling_count": len([e for e in entity_map.values() if e["parent"] == entity_node["parent"]]) - 1,
                    "level": "Unknown"  # Would need to calculate
                }
    
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis


def get_sequence_node_analysis(
    sequence: List[str],
    rl_service: Any,
    feedback_service: Any
) -> Dict[str, Any]:
    """Get comprehensive analysis for a tool sequence node."""
    analysis = {
        "sequence": sequence,
        "metrics": {},
        "pattern_analysis": {},
        "learning_insights": {}
    }
    
    if not sequence:
        return analysis
    
    sequence_key = " → ".join(sequence)
    analysis["pattern_analysis"]["sequence_key"] = sequence_key
    analysis["pattern_analysis"]["length"] = len(sequence)
    
    # Get sequence metrics from RL service
    if rl_service:
        try:
            episodes = rl_service.get_successful_sequences(limit=1000)
            matching_episodes = [
                ep for ep in episodes
                if ep.get("tool_sequence") == sequence or 
                   (isinstance(ep.get("tool_sequence"), list) and ep.get("tool_sequence") == sequence)
            ]
            
            if matching_episodes:
                rewards = [ep.get("episode_reward", 0) for ep in matching_episodes]
                analysis["metrics"] = {
                    "frequency": len(matching_episodes),
                    "avg_reward": sum(rewards) / len(rewards) if rewards else 0,
                    "max_reward": max(rewards) if rewards else 0,
                    "min_reward": min(rewards) if rewards else 0,
                    "success_rate": len([ep for ep in matching_episodes if ep.get("outcome") == "success"]) / len(matching_episodes) if matching_episodes else 0
                }
        except Exception:
            pass
    
    # Pattern analysis
    if len(sequence) >= 2:
        analysis["pattern_analysis"]["first_tool"] = sequence[0]
        analysis["pattern_analysis"]["last_tool"] = sequence[-1]
        analysis["pattern_analysis"]["common_pattern"] = "Multi-step workflow"
    
    return analysis


def render_help_me_page(
    tool_metrics: List[Dict],
    rl_service: Any,
    feedback_service: Any,
    use_api: bool,
    config: Any
):
    """Render the Help Me page with comprehensive node analysis."""
    st.subheader("💡 Help Me - Node Analysis")
    st.markdown("Get detailed analysis for every node in the system: tools, dimensions, entities, and sequences.")
    
    # Get tool definitions
    try:
        tool_definitions = get_tool_definitions()
    except Exception:
        tool_definitions = []
    
    # Create tabs for different node types
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Tool Nodes", "📊 Dimension Nodes", "🏢 Entity Nodes", "🔗 Sequence Nodes"])
    
    with tab1:
        st.markdown("### Tool Node Analysis")
        st.markdown("Select a tool to see comprehensive analysis including performance metrics, RL learning data, usage information, relationships, and best practices.")
        
        # Tool selection and search
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            tool_search = st.text_input("🔍 Search tools", placeholder="Type to filter tools...", help="Search tools by name")
        with col2:
            show_all = st.checkbox("Show all tools", value=False, help="Show all available tools, even without execution data")
        with col3:
            compare_mode = st.checkbox("Compare Mode", value=False, help="Compare multiple tools side-by-side")
        
        # Filter tools
        available_tools = [m.get("tool_name") for m in tool_metrics] if tool_metrics else []
        if not available_tools and tool_definitions:
            available_tools = [t.get("name") for t in tool_definitions]
        
        if tool_search:
            available_tools = [t for t in available_tools if tool_search.lower() in t.lower()]
        
        if available_tools:
            selected_tool = None
            
            if compare_mode:
                # Comparison mode
                selected_tools = st.multiselect(
                    "Select Tools to Compare (up to 3)",
                    available_tools,
                    max_selections=3,
                    help="Select up to 3 tools to compare side-by-side"
                )
                
                if selected_tools:
                    st.markdown("#### 📊 Tool Comparison")
                    comparison_data = []
                    for tool_name in selected_tools:
                        with st.spinner(f"Analyzing {tool_name}..."):
                            analysis = get_tool_node_analysis(
                                tool_name,
                                tool_metrics,
                                rl_service,
                                feedback_service,
                                tool_definitions
                            )
                            comparison_data.append(analysis)
                    
                    # Comparison table
                    comp_df_data = []
                    for analysis in comparison_data:
                        perf = analysis.get("performance", {})
                        rl_met = analysis.get("rl_metrics", {})
                        comp_df_data.append({
                            "Tool": analysis["tool_name"],
                            "Total Calls": perf.get("total_calls", 0),
                            "Success Rate": f"{perf.get('success_rate', 0):.1%}",
                            "Avg Time (ms)": f"{perf.get('avg_execution_time_ms', 0):.1f}",
                            "Avg Rating": f"{perf.get('avg_user_rating', 0):.2f}" if perf.get("avg_user_rating") else "N/A",
                            "Avg Q-Value": f"{rl_met.get('avg_q_value', 0):.3f}",
                            "RL Confidence": f"{rl_met.get('confidence', 0):.1f}%"
                        })
                    
                    comp_df = pd.DataFrame(comp_df_data)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                    
                    # Comparison charts
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_comp_success = px.bar(
                            comp_df,
                            x="Tool",
                            y="Success Rate",
                            title="Success Rate Comparison",
                            color="Success Rate",
                            color_continuous_scale="Greens"
                        )
                        st.plotly_chart(fig_comp_success, use_container_width=True)
                    
                    with col2:
                        # Convert avg time to numeric for chart
                        comp_df_time = comp_df.copy()
                        comp_df_time["Avg Time (ms)"] = comp_df_time["Avg Time (ms)"].str.replace(" ms", "").astype(float)
                        fig_comp_time = px.bar(
                            comp_df_time,
                            x="Tool",
                            y="Avg Time (ms)",
                            title="Execution Time Comparison",
                            color="Avg Time (ms)",
                            color_continuous_scale="Blues"
                        )
                        st.plotly_chart(fig_comp_time, use_container_width=True)
                    
                    # Export option
                    csv = comp_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Comparison as CSV",
                        data=csv,
                        file_name=f"tool_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                # Single tool analysis mode
                selected_tool = st.selectbox("Select Tool", available_tools, index=0, help="Choose a tool to analyze")
            
            if not compare_mode and selected_tool:
                with st.spinner(f"Analyzing {selected_tool}..."):
                    analysis = get_tool_node_analysis(
                        selected_tool,
                        tool_metrics,
                        rl_service,
                        feedback_service,
                        tool_definitions
                    )
                
                # Display analysis
                st.markdown(f"#### 📋 Analysis for: `{selected_tool}`")
                
                # Performance Metrics
                with st.expander("📊 Performance Metrics", expanded=True):
                    perf = analysis.get("performance", {})
                    if perf:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Calls", perf.get("total_calls", 0))
                        with col2:
                            st.metric("Success Rate", f"{perf.get('success_rate', 0):.1%}")
                        with col3:
                            st.metric("Avg Time", f"{perf.get('avg_execution_time_ms', 0):.1f} ms")
                        with col4:
                            rating = perf.get("avg_user_rating")
                            st.metric("Avg Rating", f"{rating:.2f}" if rating else "N/A")
                        
                        if perf.get("min_execution_time") and perf.get("max_execution_time"):
                            st.markdown(f"**Execution Time Range:** {perf['min_execution_time']:.1f} - {perf['max_execution_time']:.1f} ms")
                        
                        if perf.get("rating_distribution"):
                            st.markdown("**Rating Distribution:**")
                            rating_df = pd.DataFrame(list(perf["rating_distribution"].items()), columns=["Rating", "Count"])
                            fig_ratings = px.bar(rating_df, x="Rating", y="Count", title="User Rating Distribution")
                            st.plotly_chart(fig_ratings, use_container_width=True)
                    else:
                        st.info("No performance data available yet. Execute the tool to see metrics.")
                
                # RL Learning Metrics
                with st.expander("🤖 RL Learning Metrics"):
                    rl_met = analysis.get("rl_metrics", {})
                    if rl_met:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Q-Value", f"{rl_met.get('avg_q_value', 0):.3f}")
                        with col2:
                            st.metric("Max Q-Value", f"{rl_met.get('max_q_value', 0):.3f}")
                        with col3:
                            st.metric("RL Confidence", f"{rl_met.get('confidence', 0):.1f}%")
                        st.markdown(f"**Contexts Learned:** {rl_met.get('context_count', 0)}")
                    else:
                        st.info("No RL learning data available yet.")
                
                # Usage Information
                with st.expander("📖 Usage Information"):
                    usage = analysis.get("usage_info", {})
                    if usage.get("description"):
                        st.markdown(f"**Description:** {usage['description']}")
                    
                    if usage.get("parameters"):
                        st.markdown("**Parameters:**")
                        params = usage["parameters"]
                        required = usage.get("required_params", [])
                        for param_name, param_info in params.items():
                            req_marker = "🔴 Required" if param_name in required else "⚪ Optional"
                            st.markdown(f"- **{param_name}** ({req_marker})")
                            if isinstance(param_info, dict):
                                if param_info.get("description"):
                                    st.markdown(f"  - {param_info['description']}")
                                if param_info.get("type"):
                                    st.markdown(f"  - Type: {param_info['type']}")
                    else:
                        st.info("No parameters defined.")
                
                # Relationships
                with st.expander("🔗 Relationships"):
                    rels = analysis.get("relationships", {})
                    if rels.get("common_before"):
                        st.markdown("**Commonly Used Before:**")
                        for tool, count in rels["common_before"]:
                            st.markdown(f"- `{tool}` ({count} times)")
                    if rels.get("common_after"):
                        st.markdown("**Commonly Used After:**")
                        for tool, count in rels["common_after"]:
                            st.markdown(f"- `{tool}` ({count} times)")
                    if not rels.get("common_before") and not rels.get("common_after"):
                        st.info("No relationship data available yet.")
                
                # Best Practices
                with st.expander("✅ Best Practices"):
                    practices = analysis.get("best_practices", [])
                    if practices:
                        for practice in practices:
                            st.markdown(f"- {practice}")
                    else:
                        st.info("No specific best practices available.")
                
                # Export option
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    # Export as JSON
                    analysis_json = json.dumps(analysis, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Analysis as JSON",
                        data=analysis_json,
                        file_name=f"tool_analysis_{selected_tool}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                with col2:
                    # Export summary as CSV
                    summary_data = {
                        "Tool": [selected_tool],
                        "Total Calls": [analysis.get("performance", {}).get("total_calls", 0)],
                        "Success Rate": [f"{analysis.get('performance', {}).get('success_rate', 0):.1%}"],
                        "Avg Time (ms)": [analysis.get("performance", {}).get("avg_execution_time_ms", 0)],
                        "Avg Rating": [analysis.get("performance", {}).get("avg_user_rating", "N/A")],
                        "Avg Q-Value": [analysis.get("rl_metrics", {}).get("avg_q_value", 0)],
                        "RL Confidence": [f"{analysis.get('rl_metrics', {}).get('confidence', 0):.1f}%"]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    csv = summary_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Summary as CSV",
                        data=csv,
                        file_name=f"tool_summary_{selected_tool}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No tools available. Please ensure tools are loaded.")
    
    with tab2:
        st.markdown("### Dimension Node Analysis")
        st.markdown("Analyze dimension hierarchies and members with usage statistics and relationships.")
        st.info("💡 **Tip:** Use the member search to analyze specific dimension members and their hierarchy relationships.")
        
        # Dimension selection
        try:
            client = get_client()
            app_name = get_app_name() or "Consol"
            
            # Try to get dimensions
            dimensions_list = ["Account", "Entity", "Period", "Year", "Scenario", "Currency", "Movement", "Intercompany", "Flow", "Consolidation", "Data Source", "Custom1", "Custom2", "Custom3", "Custom4"]
            
            selected_dimension = st.selectbox("Select Dimension", dimensions_list, index=0, help="Choose a dimension to analyze")
            member_search = st.text_input("🔍 Search member (optional)", placeholder="Type member name...", help="Enter a specific member name to see detailed hierarchy information")
            
            if selected_dimension:
                with st.spinner(f"Analyzing {selected_dimension} dimension..."):
                    analysis = get_dimension_node_analysis(
                        selected_dimension,
                        member_search if member_search else None,
                        config
                    )
                
                st.markdown(f"#### 📊 Analysis for: `{selected_dimension}`")
                if member_search:
                    st.markdown(f"**Member:** `{member_search}`")
                
                # Hierarchy Information
                with st.expander("🌳 Hierarchy Information", expanded=True):
                    hier = analysis.get("hierarchy", {})
                    if hier:
                        if hier.get("total_members"):
                            st.metric("Total Members", hier["total_members"])
                        if hier.get("root_count"):
                            st.metric("Root Nodes", hier["root_count"])
                        if member_search and hier.get("parent"):
                            st.markdown(f"**Parent:** `{hier['parent']}`")
                        if member_search and hier.get("children"):
                            st.markdown(f"**Children:** {len(hier['children'])}")
                            if hier["children"]:
                                for child in hier["children"][:10]:
                                    st.markdown(f"- `{child}`")
                                if len(hier["children"]) > 10:
                                    st.markdown(f"... and {len(hier['children']) - 10} more")
                        if member_search and hier.get("sibling_count") is not None:
                            st.markdown(f"**Siblings:** {hier['sibling_count']}")
                    else:
                        st.info("No hierarchy data available. Try loading dimension members first.")
                
                # Metadata
                if analysis.get("metadata"):
                    with st.expander("📝 Metadata"):
                        meta = analysis["metadata"]
                        if meta.get("description"):
                            st.markdown(f"**Description:** {meta['description']}")
                        if meta.get("aliases"):
                            st.markdown(f"**Aliases:** {', '.join(meta['aliases'])}")
                
                # Export option
                if analysis.get("hierarchy"):
                    st.markdown("---")
                    analysis_json = json.dumps(analysis, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Analysis as JSON",
                        data=analysis_json,
                        file_name=f"dimension_analysis_{selected_dimension}_{member_search or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        except Exception as e:
            st.error(f"Error loading dimensions: {e}")
            st.info("Ensure FCCS client is initialized and connected.")
    
    with tab3:
        st.markdown("### Entity Node Analysis")
        st.markdown("Analyze entity hierarchy and organizational structure.")
        st.info("💡 **Tip:** Enter an entity name to see its position in the organizational hierarchy, parent entities, and child entities.")
        
        entity_search = st.text_input("🔍 Search entity", placeholder="Type entity name...", help="Enter the name of an entity to analyze its hierarchy")
        
        if entity_search:
            with st.spinner(f"Analyzing {entity_search}..."):
                analysis = get_entity_node_analysis(entity_search, config)
            
            st.markdown(f"#### 🏢 Analysis for: `{entity_search}`")
            
            # Hierarchy Information
            with st.expander("🌳 Hierarchy Information", expanded=True):
                hier = analysis.get("hierarchy", {})
                if hier:
                    if hier.get("parent"):
                        st.markdown(f"**Parent Entity:** `{hier['parent']}`")
                    if hier.get("children"):
                        st.markdown(f"**Child Entities:** {len(hier['children'])}")
                        for child in hier["children"][:10]:
                            st.markdown(f"- `{child}`")
                        if len(hier["children"]) > 10:
                            st.markdown(f"... and {len(hier['children']) - 10} more")
                    if hier.get("sibling_count") is not None:
                        st.markdown(f"**Sibling Entities:** {hier['sibling_count']}")
                    
                    # Export option
                    if hier:
                        st.markdown("---")
                        analysis_json = json.dumps(analysis, indent=2, default=str)
                        st.download_button(
                            label="📥 Download Analysis as JSON",
                            data=analysis_json,
                            file_name=f"entity_analysis_{entity_search}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                else:
                    st.info("No hierarchy data available. Ensure entity cache is loaded.")
        else:
            st.info("Enter an entity name to see analysis.")
    
    with tab4:
        st.markdown("### Sequence Node Analysis")
        st.markdown("Analyze tool execution sequences and patterns learned by RL.")
        st.info("💡 **Tip:** Sequences show successful tool execution patterns. RL learns which tool combinations work best together.")
        
        # Get sequences from RL service
        sequences = []
        if rl_service:
            try:
                episodes = rl_service.get_successful_sequences(limit=100)
                sequences = [ep.get("tool_sequence", []) for ep in episodes if ep.get("tool_sequence")]
                # Remove duplicates
                seen = set()
                unique_sequences = []
                for seq in sequences:
                    seq_key = tuple(seq) if isinstance(seq, list) else tuple([seq])
                    if seq_key not in seen:
                        seen.add(seq_key)
                        unique_sequences.append(seq)
                sequences = unique_sequences[:20]  # Limit to 20
            except Exception:
                pass
        
        if sequences:
            st.markdown(f"Found {len(sequences)} unique sequences")
            selected_seq_idx = st.selectbox(
                "Select Sequence",
                range(len(sequences)),
                format_func=lambda i: " → ".join(sequences[i]) if isinstance(sequences[i], list) else str(sequences[i])
            )
            
            if selected_seq_idx is not None:
                selected_sequence = sequences[selected_seq_idx]
                with st.spinner("Analyzing sequence..."):
                    analysis = get_sequence_node_analysis(selected_sequence, rl_service, feedback_service)
                
                st.markdown(f"#### 🔗 Analysis for Sequence")
                st.code(" → ".join(selected_sequence) if isinstance(selected_sequence, list) else str(selected_sequence))
                
                # Sequence Metrics
                with st.expander("📊 Sequence Metrics", expanded=True):
                    metrics = analysis.get("metrics", {})
                    if metrics:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Frequency", metrics.get("frequency", 0))
                        with col2:
                            st.metric("Avg Reward", f"{metrics.get('avg_reward', 0):.2f}")
                        with col3:
                            st.metric("Success Rate", f"{metrics.get('success_rate', 0):.1%}")
                    else:
                        st.info("No metrics available for this sequence.")
                
                # Pattern Analysis
                with st.expander("🔍 Pattern Analysis"):
                    pattern = analysis.get("pattern_analysis", {})
                    if pattern:
                        st.markdown(f"**Sequence Length:** {pattern.get('length', 0)} tools")
                        if pattern.get("first_tool"):
                            st.markdown(f"**First Tool:** `{pattern['first_tool']}`")
                        if pattern.get("last_tool"):
                            st.markdown(f"**Last Tool:** `{pattern['last_tool']}`")
                        if pattern.get("common_pattern"):
                            st.markdown(f"**Pattern Type:** {pattern['common_pattern']}")
                    else:
                        st.info("No pattern analysis available.")
                
                # Learning Insights
                with st.expander("🧠 Learning Insights"):
                    insights = analysis.get("learning_insights", {})
                    if insights:
                        st.json(insights)
                    else:
                        st.info("No learning insights available yet.")
                
                # Export option
                if analysis.get("metrics"):
                    st.markdown("---")
                    analysis_json = json.dumps(analysis, indent=2, default=str)
                    seq_name = "_".join(selected_sequence[:3]) if isinstance(selected_sequence, list) else str(selected_sequence)
                    st.download_button(
                        label="📥 Download Analysis as JSON",
                        data=analysis_json,
                        file_name=f"sequence_analysis_{seq_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        else:
            st.info("No sequences available. Execute some tools to see sequence patterns.")




def run_rl_dashboard():
    """Run the RL Performance Dashboard."""
    st.set_page_config(
        page_title="RL Performance Dashboard",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 RL Performance Dashboard")
    st.markdown("Reinforcement Learning Metrics & Analytics for FCCS Agent")
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        global API_BASE_URL
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        API_BASE_URL = api_url
        
        refresh_interval = st.slider("Auto-refresh (seconds)", 0, 60, 0)
        if refresh_interval > 0:
            st.info(f"Auto-refreshing every {refresh_interval} seconds")
        
        st.markdown("---")
        st.header("ℹ️ Info")
        st.info("""
        This dashboard shows:
        - RL learning metrics
        - Tool performance statistics
        - Policy values and Q-learning progress
        - Successful tool sequences
        - Exploration vs exploitation rates
        """)
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Initialize services if not already initialized
    try:
        config = load_config()
        
        # Initialize feedback service
        feedback_service = get_feedback_service()
        if feedback_service is None:
            try:
                feedback_service = init_feedback_service(config.database_url)
                st.success("✅ Feedback service initialized")
            except Exception as e:
                st.warning(f"⚠️ Could not initialize feedback service: {e}")
                feedback_service = None
        
        # Initialize RL service if enabled
        rl_service = get_rl_service()
        if rl_service is None and config.rl_enabled and feedback_service:
            try:
                rl_service = init_rl_service(
                    feedback_service,
                    config.database_url,
                    exploration_rate=config.rl_exploration_rate,
                    learning_rate=config.rl_learning_rate,
                    discount_factor=config.rl_discount_factor,
                    min_samples=config.rl_min_samples
                )
                st.success("✅ RL service initialized")
            except Exception as e:
                st.warning(f"⚠️ Could not initialize RL service: {e}")
                rl_service = None
    except Exception as e:
        st.error(f"❌ Configuration error: {e}")
        feedback_service = None
        rl_service = None
    
    # If services available, use direct access; otherwise use API
    use_api = rl_service is None or feedback_service is None
    
    if use_api:
        st.info("📡 Using API mode - fetching data from web server")
        rl_metrics = fetch_rl_metrics()
        tool_metrics = fetch_tool_metrics()
    else:
        st.success("✅ Direct service access - using local services")
        # Get metrics directly from services
        tool_metrics_data = feedback_service.get_tool_metrics() if feedback_service else []
        tool_metrics = [
            {
                "tool_name": m.get("tool_name", ""),
                "total_calls": m.get("total_calls", 0),
                "success_rate": m.get("success_rate", 0),
                "avg_execution_time_ms": m.get("avg_execution_time_ms", 0),
                "avg_user_rating": m.get("avg_user_rating")
            }
            for m in tool_metrics_data
        ]
        
        if rl_service:
            learning_stats = rl_service.get_learning_stats()
            rl_metrics = {
                "rl_enabled": True,
                "tool_metrics": {
                    "total_tools": len(tool_metrics),
                    "avg_success_rate": sum(m.get("success_rate", 0) for m in tool_metrics) / len(tool_metrics) if tool_metrics else 0,
                    "avg_user_rating": sum(m.get("avg_user_rating", 0) or 0 for m in tool_metrics) / len(tool_metrics) if tool_metrics else 0
                },
                "policy_metrics": {
                    "total_policies": learning_stats.get("replay_buffer_size", 0),
                    "avg_action_value": 0  # Would need to calculate from policy cache
                },
                "learning_stats": learning_stats
            }
        else:
            rl_metrics = {}
    
    if not rl_metrics.get("rl_enabled"):
        st.error("❌ RL service not available")
        st.info("""
        Please ensure:
        1. RL is enabled in configuration (RL_ENABLED=true)
        2. Database is configured (DATABASE_URL)
        3. Web server is running (if using API mode)
        """)
        st.stop()
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tools = rl_metrics.get("tool_metrics", {}).get("total_tools", 0)
        st.metric("Total Tools", total_tools)
    
    with col2:
        avg_success = rl_metrics.get("tool_metrics", {}).get("avg_success_rate", 0)
        st.metric("Avg Success Rate", f"{avg_success:.1%}")
    
    with col3:
        avg_rating = rl_metrics.get("tool_metrics", {}).get("avg_user_rating", 0)
        st.metric("Avg User Rating", f"{avg_rating:.2f}" if avg_rating else "N/A")
    
    with col4:
        total_policies = rl_metrics.get("policy_metrics", {}).get("total_policies", 0)
        st.metric("Total Policies", total_policies)
    
    with col5:
        if rl_service:
            exploration_stats = rl_service.tool_selector.get_exploration_stats()
            exploration_rate = exploration_stats.get("current_exploration_rate", 0)
            st.metric("Exploration Rate", f"{exploration_rate:.1%}")
        else:
            st.metric("Exploration Rate", "N/A")
    
    st.markdown("---")
    
    # Tool Performance Analysis
    st.subheader("📊 Tool Performance Analysis")
    
    # Get all available tools if no metrics exist
    if not tool_metrics:
        st.warning("⚠️ No tool execution metrics found yet. Showing available tools.")
        try:
            all_tools = get_tool_definitions()
            tool_metrics = [
                {
                    "tool_name": tool.get("name", ""),
                    "total_calls": 0,
                    "success_rate": 0,
                    "avg_execution_time_ms": 0,
                    "avg_user_rating": None
                }
                for tool in all_tools
            ]
            st.info(f"Found {len(tool_metrics)} available tools. Execute some tools to see performance metrics.")
        except Exception as e:
            st.error(f"Could not load tool definitions: {e}")
            tool_metrics = []
    
    if tool_metrics:
        df_tools = pd.DataFrame(tool_metrics)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success Rate Chart
            df_sorted = df_tools[df_tools["success_rate"] > 0].sort_values("success_rate", ascending=False).head(15)
            if not df_sorted.empty:
                fig_success = px.bar(
                    df_sorted,
                    x="success_rate",
                    y="tool_name",
                    orientation="h",
                    title="Top 15 Tools by Success Rate",
                    labels={"success_rate": "Success Rate", "tool_name": "Tool"},
                    color="success_rate",
                    color_continuous_scale="Greens"
                )
                fig_success.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_success, use_container_width=True)
            else:
                st.info("No tools with execution data yet. Execute some tools to see success rate charts.")
        
        with col2:
            # Execution Time Chart
            df_time = df_tools[df_tools["avg_execution_time_ms"] > 0].sort_values("avg_execution_time_ms", ascending=False).head(15)
            if not df_time.empty:
                fig_time = px.bar(
                    df_time,
                    x="avg_execution_time_ms",
                    y="tool_name",
                    orientation="h",
                    title="Top 15 Tools by Execution Time",
                    labels={"avg_execution_time_ms": "Time (ms)", "tool_name": "Tool"},
                    color="avg_execution_time_ms",
                    color_continuous_scale="Reds"
                )
                fig_time.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("No execution time data available")
        
        # Tool Metrics Table
        st.subheader("📋 Detailed Tool Metrics")
        df_display = df_tools[["tool_name", "total_calls", "success_rate", "avg_execution_time_ms", "avg_user_rating"]].copy()
        df_display["success_rate"] = df_display["success_rate"].apply(lambda x: f"{x:.1%}" if x > 0 else "N/A")
        df_display["avg_execution_time_ms"] = df_display["avg_execution_time_ms"].apply(lambda x: f"{x:.1f} ms" if x > 0 else "N/A")
        df_display["avg_user_rating"] = df_display["avg_user_rating"].apply(lambda x: f"{x:.2f}" if x else "N/A")
        df_display.columns = ["Tool", "Total Calls", "Success Rate", "Avg Time", "Avg Rating"]
        
        # Filter out tools with no calls if there are tools with calls
        has_executions = df_display["Total Calls"].astype(str).str.replace("N/A", "0").astype(int).sum() > 0
        if has_executions:
            # Show only tools with executions
            df_display = df_display[df_display["Total Calls"] != "0"]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Show count
        total_tools_shown = len(df_display)
        total_tools_available = len(tool_metrics)
        if total_tools_shown < total_tools_available:
            st.caption(f"Showing {total_tools_shown} tools with execution data (out of {total_tools_available} available tools)")
        
        # Show all available tools if no executions
        if not has_executions:
            st.markdown("#### 📦 All Available Tools")
            try:
                all_tools = get_tool_definitions()
                tools_list = pd.DataFrame([
                    {
                        "Tool Name": tool.get("name", ""),
                        "Description": tool.get("description", "").split("/")[0].strip()  # Get first part before /
                    }
                    for tool in all_tools
                ])
                st.dataframe(tools_list, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Could not load tool definitions: {e}")
    else:
        st.info("No tool metrics available")
    
    st.markdown("---")
    
    # RL Learning Statistics
    st.subheader("🧠 RL Learning Statistics")
    
    if rl_service:
        learning_stats = rl_service.get_learning_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Exploration Statistics")
            exploration_stats = learning_stats.get("exploration_stats", {})
            exp_df = pd.DataFrame([{
                "Metric": "Current Exploration Rate",
                "Value": exploration_stats.get("current_exploration_rate", 0)
            }, {
                "Metric": "Initial Exploration Rate",
                "Value": exploration_stats.get("initial_exploration_rate", 0)
            }, {
                "Metric": "Total Selections",
                "Value": exploration_stats.get("total_selections", 0)
            }])
            st.dataframe(exp_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Learning Progress")
            progress_df = pd.DataFrame([{
                "Metric": "Update Count",
                "Value": learning_stats.get("update_count", 0)
            }, {
                "Metric": "Replay Buffer Size",
                "Value": learning_stats.get("replay_buffer_size", 0)
            }])
            st.dataframe(progress_df, use_container_width=True, hide_index=True)
        
        # Metric summaries
        st.markdown("#### Learning Metrics Summary")
        metric_names = ["reward", "td_error", "episode_reward", "exploration_rate"]
        metric_data = []
        
        for metric_name in metric_names:
            summary = learning_stats.get(f"{metric_name}_stats", {})
            if summary.get("count", 0) > 0:
                metric_data.append({
                    "Metric": metric_name.replace("_", " ").title(),
                    "Count": summary.get("count", 0),
                    "Mean": summary.get("mean", 0),
                    "Std": summary.get("std", 0),
                    "Min": summary.get("min", 0),
                    "Max": summary.get("max", 0),
                    "Latest": summary.get("latest", 0)
                })
        
        if metric_data:
            metrics_df = pd.DataFrame(metric_data)
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Plot metric trends
            if rl_service.metrics_tracker:
                st.markdown("#### Metric Trends")
                metric_select = st.selectbox("Select Metric", metric_names)
                
                recent_metrics = rl_service.metrics_tracker.get_recent_metrics(metric_select, limit=100)
                if recent_metrics:
                    df_metrics = pd.DataFrame(recent_metrics)
                    df_metrics["timestamp"] = pd.to_datetime(df_metrics["timestamp"])
                    df_metrics = df_metrics.sort_values("timestamp")
                    
                    fig_trend = px.line(
                        df_metrics,
                        x="timestamp",
                        y="value",
                        title=f"{metric_select.replace('_', ' ').title()} Over Time",
                        markers=True
                    )
                    fig_trend.update_layout(height=400)
                    st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No learning metrics available yet")
    else:
        st.info("RL service not available - cannot show learning statistics")
    
    st.markdown("---")
    
    # Successful Sequences
    st.subheader("🎯 Successful Tool Sequences")
    
    tool_select = st.selectbox(
        "Filter by Tool (optional)",
        options=["All"] + [m["tool_name"] for m in tool_metrics] if tool_metrics else ["All"],
        index=0
    )
    
    if use_api:
        episodes = fetch_rl_episodes(
            tool_name=tool_select if tool_select != "All" else None,
            limit=20
        )
    else:
        if rl_service:
            episodes = rl_service.get_successful_sequences(
                tool_name=tool_select if tool_select != "All" else None,
                limit=20
            )
        else:
            episodes = []
    
    if episodes:
        for i, episode in enumerate(episodes[:10], 1):
            with st.expander(f"Sequence {i}: {episode.get('session_id', 'Unknown')} - Reward: {episode.get('episode_reward', 0):.2f}"):
                sequence = episode.get("tool_sequence", [])
                if sequence:
                    st.markdown("**Tool Sequence:**")
                    sequence_str = " → ".join(sequence)
                    st.code(sequence_str, language=None)
                st.markdown(f"**Reward:** {episode.get('episode_reward', 0):.2f}")
                st.markdown(f"**Outcome:** {episode.get('outcome', 'unknown')}")
                if episode.get("created_at"):
                    st.markdown(f"**Date:** {episode['created_at']}")
    else:
        st.info("No successful sequences recorded yet")
    
    st.markdown("---")
    
    # RL Policy Explorer
    st.subheader("🔍 RL Policy Explorer")
    
    policy_tool = st.selectbox(
        "Select Tool to View Policy",
        options=[m["tool_name"] for m in tool_metrics] if tool_metrics else [],
        index=0 if tool_metrics else None
    )
    
    if policy_tool:
        if use_api:
            policy_data = fetch_rl_policy(policy_tool)
        else:
            # Get policy directly from service
            if rl_service:
                policy_dict = rl_service._get_policy_dict()
                policies = [
                    {
                        "context_hash": key.split(":")[1] if ":" in key else "",
                        "action_value": value,
                        "visit_count": 0,  # Would need to query database for this
                        "last_updated": None
                    }
                    for key, value in policy_dict.items()
                    if key.startswith(f"{policy_tool}:")
                ]
                policy_data = {
                    "tool_name": policy_tool,
                    "policies": policies,
                    "total_contexts": len(policies)
                }
            else:
                policy_data = {}
        
        if policy_data.get("policies"):
            st.metric("Total Contexts", policy_data.get("total_contexts", 0))
            
            policies_df = pd.DataFrame(policy_data["policies"])
            policies_df = policies_df.sort_values("action_value", ascending=False)
            
            # Policy value distribution
            fig_policy = px.histogram(
                policies_df,
                x="action_value",
                title=f"Policy Value Distribution for {policy_tool}",
                labels={"action_value": "Q-Value (Action Value)", "count": "Frequency"},
                nbins=20
            )
            fig_policy.update_layout(height=400)
            st.plotly_chart(fig_policy, use_container_width=True)
            
            # Top policies
            st.markdown("#### Top Policies by Q-Value")
            top_policies = policies_df.head(10)[["context_hash", "action_value", "visit_count"]].copy()
            top_policies.columns = ["Context Hash", "Q-Value", "Visit Count"]
            top_policies["Context Hash"] = top_policies["Context Hash"].apply(lambda x: x[:16] + "..." if len(x) > 16 else x)
            st.dataframe(top_policies, use_container_width=True, hide_index=True)
        else:
            st.info(f"No policies found for {policy_tool}")
    
    st.markdown("---")
    
    # Help Me Page
    render_help_me_page(
        tool_metrics=tool_metrics,
        rl_service=rl_service,
        feedback_service=feedback_service,
        use_api=use_api,
        config=config if 'config' in locals() else None
    )
    
    # Footer
    st.markdown("---")
    st.markdown("**RL Performance Dashboard** | Reinforcement Learning Analytics for FCCS Agent")


if __name__ == "__main__":
    run_rl_dashboard()

