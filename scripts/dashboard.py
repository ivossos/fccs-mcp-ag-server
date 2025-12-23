"""FCCS Performance Dashboard - Streamlit web dashboard."""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from functools import lru_cache

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache

# Try to import nest_asyncio for nested event loops
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# Global event loop for async operations
_loop = None


async def get_entity_performance(entity_name: str, year: str) -> float | None:
    """Get Net Income for an entity."""
    try:
        result = await smart_retrieve(
            account="FCCS_Net Income",
            entity=entity_name,
            period="Dec",
            years=year,
            scenario="Actual"
        )
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else None
    except Exception:
        pass
    return None


async def get_monthly_data(entity_name: str, year: str) -> dict:
    """Get monthly Net Income data."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = {}
    
    for month in months:
        try:
            result = await smart_retrieve(
                account="FCCS_Net Income",
                entity=entity_name,
                period=month,
                years=year,
                scenario="Actual"
            )
            if result.get("status") == "success":
                data = result.get("data", {})
                rows = data.get("rows", [])
                if rows and rows[0].get("data"):
                    value = rows[0]["data"][0]
                    if value is not None:
                        monthly_data[month] = float(value)
        except Exception:
            pass
    
    return monthly_data


async def get_top_performers(year: str, top_n: int = 10):
    """Get top N performers."""
    cached_entities = load_members_from_cache("Consol", "Entity")
    if not cached_entities:
        return []
    
    entities = [item.get("name") for item in cached_entities.get("items", []) if item.get("name")]
    exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total"]
    entities = [e for e in entities if not any(kw in e for kw in exclude_keywords)]
    
    performance = []
    for entity in entities[:100]:  # Limit for performance
        value = await get_entity_performance(entity, year)
        if value is not None:
            performance.append({"entity": entity, "net_income": value})
    
    performance.sort(key=lambda x: x["net_income"], reverse=True)
    return performance[:top_n]


async def get_underperformers(year: str, bottom_n: int = 10):
    """Get bottom N performers."""
    cached_entities = load_members_from_cache("Consol", "Entity")
    if not cached_entities:
        return []
    
    entities = [item.get("name") for item in cached_entities.get("items", []) if item.get("name")]
    exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total"]
    entities = [e for e in entities if not any(kw in e for kw in exclude_keywords)]
    
    performance = []
    for entity in entities[:100]:  # Limit for performance
        value = await get_entity_performance(entity, year)
        if value is not None:
            performance.append({"entity": entity, "net_income": value})
    
    performance.sort(key=lambda x: x["net_income"])
    return performance[:bottom_n]


async def get_consolidated_total(year: str) -> float | None:
    """Get consolidated total Net Income."""
    return await get_entity_performance("FCCS_Total Geography", year)


def get_event_loop():
    """Get or create event loop for async operations."""
    global _loop
    try:
        # Try to get the current running loop
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # No running loop, create a new one
        if _loop is None or _loop.is_closed():
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
        return _loop


def run_async(coro):
    """Run async coroutine, handling both running and new event loops."""
    import concurrent.futures
    import threading
    
    try:
        # Check if there's a running event loop
        loop = asyncio.get_running_loop()
        # If we're here, there's a running loop (Streamlit's)
        # Run the coroutine in a separate thread with its own event loop
        result = None
        exception = None
        
        def run_in_thread():
            nonlocal result, exception
            try:
                # Create a new event loop in this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(coro)
                new_loop.close()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=60)  # 60 second timeout
        
        if thread.is_alive():
            raise TimeoutError("Async operation timed out")
        
        if exception:
            raise exception
        
        return result
    except RuntimeError:
        # No running loop, can use asyncio.run directly
        return asyncio.run(coro)


def run_dashboard():
    """Run the Streamlit dashboard."""
    st.set_page_config(
        page_title="FCCS Performance Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 FCCS Performance Dashboard")
    st.markdown("Oracle EPM Cloud Financial Consolidation and Close - Performance Analytics")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        year = st.selectbox("Select Year", ["FY24", "FY25"], index=1)
        top_n = st.slider("Top N Performers", 5, 20, 10)
        bottom_n = st.slider("Bottom N Underperformers", 5, 20, 10)
        
        st.markdown("---")
        st.header("ℹ️ Info")
        st.info("""
        This dashboard shows:
        - Top performing entities
        - Underperforming entities
        - Monthly performance trends
        - Divestiture opportunities
        """)
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Initialize agent
    @st.cache_resource
    def init_agent():
        try:
            config = load_config()
            app_name = run_async(initialize_agent(config))
            return config, True
        except Exception as e:
            st.error(f"Agent initialization error: {e}")
            return None, False
    
    config, connected = init_agent()
    
    if not connected:
        st.error("❌ Failed to connect to FCCS")
        st.info("""
        Please check:
        1. Your `.env` file has correct FCCS credentials
        2. FCCS URL is accessible
        3. Network connectivity
        """)
        st.stop()
    
    st.success("✅ Connected to FCCS")
    
    # Get consolidated total
    with st.spinner("Loading consolidated data..."):
        consolidated = run_async(get_consolidated_total(year))
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Consolidated Net Income",
            f"${consolidated:,.2f}" if consolidated else "N/A",
            delta=f"{abs(consolidated):,.2f} Loss" if consolidated and consolidated < 0 else None
        )
    
    with col2:
        st.metric("Year", year)
    
    with col3:
        st.metric("Application", "Consol")
    
    with col4:
        st.metric("Scenario", "Actual")
    
    st.markdown("---")
    
    # Top Performers and Underperformers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🏆 Top {top_n} Performers - {year}")
        with st.spinner("Loading top performers..."):
            top_performers = run_async(get_top_performers(year, top_n))
        
        if top_performers:
            df_top = pd.DataFrame(top_performers)
            df_top['rank'] = range(1, len(df_top) + 1)
            
            # Bar chart
            fig_top = px.bar(
                df_top,
                x='net_income',
                y='entity',
                orientation='h',
                title=f'Top {top_n} Performers',
                labels={'net_income': 'Net Income ($)', 'entity': 'Entity'},
                color='net_income',
                color_continuous_scale='Greens'
            )
            fig_top.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)
            
            # Table
            st.dataframe(
                df_top[['rank', 'entity', 'net_income']].rename(columns={
                    'rank': 'Rank',
                    'entity': 'Entity',
                    'net_income': 'Net Income ($)'
                }).style.format({'Net Income ($)': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data available")
    
    with col2:
        st.subheader(f"⚠️ Top {bottom_n} Underperformers - {year}")
        with st.spinner("Loading underperformers..."):
            underperformers = run_async(get_underperformers(year, bottom_n))
        
        if underperformers:
            df_bottom = pd.DataFrame(underperformers)
            df_bottom['rank'] = range(1, len(df_bottom) + 1)
            
            # Bar chart
            fig_bottom = px.bar(
                df_bottom,
                x='net_income',
                y='entity',
                orientation='h',
                title=f'Top {bottom_n} Underperformers',
                labels={'net_income': 'Net Income ($)', 'entity': 'Entity'},
                color='net_income',
                color_continuous_scale='Reds'
            )
            fig_bottom.update_layout(height=400, yaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig_bottom, use_container_width=True)
            
            # Table
            st.dataframe(
                df_bottom[['rank', 'entity', 'net_income']].rename(columns={
                    'rank': 'Rank',
                    'entity': 'Entity',
                    'net_income': 'Net Income ($)'
                }).style.format({'Net Income ($)': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data available")
    
    st.markdown("---")
    
    # Entity Performance Trend
    st.subheader("📈 Entity Performance Trend")
    
    entity_select = st.selectbox(
        "Select Entity to Analyze",
        options=[p['entity'] for p in top_performers[:5]] + [u['entity'] for u in underperformers[:5]] if top_performers and underperformers else [],
        index=0 if top_performers else None
    )
    
    if entity_select:
        with st.spinner(f"Loading monthly data for {entity_select}..."):
            monthly_data = run_async(get_monthly_data(entity_select, year))
        
        if monthly_data:
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            monthly_values = [monthly_data.get(m, None) for m in months]
            
            df_monthly = pd.DataFrame({
                'Month': months,
                'Net Income': monthly_values
            })
            
            fig_trend = px.line(
                df_monthly,
                x='Month',
                y='Net Income',
                title=f'{entity_select} - Monthly Performance Trend',
                markers=True
            )
            fig_trend.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            fig_trend.update_layout(height=400)
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Calculate monthly changes
            df_monthly['Monthly Change'] = df_monthly['Net Income'].diff()
            st.dataframe(
                df_monthly.style.format({
                    'Net Income': '${:,.2f}',
                    'Monthly Change': '${:,.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown("**FCCS Performance Dashboard** | Data from Oracle EPM Cloud FCCS")


if __name__ == "__main__":
    run_dashboard()

