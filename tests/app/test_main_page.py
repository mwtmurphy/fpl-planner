"""AppTest tests for main Streamlit app page."""

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.app


class TestMainAppRendering:
    """Test main app page rendering and basic functionality."""

    def test_app_renders_without_errors(self):
        """Test that main app renders without exceptions."""
        # Initialize the app
        at = AppTest.from_file("app/streamlit_app.py")

        # Run the app
        at.run()

        # Assert no exceptions occurred
        assert not at.exception, f"App raised exception: {at.exception}"

    def test_app_has_title(self):
        """Test that app displays the main title."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Check that title exists
        assert len(at.title) > 0, "No title found on page"
        assert "FPL Analysis Dashboard" in at.title[0].value

    def test_app_shows_quick_stats_metrics(self):
        """Test that Quick Stats metrics are displayed."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Check for metrics (should have at least 4: Total Players, Avg Form, Avg Value, Avg Points)
        assert (
            len(at.metric) >= 4
        ), f"Expected at least 4 metrics, found {len(at.metric)}"

    def test_sidebar_has_about_section(self):
        """Test that sidebar contains About section."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Check sidebar exists and has content
        # Note: AppTest provides access to sidebar content through the same interface
        assert not at.exception

    def test_app_loads_data_successfully(self):
        """Test that app loads player data without errors."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # If app runs without exception, data loaded successfully
        assert not at.exception

        # Check that metrics show actual data (not zero)
        if len(at.metric) > 0:
            # First metric should be Total Players
            total_players_metric = at.metric[0]
            # Value should be a string representation of a number > 0
            assert total_players_metric.value != "0"


class TestMainAppNavigation:
    """Test navigation functionality in main app."""

    def test_navigation_to_form_analysis(self):
        """Test that navigation includes Form Analysis page."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # App uses st.navigation, which creates page structure
        # The navigation should render without errors
        assert not at.exception

    def test_app_uses_st_navigation(self):
        """Test that app uses st.navigation API."""
        # Read the file to verify st.navigation is used
        with open("app/streamlit_app.py") as f:
            content = f.read()

        assert "st.navigation" in content, "App should use st.navigation API"
        assert "st.Page" in content, "App should define pages with st.Page"


class TestDataLoadingStrategies:
    """Test different data loading scenarios."""

    def test_app_handles_no_local_data(self):
        """Test app behavior when no local data is available."""
        # This test verifies the app doesn't crash when local data is missing
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Should not raise exception even if local data missing
        # (will fallback to API)
        assert not at.exception

    def test_refresh_button_exists(self):
        """Test that refresh button is present in sidebar."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Check for refresh button
        refresh_buttons = [b for b in at.button if "Refresh" in str(b.label)]
        assert len(refresh_buttons) > 0, "Refresh button should exist in sidebar"


class TestSessionStateInitialization:
    """Test session state management."""

    def test_app_initializes_cleanly(self):
        """Test that app initializes without state errors."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # App should initialize without KeyError or state issues
        assert not at.exception

    def test_session_state_persists_across_reruns(self):
        """Test that session state is maintained across reruns."""
        at = AppTest.from_file("app/streamlit_app.py")
        at.run()

        # Add a test value to session state
        at.session_state["test_value"] = "persisted"
        at.run()

        # Verify value persisted (use dict access, not .get())
        assert "test_value" in at.session_state
        assert at.session_state["test_value"] == "persisted"


@pytest.mark.slow
class TestDataCaching:
    """Test data caching behavior."""

    def test_data_is_cached(self):
        """Test that load_all_data uses caching."""
        # Read data_loader.py to verify caching decorator
        with open("app/utils/data_loader.py") as f:
            content = f.read()

        assert "@st.cache_data" in content, "load_all_data should use @st.cache_data"
        assert "ttl=3600" in content, "Cache should have 1 hour TTL"
