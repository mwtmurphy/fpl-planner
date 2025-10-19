#!/usr/bin/env python3
"""
FPL Data Validation Module

This module validates the collected FPL data to ensure it meets quality standards
before proceeding to feature engineering.
"""

from pathlib import Path
from typing import Dict

import pandas as pd


class FPLDataValidator:
    """Validates FPL data quality and structure."""

    def __init__(self, data_dir: str = "data/raw"):
        """Initialize the validator."""
        self.data_dir = Path(data_dir)

    def validate_players_data(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Validate players dataset."""
        checks = {}

        # Basic structure checks
        checks["has_minimum_rows"] = len(df) >= 500
        checks["has_required_columns"] = all(
            col in df.columns
            for col in [
                "player_id",
                "web_name",
                "team_id",
                "element_type",
                "now_cost",
                "total_points",
            ]
        )

        # Data quality checks
        checks["no_missing_ids"] = df["player_id"].notna().all()
        checks["valid_positions"] = df["element_type"].isin([1, 2, 3, 4]).all()
        checks["valid_prices"] = (df["now_cost"] > 0).all()
        checks["no_negative_points"] = (df["total_points"] >= 0).all()

        return checks

    def validate_fixtures_data(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Validate fixtures dataset."""
        checks = {}

        # Basic structure checks
        checks["has_minimum_rows"] = len(df) >= 380  # 20 teams * 38 GWs / 2
        checks["has_required_columns"] = all(
            col in df.columns
            for col in [
                "fixture_id",
                "gameweek",
                "team_h",
                "team_a",
                "team_h_difficulty",
                "team_a_difficulty",
            ]
        )

        # Data quality checks
        checks["no_missing_fixture_ids"] = df["fixture_id"].notna().all()
        checks["valid_gameweeks"] = df["gameweek"].between(1, 38).all()
        checks["valid_difficulties"] = (
            df["team_h_difficulty"].between(1, 5).all()
            and df["team_a_difficulty"].between(1, 5).all()
        )
        checks["different_teams"] = (df["team_h"] != df["team_a"]).all()

        return checks

    def validate_results_data(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Validate results dataset."""
        checks = {}

        if len(df) == 0:
            checks["has_minimum_rows"] = False
            checks["non_empty"] = False
            return checks

        # Basic structure checks
        checks["has_minimum_rows"] = len(df) >= 10000  # Players * gameweeks
        checks["has_required_columns"] = all(
            col in df.columns
            for col in ["player_id", "gameweek", "minutes", "total_points"]
        )

        # Data quality checks
        checks["no_missing_ids"] = df["player_id"].notna().all()
        checks["valid_gameweeks"] = df["gameweek"].between(1, 38).all()
        checks["valid_minutes"] = (df["minutes"] >= 0).all() and (
            df["minutes"] <= 90
        ).all()
        checks["no_negative_points"] = (df["total_points"] >= 0).all()
        checks["non_empty"] = True

        return checks

    def validate_all_data(self) -> Dict[str, Dict[str, bool]]:
        """Validate all datasets and return comprehensive report."""
        print("🔍 Validating collected data...")

        results = {}

        # Load and validate each dataset
        try:
            # Players data
            players_file = self.data_dir / "players.csv"
            if players_file.exists():
                players_df = pd.read_csv(players_file)
                results["players"] = self.validate_players_data(players_df)
                print(f"  Players data: {len(players_df)} rows")
            else:
                print("  ❌ Players file not found")
                results["players"] = {"file_exists": False}

            # Fixtures data
            fixtures_file = self.data_dir / "fixtures.csv"
            if fixtures_file.exists():
                fixtures_df = pd.read_csv(fixtures_file)
                results["fixtures"] = self.validate_fixtures_data(fixtures_df)
                print(f"  Fixtures data: {len(fixtures_df)} rows")
            else:
                print("  ❌ Fixtures file not found")
                results["fixtures"] = {"file_exists": False}

            # Results data
            results_file = self.data_dir / "results.csv"
            if results_file.exists():
                results_df = pd.read_csv(results_file)
                results["results"] = self.validate_results_data(results_df)
                print(f"  Results data: {len(results_df)} rows")
            else:
                print("  ❌ Results file not found")
                results["results"] = {"file_exists": False}

        except Exception as e:
            print(f"  ❌ Validation error: {e}")
            return {"error": str(e)}

        return results

    def print_validation_report(self, results: Dict[str, Dict[str, bool]]) -> None:
        """Print a formatted validation report."""
        print("\n" + "=" * 50)
        print("📊 DATA VALIDATION REPORT")
        print("=" * 50)

        if "error" in results:
            print(f"❌ Validation failed: {results['error']}")
            return

        all_passed = True

        for dataset_name, checks in results.items():
            print(f"\n{dataset_name.upper()} DATA:")

            dataset_passed = True
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name.replace('_', ' ').title()}")
                if not passed:
                    dataset_passed = False
                    all_passed = False

            dataset_status = "✅ PASSED" if dataset_passed else "❌ FAILED"
            print(f"  {dataset_status}")

        print("\n" + "=" * 50)
        overall_status = (
            "✅ ALL VALIDATIONS PASSED" if all_passed else "❌ SOME VALIDATIONS FAILED"
        )
        print(f"OVERALL: {overall_status}")
        print("=" * 50)

        if not all_passed:
            print(
                "\n⚠️  Please check the data collection process and resolve "
                "issues before proceeding."
            )

    def run_validation(self) -> bool:
        """Run complete validation and return success status."""
        results = self.validate_all_data()
        self.print_validation_report(results)

        # Check if all validations passed
        if "error" in results:
            return False

        for dataset_checks in results.values():
            for passed in dataset_checks.values():
                if not passed:
                    return False

        return True


def main():
    """Main entry point for data validation."""
    validator = FPLDataValidator()
    success = validator.run_validation()

    if success:
        print("✅ Data validation completed successfully!")
        exit(0)
    else:
        print("❌ Data validation failed!")
        exit(1)


if __name__ == "__main__":
    main()
