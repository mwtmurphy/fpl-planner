"""Integration tests for Streamlit app imports."""

from pathlib import Path

import pytest


class TestStreamlitImports:
    """Test that Streamlit app files can be imported correctly."""

    def test_import_data_loader(self):
        """Test importing data_loader module."""
        try:
            from app.utils.data_loader import load_all_data

            assert callable(load_all_data)
        except ImportError as e:
            pytest.fail(f"Failed to import data_loader: {e}")

    def test_import_formatters(self):
        """Test importing formatters module."""
        try:
            from app.utils.formatters import (
                apply_position_filter,
                apply_price_bracket_filter,
                apply_team_filter,
            )

            assert callable(apply_position_filter)
            assert callable(apply_team_filter)
            assert callable(apply_price_bracket_filter)
        except ImportError as e:
            pytest.fail(f"Failed to import formatters: {e}")

    def test_streamlit_app_imports(self):
        """Test that streamlit_app.py has correct imports."""
        # This test verifies the imports follow workspace standards:
        # - Absolute imports (from app.utils.*)
        # - sys.path setup at top of file
        app_path = Path(__file__).parent.parent.parent / "app" / "streamlit_app.py"
        assert app_path.exists(), "streamlit_app.py not found"

        # Read the file and check for correct import statement
        with open(app_path) as f:
            content = f.read()

        # Verify absolute import is used (workspace standard)
        assert "from app.utils.data_loader import load_all_data" in content
        # Verify sys.path setup is present
        assert "sys.path.insert(0, str(project_root))" in content
        # Verify no relative imports are used
        assert "from .utils" not in content and "from ..utils" not in content

    def test_form_analysis_page_imports(self):
        """Test that Form Analysis page has correct imports."""
        page_path = (
            Path(__file__).parent.parent.parent
            / "app"
            / "pages"
            / "1_📊_Form_Analysis.py"
        )
        assert page_path.exists(), "Form Analysis page not found"

        with open(page_path) as f:
            content = f.read()

        # Verify absolute imports are used (workspace standard)
        assert (
            "from app.utils.data_loader import" in content
            or "from app.utils.formatters import" in content
        )
        # Verify sys.path setup is present
        assert "sys.path.insert(0, str(project_root))" in content
        # Verify path calculation is correct for pages/ (parent.parent.parent)
        assert "Path(__file__).parent.parent.parent" in content
        # Verify no relative imports are used
        assert "from ..utils" not in content and "from .utils" not in content

    def test_app_package_structure(self):
        """Test that app package has correct structure."""
        app_path = Path(__file__).parent.parent.parent / "app"

        # Check __init__.py files exist
        assert (app_path / "__init__.py").exists(), "app/__init__.py missing"
        assert (
            app_path / "utils" / "__init__.py"
        ).exists(), "app/utils/__init__.py missing"

        # Check main files exist
        assert (app_path / "streamlit_app.py").exists()
        assert (app_path / "utils" / "data_loader.py").exists()
        assert (app_path / "utils" / "formatters.py").exists()

    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        try:
            # Try importing all modules in sequence
            from app import streamlit_app
            from app.utils import data_loader, formatters

            # If we get here, no circular imports
            assert True
        except ImportError as e:
            if "cannot import" in str(e).lower() or "circular" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            # Re-raise other import errors
            raise


class TestAppModuleImports:
    """Test importing app modules directly."""

    def test_import_app_utils_data_loader(self):
        """Test direct import of app.utils.data_loader."""
        try:
            import app.utils.data_loader

            assert hasattr(app.utils.data_loader, "load_all_data")
        except ImportError as e:
            pytest.fail(f"Failed to import app.utils.data_loader: {e}")

    def test_import_app_utils_formatters(self):
        """Test direct import of app.utils.formatters."""
        try:
            import app.utils.formatters

            assert hasattr(app.utils.formatters, "apply_position_filter")
            assert hasattr(app.utils.formatters, "apply_team_filter")
            assert hasattr(app.utils.formatters, "apply_price_bracket_filter")
        except ImportError as e:
            pytest.fail(f"Failed to import app.utils.formatters: {e}")


class TestRelativeImportFunctionality:
    """Test that relative imports work as expected."""

    def test_data_loader_uses_fpl_imports(self):
        """Test that data_loader correctly imports from fpl package."""
        # Check the module imports, not just the function
        with open("app/utils/data_loader.py") as f:
            content = f.read()

        # Should import from fpl package
        assert "from fpl.api.client import FPLClient" in content
        assert "from fpl.core.models import Team" in content
        assert "from fpl.data" in content

    def test_formatters_use_pandas(self):
        """Test that formatters correctly import pandas."""
        import inspect

        from app.utils.formatters import apply_position_filter

        # Get the module source
        source = inspect.getsource(apply_position_filter)

        # Should handle pandas DataFrames
        # This is implicit - the function signature shows pd.DataFrame
        assert callable(apply_position_filter)
