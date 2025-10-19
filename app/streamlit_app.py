"""FPL Analysis Dashboard - Home Page.

Run with: poetry run streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.utils.components import initialize_session_state, show_session_state_debug
from app.utils.data_loader import load_all_data
from fpl.data.historical import HistoricalDataManager
from fpl.data.storage import DataStorage

# Initialize session state with defaults
initialize_session_state(
    {
        "debug_mode": False,
        "last_refresh": None,
    }
)


def home_page():
    """Home page content."""
    # Title and description
    st.title("🏆 FPL Analysis Dashboard")
    st.markdown(
        """
        Welcome to the **Fantasy Premier League Analysis Dashboard**!

        This app provides interactive analysis of FPL players to help you make
        better transfer and captain decisions.
        """
    )

    # Load data
    with st.spinner("Loading player data..."):
        df, teams_dict, last_update = load_all_data()

    # Summary statistics
    st.header("📊 Quick Stats")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Players", len(df))

    with col2:
        avg_form = df["form"].mean()
        st.metric("Average Form", f"{avg_form:.1f}")

    with col3:
        avg_value = df["value"].mean()
        st.metric("Average Value", f"{avg_value:.1f} pts/£m")

    with col4:
        avg_points = df["total_points"].mean()
        st.metric("Average Points", f"{avg_points:.0f}")

    # Analysis pages navigation
    st.header("📑 Analysis Pages")

    st.markdown(
        """
        Select a page from the sidebar to explore the analysis:
        """
    )

    st.subheader("📊 Form Analysis")
    st.markdown(
        """
        **Which players are in the best current form?**

        Analyze players based on their average points over the last 5 games played.
        Filter by position and team to find the best in-form picks.

        - Sortable by form score
        - Filter by position (GK, DEF, MID, FWD)
        - Filter by team
        - Export to CSV
        """
    )

    # Instructions
    st.header("ℹ️ How to Use")
    st.markdown(
        """
        1. **Navigate to Form Analysis** from the sidebar
        2. **Apply filters** to narrow down your analysis
        3. **Sort the table** by clicking column headers
        4. **Download results** as CSV for further analysis

        Data is cached for 1 hour to improve performance. Use the refresh button
        in the sidebar if you need the latest data.
        """
    )

    # Footer
    st.divider()
    st.caption(f"📅 Data last updated: {last_update}")
    st.caption("🔄 Data automatically refreshes every hour")
    st.caption("⚡ Powered by the official FPL API")

    # Sidebar info
    with st.sidebar:
        st.header("About")
        st.markdown(
            """
            This dashboard uses data from the official
            **Fantasy Premier League API** to provide
            real-time player analysis.

            **Form** = Average points over last 5 games played

            **Value** = Total points ÷ Price (in £m)
            """
        )

        st.divider()

        # Data Status
        st.markdown("**Data Status**")

        # Check if local data exists
        data_dir = Path("data")
        storage = DataStorage(data_dir=data_dir)
        player_histories_dir = data_dir / "current" / "player_histories"
        has_local_data = player_histories_dir.exists() and any(
            player_histories_dir.glob("*.json")
        )

        if has_local_data:
            # Show local data status
            manager = HistoricalDataManager(data_dir=data_dir)
            summary = manager.get_data_summary()

            st.success(f"✅ Loaded {len(df)} players (from local storage)")
            st.info(f"🕒 Updated: {last_update}")

            # Historical data info
            if summary["historical_seasons"] > 0:
                st.caption(
                    f"📚 Historical: {summary['historical_seasons']} seasons ({', '.join(summary['available_seasons'][-3:])}...)"
                )

            # Update instructions
            with st.expander("🔄 Update Data"):
                st.markdown(
                    """
                    **To update with latest gameweek(s):**
                    ```bash
                    poetry run python scripts/update_latest_gameweeks.py --gameweeks 1
                    ```

                    **To re-import historical data:**
                    ```bash
                    poetry run python scripts/import_historical_data.py
                    ```

                    **To collect full current season:**
                    ```bash
                    poetry run python scripts/collect_current_season.py
                    ```
                    """
                )
        else:
            # No local data - using API
            st.warning("⚠️ Loading from API (no local data)")
            st.info(f"🕒 Updated: {last_update}")

            with st.expander("💾 Setup Local Data"):
                st.markdown(
                    """
                    **To enable faster loading, collect local data:**

                    1. **Import historical data** (2-3 mins):
                    ```bash
                    poetry run python scripts/import_historical_data.py
                    ```

                    2. **Collect current season** (60-70 mins):
                    ```bash
                    poetry run python scripts/collect_current_season.py
                    ```

                    3. **Refresh the app** to use local data
                    """
                )

        if st.button(
            "🔄 Refresh App", key="refresh_app_button", use_container_width=True
        ):
            st.cache_data.clear()
            from datetime import datetime

            st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()

        # Session state debug (for development)
        st.divider()
        if st.checkbox("🐛 Debug Mode", key="debug_mode_toggle"):
            show_session_state_debug(expanded=True)


# Page configuration
st.set_page_config(
    page_title="FPL Analysis Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define pages
home = st.Page(home_page, title="Home", icon="🏠", default=True)
form_analysis = st.Page("pages/1_📊_Form_Analysis.py", title="Form Analysis", icon="📊")

# Create navigation
pg = st.navigation([home, form_analysis])

# Run the selected page
pg.run()
