"""Form Analysis Page - Which players are in the best current form?"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.utils.data_loader import load_all_data, load_snapshot_data
from app.utils.formatters import apply_position_filter, apply_team_filter

# Page configuration
st.set_page_config(
    page_title="Form Analysis",
    page_icon="📊",
    layout="wide",
)

# Title and description
st.title("📊 Form Analysis")
st.markdown("**Which players are in the best current form?**")
st.markdown(
    """
    Compare fixture-based form (includes all games) vs game-based form (only games played).
    Use Value (games) to find players with best projected season performance.
    """
)

# SIDEBAR FILTERS
st.sidebar.header("Filters")

# Season filter
from fpl.data.historical import HistoricalDataManager
manager = HistoricalDataManager()
available_seasons = manager.get_available_seasons()
season_options = ["2024-25 (Current)"] + available_seasons[::-1]  # Reverse to show newest first

selected_season = st.sidebar.selectbox(
    "Season",
    season_options,
    index=0,
    help="Select season to analyze",
    key="form_analysis_season_filter",
)

# Gameweek filter
if selected_season == "2024-25 (Current)":
    current_gw = manager.get_last_collected_gameweek()
    if current_gw:
        gw_options = list(range(1, current_gw + 1))
    else:
        gw_options = list(range(1, 39))
else:
    gw_options = list(range(1, 39))

selected_gw = st.sidebar.selectbox(
    "Up to Gameweek",
    gw_options[::-1],  # Reverse to show latest first
    index=0,
    help="Show stats through end of this gameweek",
    key="form_analysis_gameweek_filter",
)

st.sidebar.divider()

# Load data based on filters
with st.spinner("Loading player data..."):
    if selected_season == "2024-25 (Current)" and selected_gw == (current_gw if current_gw else 38):
        # Load current full data
        df, teams_dict, last_update = load_all_data()
    else:
        # Load snapshot data
        df, teams_dict, last_update = load_snapshot_data(selected_season, selected_gw)

# Position filter
position_options = ["All", "GK", "DEF", "MID", "FWD"]
selected_positions = st.sidebar.multiselect(
    "Position",
    position_options,
    default=["All"],
    help="Filter players by position",
    key="form_analysis_position_filter",
)

# Team filter
team_names = sorted(teams_dict.values())
selected_teams = st.sidebar.multiselect(
    "Team",
    team_names,
    default=[],
    help="Filter players by team (leave empty for all)",
    key="form_analysis_team_filter",
)

st.sidebar.divider()
st.sidebar.caption(f"Last updated: {last_update}")

# Apply filters
filtered_df = df.copy()
filtered_df = apply_position_filter(filtered_df, selected_positions)
filtered_df = apply_team_filter(filtered_df, selected_teams)

# Sort by form (games) descending (default sort)
filtered_df = filtered_df.sort_values("form_games", ascending=False).reset_index(drop=True)

# METRICS ROW
st.subheader("Summary Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Players Shown", len(filtered_df))

with col2:
    avg_form = filtered_df["form_games"].mean() if len(filtered_df) > 0 else 0
    st.metric("Average Form (games)", f"{avg_form:.1f}")

with col3:
    if len(filtered_df) > 0:
        top_player = filtered_df.iloc[0]
        st.metric(
            "Top Form Player", f"{top_player['name']} ({top_player['form_games']:.1f})"
        )
    else:
        st.metric("Top Form Player", "N/A")

with col4:
    avg_value_games = filtered_df["value_games"].mean() if len(filtered_df) > 0 else 0
    st.metric("Avg Value (games)", f"{avg_value_games:.1f}")

# TABLE
st.subheader("Player Form Table")

# Select columns to display
display_columns = [
    "name",
    "team_name",
    "position",
    "price_formatted",
    "total_points",
    "form_fixtures",
    "value_fixtures",
    "form_games",
    "value_games",
    "ownership",
    "status_circle",
]

# Configure column display
column_config = {
    "name": st.column_config.TextColumn("Player", help="Player name"),
    "team_name": st.column_config.TextColumn("Team", help="Player's team"),
    "position": st.column_config.TextColumn("Pos", help="Position (GK/DEF/MID/FWD)"),
    "price_formatted": st.column_config.TextColumn("Price", help="Current price"),
    "total_points": st.column_config.NumberColumn(
        "Points", help="Total season points", format="%d"
    ),
    "form_fixtures": st.column_config.NumberColumn(
        "Form (fixtures)",
        help="Average points over last 5 fixtures (including when didn't play)",
        format="%.1f",
    ),
    "value_fixtures": st.column_config.NumberColumn(
        "Value (fixtures)",
        help="Total points per £m",
        format="%.1f",
    ),
    "form_games": st.column_config.NumberColumn(
        "Form (games)",
        help="Average points over last 5 games actually played",
        format="%.1f",
    ),
    "value_games": st.column_config.NumberColumn(
        "Value (games)",
        help="Projected season value based on game form (form × 38 ÷ price)",
        format="%.1f",
    ),
    "ownership": st.column_config.NumberColumn(
        "Own %",
        help="Ownership percentage",
        format="%.1f%%",
    ),
    "status_circle": st.column_config.TextColumn(
        "Status", help="Player status (🟢 available, 🟡 doubtful, 🔴 injured/unavailable)"
    ),
}

# Display the dataframe
st.dataframe(
    filtered_df[display_columns],
    column_config=column_config,
    width='stretch',
    hide_index=True,
    height=600,
)

# DOWNLOAD BUTTON
st.subheader("Export Data")
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"fpl_form_analysis_{last_update.replace(' ', '_').replace(':', '-')}.csv",
    mime="text/csv",
    width='stretch',
)

# INSIGHTS
st.divider()
st.subheader("📈 Insights")

if len(filtered_df) > 0:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 5 By Form (games)**")
        top_5 = filtered_df.head(5)[["name", "team_name", "position", "form_games"]]
        for idx, row in top_5.iterrows():
            st.markdown(
                f"- **{row['name']}** ({row['team_name']}, {row['position']}) - {row['form_games']:.1f}"
            )

    with col2:
        st.markdown("**Top 5 By Value (games)**")
        top_5_value = filtered_df.nlargest(5, "value_games")[["name", "team_name", "position", "value_games"]]
        for idx, row in top_5_value.iterrows():
            st.markdown(
                f"- **{row['name']}** ({row['team_name']}, {row['position']}) - {row['value_games']:.1f}"
            )
else:
    st.info("No players match the selected filters.")

# FOOTER
st.divider()
st.caption(
    """
    **Note:**
    - **Form (fixtures)**: Average points over last 5 fixtures (includes 0s when didn't play)
    - **Form (games)**: Average points over last 5 games actually played
    - **Value (fixtures)**: Total season points per £m
    - **Value (games)**: Projected season value based on game form (form × 38 ÷ price)
    """
)
st.caption(f"📅 Data last updated: {last_update}")
