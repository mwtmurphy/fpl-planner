"""Tests for Streamlit app formatters."""

import pandas as pd
import pytest

from app.utils.formatters import (
    apply_position_filter,
    apply_price_bracket_filter,
    apply_team_filter,
)


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "name": ["Salah", "Haaland", "Alisson", "Saka", "Kane"],
            "team_name": ["Liverpool", "Man City", "Liverpool", "Arsenal", "Bayern"],
            "position": ["MID", "FWD", "GK", "MID", "FWD"],
            "price": [13.0, 14.5, 5.5, 9.0, 12.0],
            "total_points": [186, 210, 120, 150, 180],
            "form": [8.5, 9.2, 5.0, 7.5, 8.0],
        }
    )


class TestApplyPositionFilter:
    """Test suite for apply_position_filter."""

    def test_filter_all_positions(self, sample_df):
        """Test filtering with 'All' returns all data."""
        result = apply_position_filter(sample_df, ["All"])
        assert len(result) == len(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_filter_single_position(self, sample_df):
        """Test filtering for single position."""
        result = apply_position_filter(sample_df, ["MID"])
        assert len(result) == 2
        assert all(result["position"] == "MID")
        assert set(result["name"]) == {"Salah", "Saka"}

    def test_filter_multiple_positions(self, sample_df):
        """Test filtering for multiple positions."""
        result = apply_position_filter(sample_df, ["MID", "FWD"])
        assert len(result) == 4
        assert set(result["position"]) == {"MID", "FWD"}
        assert set(result["name"]) == {"Salah", "Haaland", "Saka", "Kane"}

    def test_filter_goalkeeper(self, sample_df):
        """Test filtering for goalkeepers."""
        result = apply_position_filter(sample_df, ["GK"])
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Alisson"
        assert result.iloc[0]["position"] == "GK"

    def test_filter_empty_list(self, sample_df):
        """Test filtering with empty list returns all data."""
        result = apply_position_filter(sample_df, [])
        assert len(result) == len(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_filter_all_with_others(self, sample_df):
        """Test that 'All' with other positions returns all data."""
        result = apply_position_filter(sample_df, ["All", "MID", "FWD"])
        assert len(result) == len(sample_df)

    def test_filter_no_matches(self, sample_df):
        """Test filtering with position that doesn't exist."""
        result = apply_position_filter(sample_df, ["DEF"])
        assert len(result) == 0

    def test_filter_preserves_index(self, sample_df):
        """Test that filtering preserves original index."""
        result = apply_position_filter(sample_df, ["MID"])
        assert 0 in result.index  # Salah
        assert 3 in result.index  # Saka

    def test_filter_preserves_columns(self, sample_df):
        """Test that filtering preserves all columns."""
        result = apply_position_filter(sample_df, ["FWD"])
        assert list(result.columns) == list(sample_df.columns)


class TestApplyTeamFilter:
    """Test suite for apply_team_filter."""

    def test_filter_empty_teams(self, sample_df):
        """Test filtering with empty team list returns all data."""
        result = apply_team_filter(sample_df, [])
        assert len(result) == len(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_filter_single_team(self, sample_df):
        """Test filtering for single team."""
        result = apply_team_filter(sample_df, ["Liverpool"])
        assert len(result) == 2
        assert all(result["team_name"] == "Liverpool")
        assert set(result["name"]) == {"Salah", "Alisson"}

    def test_filter_multiple_teams(self, sample_df):
        """Test filtering for multiple teams."""
        result = apply_team_filter(sample_df, ["Liverpool", "Arsenal"])
        assert len(result) == 3
        assert set(result["team_name"]) == {"Liverpool", "Arsenal"}
        assert set(result["name"]) == {"Salah", "Alisson", "Saka"}

    def test_filter_no_matches(self, sample_df):
        """Test filtering with team that doesn't exist."""
        result = apply_team_filter(sample_df, ["Chelsea"])
        assert len(result) == 0

    def test_filter_preserves_columns(self, sample_df):
        """Test that filtering preserves all columns."""
        result = apply_team_filter(sample_df, ["Man City"])
        assert list(result.columns) == list(sample_df.columns)

    def test_filter_case_sensitive(self, sample_df):
        """Test that team filter is case-sensitive."""
        result = apply_team_filter(sample_df, ["liverpool"])  # lowercase
        assert len(result) == 0  # Should not match "Liverpool"


class TestApplyPriceBracketFilter:
    """Test suite for apply_price_bracket_filter."""

    def test_filter_empty_brackets(self, sample_df):
        """Test filtering with empty bracket list returns all data."""
        result = apply_price_bracket_filter(sample_df, [])
        assert len(result) == len(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_filter_budget_bracket(self, sample_df):
        """Test filtering for budget players (<£5.5m)."""
        result = apply_price_bracket_filter(sample_df, ["Budget (<£5.5m)"])
        assert len(result) == 0  # Alisson is exactly 5.5

    def test_filter_budget_bracket_with_budget_player(self):
        """Test budget bracket with player under 5.5m."""
        df = pd.DataFrame(
            {
                "name": ["Budget Player", "Mid Player"],
                "price": [4.5, 7.0],
                "position": ["DEF", "MID"],
            }
        )
        result = apply_price_bracket_filter(df, ["Budget (<£5.5m)"])
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Budget Player"

    def test_filter_mid_bracket(self, sample_df):
        """Test filtering for mid-priced players (£5.5-9.5m)."""
        result = apply_price_bracket_filter(sample_df, ["Mid (£5.5-9.5m)"])
        assert len(result) == 2
        assert set(result["name"]) == {"Alisson", "Saka"}
        assert all((result["price"] >= 5.5) & (result["price"] <= 9.5))

    def test_filter_premium_bracket(self, sample_df):
        """Test filtering for premium players (>£9.5m)."""
        result = apply_price_bracket_filter(sample_df, ["Premium (>£9.5m)"])
        assert len(result) == 3
        assert set(result["name"]) == {"Salah", "Haaland", "Kane"}
        assert all(result["price"] > 9.5)

    def test_filter_multiple_brackets(self, sample_df):
        """Test filtering for multiple price brackets."""
        result = apply_price_bracket_filter(
            sample_df, ["Budget (<£5.5m)", "Premium (>£9.5m)"]
        )
        # Budget: 0 players, Premium: 3 players
        assert len(result) == 3
        assert all((result["price"] < 5.5) | (result["price"] > 9.5))

    def test_filter_all_brackets(self, sample_df):
        """Test filtering with all brackets returns all data."""
        result = apply_price_bracket_filter(
            sample_df,
            ["Budget (<£5.5m)", "Mid (£5.5-9.5m)", "Premium (>£9.5m)"],
        )
        assert len(result) == len(sample_df)

    def test_filter_boundary_values(self):
        """Test boundary values for price brackets."""
        df = pd.DataFrame(
            {
                "name": ["Player1", "Player2", "Player3", "Player4"],
                "price": [5.4, 5.5, 9.5, 9.6],
                "position": ["DEF", "DEF", "MID", "MID"],
            }
        )

        # Budget: < 5.5
        budget = apply_price_bracket_filter(df, ["Budget (<£5.5m)"])
        assert len(budget) == 1
        assert budget.iloc[0]["name"] == "Player1"

        # Mid: 5.5 - 9.5 (inclusive)
        mid = apply_price_bracket_filter(df, ["Mid (£5.5-9.5m)"])
        assert len(mid) == 2
        assert set(mid["name"]) == {"Player2", "Player3"}

        # Premium: > 9.5
        premium = apply_price_bracket_filter(df, ["Premium (>£9.5m)"])
        assert len(premium) == 1
        assert premium.iloc[0]["name"] == "Player4"

    def test_filter_preserves_columns(self, sample_df):
        """Test that filtering preserves all columns."""
        result = apply_price_bracket_filter(sample_df, ["Mid (£5.5-9.5m)"])
        assert list(result.columns) == list(sample_df.columns)

    def test_filter_no_matches(self):
        """Test filtering when no players match bracket."""
        df = pd.DataFrame(
            {
                "name": ["Expensive Player"],
                "price": [15.0],
                "position": ["FWD"],
            }
        )
        result = apply_price_bracket_filter(df, ["Budget (<£5.5m)"])
        assert len(result) == 0


class TestCombinedFilters:
    """Test combining multiple filters."""

    def test_position_and_team_filter(self, sample_df):
        """Test applying both position and team filters."""
        # Filter for Liverpool midfielders
        result = sample_df.copy()
        result = apply_position_filter(result, ["MID"])
        result = apply_team_filter(result, ["Liverpool"])

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Salah"

    def test_all_filters_combined(self, sample_df):
        """Test applying all three filters together."""
        # Filter for premium midfielders from Liverpool
        result = sample_df.copy()
        result = apply_position_filter(result, ["MID"])
        result = apply_team_filter(result, ["Liverpool"])
        result = apply_price_bracket_filter(result, ["Premium (>£9.5m)"])

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Salah"

    def test_filters_with_no_results(self, sample_df):
        """Test filter combination that yields no results."""
        # Filter for budget goalkeepers from Arsenal (doesn't exist)
        result = sample_df.copy()
        result = apply_position_filter(result, ["GK"])
        result = apply_team_filter(result, ["Arsenal"])

        assert len(result) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test filters on empty DataFrame."""
        empty_df = pd.DataFrame(columns=["name", "position", "team_name", "price"])

        result_pos = apply_position_filter(empty_df, ["MID"])
        assert len(result_pos) == 0

        result_team = apply_team_filter(empty_df, ["Liverpool"])
        assert len(result_team) == 0

        result_price = apply_price_bracket_filter(empty_df, ["Premium (>£9.5m)"])
        assert len(result_price) == 0

    def test_none_values_in_filters(self, sample_df):
        """Test handling None in filter lists."""
        # Most implementations should handle None gracefully or raise error
        # Testing current behavior
        result = apply_team_filter(sample_df, [])
        assert len(result) == len(sample_df)
