"""Reusable Streamlit UI components.

This module provides reusable UI components following workspace standards
for component reusability and consistency.
"""

from typing import Any, Callable

import pandas as pd
import streamlit as st


def display_metric_card(
    title: str,
    value: float | int | str,
    delta: float | int | str | None = None,
    icon: str = "📊",
    help_text: str | None = None,
) -> None:
    """Display a metric in a styled card with icon.

    Args:
        title: Metric title/label
        value: Metric value to display
        delta: Optional delta value (change indicator)
        icon: Icon emoji to display (default: 📊)
        help_text: Optional help text tooltip

    Example:
        >>> display_metric_card("Revenue", 1000, delta=50, icon="💰")
    """
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"<h1 style='text-align: center;'>{icon}</h1>", unsafe_allow_html=True)
    with col2:
        st.metric(label=title, value=value, delta=delta, help=help_text)


def display_metric_row(
    metrics: list[dict[str, Any]],
    columns: int | None = None,
) -> None:
    """Display multiple metrics in a row.

    Args:
        metrics: List of metric configs, each with keys:
            - title: str
            - value: float | int | str
            - delta: float | int | str | None (optional)
            - icon: str (optional)
            - help: str (optional)
        columns: Number of columns (defaults to len(metrics))

    Example:
        >>> metrics = [
        ...     {"title": "Players", "value": 100, "icon": "👥"},
        ...     {"title": "Teams", "value": 20, "icon": "🏆"},
        ... ]
        >>> display_metric_row(metrics)
    """
    if columns is None:
        columns = len(metrics)

    cols = st.columns(columns)
    for idx, metric in enumerate(metrics):
        with cols[idx]:
            st.metric(
                label=metric["title"],
                value=metric["value"],
                delta=metric.get("delta"),
                help=metric.get("help"),
            )


def create_filter_sidebar(
    filters: dict[str, dict[str, Any]],
    key_prefix: str = "filter",
) -> dict[str, Any]:
    """Create a standardized filter sidebar with various widget types.

    Args:
        filters: Dict mapping filter name to filter config:
            {
                "position": {
                    "type": "multiselect",
                    "label": "Position",
                    "options": ["GK", "DEF", "MID", "FWD"],
                    "default": []
                },
                "price": {
                    "type": "slider",
                    "label": "Max Price",
                    "min": 4.0,
                    "max": 15.0,
                    "default": 15.0
                }
            }
        key_prefix: Prefix for widget keys to avoid conflicts

    Returns:
        Dict of selected filter values

    Example:
        >>> filters = {
        ...     "team": {
        ...         "type": "multiselect",
        ...         "label": "Select Teams",
        ...         "options": ["Arsenal", "Liverpool"]
        ...     }
        ... }
        >>> selected = create_filter_sidebar(filters)
        >>> print(selected["team"])
    """
    selected_filters = {}

    with st.sidebar:
        st.header("🔍 Filters")

        for key, config in filters.items():
            filter_key = f"{key_prefix}_{key}"

            if config["type"] == "multiselect":
                selected_filters[key] = st.multiselect(
                    config["label"],
                    options=config["options"],
                    default=config.get("default", []),
                    help=config.get("help"),
                    key=filter_key,
                )
            elif config["type"] == "selectbox":
                selected_filters[key] = st.selectbox(
                    config["label"],
                    options=config["options"],
                    index=config.get("index", 0),
                    help=config.get("help"),
                    key=filter_key,
                )
            elif config["type"] == "slider":
                selected_filters[key] = st.slider(
                    config["label"],
                    min_value=config["min"],
                    max_value=config["max"],
                    value=config.get("default", config["min"]),
                    help=config.get("help"),
                    key=filter_key,
                )
            elif config["type"] == "date_input":
                selected_filters[key] = st.date_input(
                    config["label"],
                    value=config.get("default"),
                    help=config.get("help"),
                    key=filter_key,
                )

    return selected_filters


