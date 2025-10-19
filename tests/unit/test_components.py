"""Tests for reusable Streamlit components."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestComponentsModule:
    """Test that components module can be imported."""

    def test_import_components(self):
        """Test importing components module."""
        from app.utils.components import (
            create_data_table,
            create_filter_sidebar,
            display_dataframe_with_download,
            display_metric_card,
            display_metric_row,
            initialize_session_state,
            require_authentication,
            show_error_boundary,
            show_session_state_debug,
            with_loading_state,
        )

        # Verify all functions exist
        assert callable(display_metric_card)
        assert callable(display_metric_row)
        assert callable(create_filter_sidebar)
        assert callable(display_dataframe_with_download)
        assert callable(with_loading_state)
        assert callable(show_error_boundary)
        assert callable(require_authentication)
        assert callable(show_session_state_debug)
        assert callable(initialize_session_state)
        assert callable(create_data_table)


class TestInitializeSessionState:
    """Test session state initialization."""

    def test_initialize_session_state_basic(self):
        """Test basic session state initialization."""
        from app.utils.components import initialize_session_state

        # Mock st.session_state
        with patch("app.utils.components.st") as mock_st:
            mock_st.session_state = {}

            defaults = {
                "authenticated": False,
                "username": None,
                "count": 0,
            }

            initialize_session_state(defaults)

            # Verify all defaults were set
            assert mock_st.session_state["authenticated"] is False
            assert mock_st.session_state["username"] is None
            assert mock_st.session_state["count"] == 0

    def test_initialize_session_state_preserves_existing(self):
        """Test that existing state is not overwritten."""
        from app.utils.components import initialize_session_state

        with patch("app.utils.components.st") as mock_st:
            # Pre-populate session state
            mock_st.session_state = {"authenticated": True}

            defaults = {
                "authenticated": False,  # Should not overwrite
                "username": None,  # Should be set
            }

            initialize_session_state(defaults)

            # Existing value preserved
            assert mock_st.session_state["authenticated"] is True
            # New value set
            assert mock_st.session_state["username"] is None


class TestWithLoadingState:
    """Test loading state wrapper."""

    def test_with_loading_state_success(self):
        """Test loading wrapper with successful function."""
        from app.utils.components import with_loading_state

        def sample_func(x, y):
            return x + y

        with patch("app.utils.components.st") as mock_st:
            result = with_loading_state(sample_func, "Loading...", 2, 3)

            # Function executed correctly
            assert result == 5
            # Spinner was called
            mock_st.spinner.assert_called_once_with("Loading...")

    def test_with_loading_state_custom_message(self):
        """Test loading wrapper with custom message."""
        from app.utils.components import with_loading_state

        def sample_func():
            return "done"

        with patch("app.utils.components.st") as mock_st:
            with_loading_state(sample_func, "Custom loading message...")

            mock_st.spinner.assert_called_once_with("Custom loading message...")


class TestShowErrorBoundary:
    """Test error boundary wrapper."""

    def test_show_error_boundary_success(self):
        """Test error boundary with successful function."""
        from app.utils.components import show_error_boundary

        def sample_func(x):
            return x * 2

        with patch("app.utils.components.st"):
            result = show_error_boundary(sample_func, 5)
            assert result == 10

    def test_show_error_boundary_handles_error(self):
        """Test error boundary catches and displays errors."""
        from app.utils.components import show_error_boundary

        def failing_func():
            raise ValueError("Test error")

        with patch("app.utils.components.st") as mock_st:
            result = show_error_boundary(failing_func)

            # Returns None on error
            assert result is None
            # Error was displayed
            mock_st.error.assert_called_once()
            assert "Test error" in str(mock_st.error.call_args)


class TestDisplayMetricRow:
    """Test metric row display."""

    def test_display_metric_row_basic(self):
        """Test displaying multiple metrics."""
        from app.utils.components import display_metric_row

        metrics = [
            {"title": "Players", "value": 100},
            {"title": "Teams", "value": 20},
        ]

        with patch("app.utils.components.st") as mock_st:
            mock_st.columns.return_value = [MagicMock(), MagicMock()]

            display_metric_row(metrics)

            # Columns created
            mock_st.columns.assert_called_once_with(2)
            # Metrics displayed
            assert mock_st.metric.call_count == 2

    def test_display_metric_row_with_deltas(self):
        """Test metrics with delta values."""
        from app.utils.components import display_metric_row

        metrics = [
            {"title": "Score", "value": 100, "delta": 5},
        ]

        with patch("app.utils.components.st") as mock_st:
            mock_st.columns.return_value = [MagicMock()]

            display_metric_row(metrics)

            # Metric called with delta
            call_args = mock_st.metric.call_args
            assert call_args[1]["delta"] == 5


class TestDisplayDataframeWithDownload:
    """Test dataframe display with download."""

    def test_display_dataframe_with_download(self):
        """Test dataframe display and download button."""
        from app.utils.components import display_dataframe_with_download

        df = pd.DataFrame({"name": ["Alice", "Bob"], "score": [95, 87]})

        with patch("app.utils.components.st") as mock_st:
            display_dataframe_with_download(df, "Test Table")

            # Subheader displayed
            mock_st.subheader.assert_called_once_with("Test Table")
            # Dataframe displayed
            mock_st.dataframe.assert_called_once()
            # Download button created
            mock_st.download_button.assert_called_once()

    def test_display_dataframe_custom_filename(self):
        """Test custom filename for download."""
        from app.utils.components import display_dataframe_with_download

        df = pd.DataFrame({"col": [1, 2]})

        with patch("app.utils.components.st") as mock_st:
            display_dataframe_with_download(
                df, "Table", filename="custom.csv"
            )

            call_args = mock_st.download_button.call_args
            assert call_args[1]["file_name"] == "custom.csv"


class TestCreateDataTable:
    """Test data table component."""

    def test_create_data_table_basic(self):
        """Test basic data table creation."""
        from app.utils.components import create_data_table

        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})

        with patch("app.utils.components.st") as mock_st:
            result = create_data_table(df, "Users", show_download=False, show_search=False)

            # Returns dataframe
            assert result.equals(df)
            # Title displayed
            mock_st.subheader.assert_called_once_with("Users")
            # Dataframe displayed
            mock_st.dataframe.assert_called_once()

    def test_create_data_table_with_search(self):
        """Test data table with search functionality."""
        from app.utils.components import create_data_table

        df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})

        with patch("app.utils.components.st") as mock_st:
            # Mock search input
            mock_st.text_input.return_value = "Alice"

            result = create_data_table(df, "Users", show_search=True, show_download=False)

            # Search input created
            mock_st.text_input.assert_called_once()
            # Result is filtered (would be in real execution)
            assert isinstance(result, pd.DataFrame)
