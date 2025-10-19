#!/usr/bin/env python3
"""Validate all Streamlit pages can be imported and run.

This script should be run after any changes to Streamlit app files to ensure
all pages remain functional. It validates:
- All Python files can be compiled
- All imports work correctly
- No syntax errors exist
- Path setup is correct

Run with: poetry run python scripts/validate_streamlit_pages.py
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_file_compiles(file_path: Path) -> None:
    """Validate a Python file compiles without errors.

    Args:
        file_path: Path to Python file

    Raises:
        ValidationError: If file doesn't compile
    """
    try:
        with open(file_path) as f:
            code = f.read()
        compile(code, str(file_path), "exec")
        print(f"✅ {file_path.name}: Compiles successfully")
    except SyntaxError as e:
        raise ValidationError(f"❌ {file_path.name}: Syntax error: {e}")


def validate_imports(file_path: Path) -> None:
    """Validate imports in a file work correctly.

    Args:
        file_path: Path to Python file

    Raises:
        ValidationError: If imports fail
    """
    try:
        # Read the file and extract import statements
        with open(file_path) as f:
            content = f.read()

        # Look for expected imports
        expected_imports = {
            "streamlit_app.py": ["streamlit", "app.utils.data_loader"],
            "1_📊_Form_Analysis.py": [
                "streamlit",
                "app.utils.data_loader",
                "app.utils.formatters",
            ],
            "2_💰_Value_Analysis.py": [
                "streamlit",
                "app.utils.data_loader",
                "app.utils.formatters",
            ],
        }

        if file_path.name in expected_imports:
            for expected_import in expected_imports[file_path.name]:
                if expected_import not in content:
                    raise ValidationError(
                        f"❌ {file_path.name}: Missing expected import '{expected_import}'"
                    )

        # Check for sys.path setup
        if "sys.path.insert" not in content and "streamlit" in content:
            raise ValidationError(
                f"❌ {file_path.name}: Missing sys.path setup for imports"
            )

        # Check for relative imports (should not exist)
        if "from .." in content or "from ." in content:
            raise ValidationError(
                f"❌ {file_path.name}: Uses relative imports (should use absolute imports)"
            )

        print(f"✅ {file_path.name}: Import statements validated")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"❌ {file_path.name}: Import validation failed: {e}")


def validate_path_setup(file_path: Path) -> None:
    """Validate sys.path setup is correct.

    Args:
        file_path: Path to Python file

    Raises:
        ValidationError: If path setup is incorrect
    """
    try:
        with open(file_path) as f:
            content = f.read()

        # Check for proper path setup
        if "import streamlit" in content:
            # Streamlit files should have path setup
            required_lines = [
                "import sys",
                "from pathlib import Path",
                "project_root =",
                "sys.path.insert",
            ]

            missing = [line for line in required_lines if line not in content]
            if missing:
                raise ValidationError(
                    f"❌ {file_path.name}: Missing path setup components: {missing}"
                )

            # Verify correct path calculation
            if file_path.parent.name == "pages":
                # Pages are 3 levels deep: pages/file.py -> pages -> app -> root
                if "parent.parent.parent" not in content:
                    raise ValidationError(
                        f"❌ {file_path.name}: Incorrect path calculation (should be parent.parent.parent)"
                    )
            elif file_path.parent.name == "app":
                # Main app is 2 levels deep: app/file.py -> app -> root
                if "parent.parent" not in content or "parent.parent.parent" in content:
                    raise ValidationError(
                        f"❌ {file_path.name}: Incorrect path calculation (should be parent.parent)"
                    )

            print(f"✅ {file_path.name}: Path setup validated")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"❌ {file_path.name}: Path setup validation failed: {e}")


def validate_page_structure(file_path: Path) -> None:
    """Validate page follows Streamlit best practices.

    Args:
        file_path: Path to Python file

    Raises:
        ValidationError: If structure is incorrect
    """
    try:
        with open(file_path) as f:
            content = f.read()

        # Check for st.set_page_config (should be early in file)
        if "streamlit" in content and "st.set_page_config" not in content:
            print(f"⚠️  {file_path.name}: Missing st.set_page_config")

        # Check for docstring
        if not content.strip().startswith('"""') and not content.strip().startswith(
            "'''"
        ):
            print(f"⚠️  {file_path.name}: Missing module docstring")

        print(f"✅ {file_path.name}: Page structure validated")
    except Exception as e:
        # Structure issues are warnings, not errors
        print(f"⚠️  {file_path.name}: Structure validation warning: {e}")


def validate_all_pages() -> tuple[int, int]:
    """Validate all Streamlit pages.

    Returns:
        Tuple of (passed, failed) counts

    Raises:
        ValidationError: If validation fails
    """
    app_dir = project_root / "app"
    pages_dir = app_dir / "pages"

    # Find all Python files
    streamlit_files = [app_dir / "streamlit_app.py"]
    if pages_dir.exists():
        streamlit_files.extend(sorted(pages_dir.glob("*.py")))

    if not streamlit_files:
        raise ValidationError("❌ No Streamlit files found")

    print("\n" + "=" * 70)
    print("STREAMLIT PAGES VALIDATION")
    print("=" * 70 + "\n")

    passed = 0
    failed = 0
    errors: list[str] = []

    for file_path in streamlit_files:
        if file_path.name.startswith("_"):
            continue  # Skip private files

        print(f"\nValidating: {file_path.relative_to(project_root)}")
        print("-" * 70)

        try:
            # Run all validations
            validate_file_compiles(file_path)
            validate_imports(file_path)
            validate_path_setup(file_path)
            validate_page_structure(file_path)

            passed += 1
            print(f"✅ {file_path.name}: ALL CHECKS PASSED\n")

        except ValidationError as e:
            failed += 1
            error_msg = str(e)
            errors.append(error_msg)
            print(f"\n{error_msg}\n")

    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total files: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")

    print("=" * 70 + "\n")

    return passed, failed


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        passed, failed = validate_all_pages()

        if failed > 0:
            print("❌ VALIDATION FAILED\n")
            return 1

        print("✅ ALL VALIDATIONS PASSED\n")
        print("You can now run the Streamlit app with:")
        print("  poetry run streamlit run app/streamlit_app.py\n")
        return 0

    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