def display_dataframe_with_download(
    df: pd.DataFrame,
    title: str,
    filename: str = "data.csv",
    height: int = 600,
    column_config: dict | None = None,
    hide_index: bool = True,
    use_container_width: bool = True,
) -> None:
    """Display dataframe with download button.

    Args:
        df: DataFrame to display
        title: Section title
        filename: CSV filename for download
        height: Table height in pixels
        column_config: Optional column configuration dict
        hide_index: Whether to hide the index
        use_container_width: Whether to use full container width

    Example:
        >>> df = pd.DataFrame({"name": ["Alice", "Bob"], "score": [95, 87]})
        >>> display_dataframe_with_download(df, "Player Scores")
    """
    st.subheader(title)

    # Display dataframe
    st.dataframe(
        df,
        column_config=column_config,
        height=height,
        hide_index=hide_index,
        use_container_width=use_container_width,
    )

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def with_loading_state(
    func: Callable,
    message: str = "Loading...",
    *args,
    **kwargs,
) -> Any:
    """Execute function with loading spinner.

    Args:
        func: Function to execute
        message: Loading message to display
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution

    Example:
        >>> data = with_loading_state(load_data, "Loading players...")
    """
    with st.spinner(message):
        return func(*args, **kwargs)


def show_error_boundary(func: Callable, *args, **kwargs) -> Any:
    """Execute function with error handling UI.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution, or None if error occurred

    Example:
        >>> result = show_error_boundary(risky_operation, param1, param2)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("View Details"):
            st.exception(e)
        return None


def require_authentication(password: str = "secret") -> bool:
    """Require authentication before showing page content.

    Args:
        password: Required password (default: "secret")

    Returns:
        True if authenticated, False otherwise

    Usage:
        >>> if not require_authentication():
        ...     st.stop()
        >>> # Rest of authenticated page code
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Authentication Required")

        with st.form("login_form"):
            entered_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if entered_password == password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid password")

        st.stop()

    return True


def show_session_state_debug(expanded: bool = False) -> None:
    """Display session state debug panel in sidebar.

    Args:
        expanded: Whether to show expanded by default

    Usage:
        >>> # In sidebar
        >>> with st.sidebar:
        ...     show_session_state_debug()
    """
    with st.expander("🔍 Session State Debug", expanded=expanded):
        st.write("**Current Session State:**")

        # Filter out internal Streamlit keys
        filtered_state = {
            k: v for k, v in st.session_state.items()
            if not k.startswith("$$")
        }

        if filtered_state:
            st.json(filtered_state, expanded=True)
        else:
            st.info("No session state variables set")


def initialize_session_state(defaults: dict[str, Any]) -> None:
    """Initialize session state variables with default values.

    Args:
        defaults: Dict mapping state keys to default values

    Example:
        >>> defaults = {
        ...     "authenticated": False,
        ...     "username": None,
        ...     "filters": {},
        ... }
        >>> initialize_session_state(defaults)
    """
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def create_data_table(
    df: pd.DataFrame,
    title: str,
    show_download: bool = True,
    show_search: bool = False,
    key_prefix: str = "table",
    height: int = 600,
) -> pd.DataFrame:
    """Display a data table with optional features.

    Args:
        df: DataFrame to display
        title: Table title
        show_download: Show download button (default: True)
        show_search: Show search box (default: False)
        key_prefix: Prefix for widget keys to avoid conflicts
        height: Table height in pixels

    Returns:
        Filtered DataFrame (same as input if no search)

    Example:
        >>> filtered_df = create_data_table(
        ...     df,
        ...     "Player Stats",
        ...     show_search=True,
        ...     key_prefix="players"
        ... )
    """
    st.subheader(title)

    # Search functionality
    filtered_df = df
    if show_search:
        search = st.text_input(
            "Search",
            key=f"{key_prefix}_search",
            placeholder="Type to search...",
        )
        if search:
            # Search across all string columns
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search, case=False).any(),
                axis=1,
            )
            filtered_df = df[mask]

    # Display table
    st.dataframe(filtered_df, height=height, use_container_width=True)

    # Download button
    if show_download:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            data=csv,
            file_name=f"{title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"{key_prefix}_download",
        )

    return filtered_df
