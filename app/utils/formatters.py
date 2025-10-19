"""Display formatting utilities for Streamlit app."""

import pandas as pd


def apply_position_filter(
    df: pd.DataFrame, selected_positions: list[str]
) -> pd.DataFrame:
    """Apply position filter to DataFrame.

    Args:
        df: Player DataFrame
        selected_positions: List of selected positions (can include "All")

    Returns:
        Filtered DataFrame
    """
    if not selected_positions or "All" in selected_positions:
        return df
    return df[df["position"].isin(selected_positions)]


def apply_team_filter(df: pd.DataFrame, selected_teams: list[str]) -> pd.DataFrame:
    """Apply team filter to DataFrame.

    Args:
        df: Player DataFrame
        selected_teams: List of selected team names

    Returns:
        Filtered DataFrame
    """
    if not selected_teams:
        return df
    return df[df["team_name"].isin(selected_teams)]


def apply_price_bracket_filter(
    df: pd.DataFrame, selected_brackets: list[str]
) -> pd.DataFrame:
    """Apply price bracket filter to DataFrame.

    Args:
        df: Player DataFrame
        selected_brackets: List of selected price brackets
            Options: "Budget (<£5.5m)", "Mid (£5.5-9.5m)", "Premium (>£9.5m)"

    Returns:
        Filtered DataFrame
    """
    if not selected_brackets:
        return df

    conditions = []
    if "Budget (<£5.5m)" in selected_brackets:
        conditions.append(df["price"] < 5.5)
    if "Mid (£5.5-9.5m)" in selected_brackets:
        conditions.append((df["price"] >= 5.5) & (df["price"] <= 9.5))
    if "Premium (>£9.5m)" in selected_brackets:
        conditions.append(df["price"] > 9.5)

    if conditions:
        # Combine conditions with OR
        combined = conditions[0]
        for condition in conditions[1:]:
            combined = combined | condition
        return df[combined]

    return df
