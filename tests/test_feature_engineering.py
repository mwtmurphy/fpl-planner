#!/usr/bin/env python3
"""
Unit tests for FPL Feature Engineering Module

Tests cover:
- Data loading and cleaning functionality
- Anti-leakage rolling feature creation
- Fixture difficulty feature engineering
- Minutes likelihood calculations
- Form-based feature creation
- Data validation and output verification
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.append('src')
from feature_engineering import FPLFeatureEngineer


class TestFPLFeatureEngineer:
    """Test suite for FPLFeatureEngineer class"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_players_data(self):
        """Create sample players data for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4],
            'web_name': ['Player1', 'Player2', 'Player3', 'Player4'],
            'element_type': [1, 2, 3, 4],  # GK, DEF, MID, FWD
            'team': [1, 1, 2, 2],
            'now_cost': [50, 45, 60, 70],  # In pence
            'total_points': [50, 45, 80, 60]
        })
    
    @pytest.fixture
    def sample_fixtures_data(self):
        """Create sample fixtures data for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4],
            'event': [1, 1, 2, 2],
            'team_h': [1, 2, 1, 2],
            'team_a': [2, 1, 2, 1],
            'team_h_difficulty': [3, 4, 2, 5],
            'team_a_difficulty': [4, 3, 5, 2],
            'kickoff_time': ['2024-08-17T14:00:00Z'] * 4
        })
    
    @pytest.fixture
    def sample_results_data(self):
        """Create sample results data for testing"""
        return pd.DataFrame({
            'player_id': [1, 2, 3, 4, 1, 2, 3, 4],
            'gameweek': [1, 1, 1, 1, 2, 2, 2, 2],
            'total_points': [10, 6, 8, 5, 8, 4, 12, 7],
            'minutes': [90, 90, 75, 60, 90, 0, 90, 80],
            'goals_scored': [0, 0, 1, 1, 0, 0, 2, 0],
            'assists': [0, 1, 0, 0, 1, 0, 1, 1],
            'clean_sheets': [1, 1, 0, 0, 0, 0, 0, 0],
            'bonus': [2, 0, 3, 0, 1, 0, 3, 2],
            'bps': [25, 15, 35, 20, 20, 5, 40, 30]
        })
    
    @pytest.fixture
    def engineer_with_temp_data(self, temp_data_dir, sample_players_data, 
                               sample_fixtures_data, sample_results_data):
        """Create FPLFeatureEngineer with temporary test data"""
        # Create raw data directory
        raw_dir = temp_data_dir / "raw"
        raw_dir.mkdir(parents=True)
        
        # Save sample data
        sample_players_data.to_csv(raw_dir / "players.csv", index=False)
        sample_fixtures_data.to_csv(raw_dir / "fixtures.csv", index=False)
        sample_results_data.to_csv(raw_dir / "results.csv", index=False)
        
        # Create engineer instance
        engineer = FPLFeatureEngineer()
        engineer.data_dir = temp_data_dir
        engineer.raw_dir = raw_dir
        engineer.features_dir = temp_data_dir / "features"
        engineer.features_dir.mkdir(exist_ok=True)
        
        return engineer
    
    def test_initialization(self):
        """Test FPLFeatureEngineer initialization"""
        engineer = FPLFeatureEngineer()
        
        assert engineer.data_dir == Path("data")
        assert engineer.raw_dir == Path("data/raw")
        assert engineer.features_dir == Path("data/features")
        assert engineer.rolling_windows == [3, 5]
    
    def test_load_raw_data_success(self, engineer_with_temp_data):
        """Test successful loading of raw data"""
        engineer = engineer_with_temp_data
        
        engineer.load_raw_data()
        
        assert hasattr(engineer, 'players_df')
        assert hasattr(engineer, 'fixtures_df')
        assert hasattr(engineer, 'results_df')
        assert len(engineer.players_df) == 4
        assert len(engineer.fixtures_df) == 4
        assert len(engineer.results_df) == 8
    
    def test_load_raw_data_file_not_found(self, temp_data_dir):
        """Test error handling when raw data files are missing"""
        engineer = FPLFeatureEngineer()
        engineer.raw_dir = temp_data_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            engineer.load_raw_data()
    
    def test_clean_and_normalize_data(self, engineer_with_temp_data):
        """Test data cleaning and normalization"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        
        # Add some problematic data to test cleaning
        engineer.results_df.loc[0, 'total_points'] = -5  # Negative points
        engineer.results_df.loc[1, 'minutes'] = None  # Missing minutes
        
        engineer.clean_and_normalize_data()
        
        # Check data cleaning
        assert (engineer.results_df['total_points'] >= 0).all()  # No negative points
        assert not engineer.results_df['minutes'].isna().any()  # No missing minutes
        
        # Check normalization
        assert 'player_id' in engineer.players_df.columns
        assert 'position' in engineer.players_df.columns
        assert 'price' in engineer.players_df.columns
        
        # Check position mapping
        expected_positions = ['GK', 'DEF', 'MID', 'FWD']
        assert engineer.players_df['position'].tolist() == expected_positions
    
    def test_create_rolling_features_lagged(self, engineer_with_temp_data):
        """Test creation of lagged rolling features (anti-leakage)"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        
        engineer.create_rolling_features()
        
        # Check that lagged features are created
        assert 'total_points_rolling_3_lag' in engineer.results_df.columns
        assert 'total_points_rolling_5_lag' in engineer.results_df.columns
        assert 'goals_scored_rolling_3_lag' in engineer.results_df.columns
        
        # Check that current features are also created
        assert 'total_points_rolling_3' in engineer.results_df.columns
        assert 'goals_scored_rolling_3' in engineer.results_df.columns
        
        # Verify lagged features exclude current gameweek
        # For gameweek 1, lagged features should be NaN
        gw1_data = engineer.results_df[engineer.results_df['gameweek'] == 1]
        assert gw1_data['total_points_rolling_3_lag'].isna().all()
        
        # For gameweek 2, lagged features should use only GW1 data
        gw2_data = engineer.results_df[engineer.results_df['gameweek'] == 2]
        player1_gw2 = gw2_data[gw2_data['player_id'] == 1].iloc[0]
        expected_lag = 10.0  # GW1 points for player 1
        assert player1_gw2['total_points_rolling_3_lag'] == expected_lag
    
    def test_create_fixture_difficulty_features(self, engineer_with_temp_data):
        """Test fixture difficulty feature creation"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        
        engineer.create_fixture_difficulty_features()
        
        # Check that difficulty features are created
        assert 'difficulty' in engineer.results_df.columns
        assert 'is_home' in engineer.results_df.columns
        assert 'difficulty_adjusted_points' in engineer.results_df.columns
        
        # Check difficulty values are reasonable (1-5 scale)
        assert engineer.results_df['difficulty'].between(1, 5).all()
        
        # Check home/away binary encoding
        assert engineer.results_df['is_home'].isin([0, 1]).all()
        
        # Check difficulty-adjusted points calculation
        assert (engineer.results_df['difficulty_adjusted_points'] >= 0).all()
    
    def test_create_minutes_likelihood_features(self, engineer_with_temp_data):
        """Test minutes likelihood feature creation"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        
        engineer.create_minutes_likelihood_features()
        
        # Check that minutes likelihood features are created
        assert 'minutes_likelihood_3' in engineer.results_df.columns
        assert 'minutes_likelihood_5' in engineer.results_df.columns
        assert 'avg_minutes_when_played_3' in engineer.results_df.columns
        assert 'avg_minutes_when_played_5' in engineer.results_df.columns
        
        # Check probability values are between 0 and 1
        assert engineer.results_df['minutes_likelihood_3'].between(0, 1).all()
        assert engineer.results_df['minutes_likelihood_5'].between(0, 1).all()
        
        # Check average minutes are reasonable (0-90)
        assert engineer.results_df['avg_minutes_when_played_3'].between(0, 90).all()
    
    def test_create_form_features(self, engineer_with_temp_data):
        """Test form-based feature creation"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        
        engineer.create_form_features()
        
        # Check that form features are created
        assert 'points_per_minute' in engineer.results_df.columns
        assert 'goal_involvement' in engineer.results_df.columns
        assert 'points_consistency_3' in engineer.results_df.columns
        assert 'points_consistency_5' in engineer.results_df.columns
        
        # Check points per minute calculation
        non_zero_minutes = engineer.results_df['minutes'] > 0
        expected_ppm = (engineer.results_df.loc[non_zero_minutes, 'total_points'] / 
                       engineer.results_df.loc[non_zero_minutes, 'minutes'])
        actual_ppm = engineer.results_df.loc[non_zero_minutes, 'points_per_minute']
        assert np.allclose(actual_ppm, expected_ppm)
        
        # Check goal involvement (goals + assists)
        expected_involvement = (engineer.results_df['goals_scored'] + 
                              engineer.results_df['assists'])
        assert (engineer.results_df['goal_involvement'] == expected_involvement).all()
    
    def test_finalize_features_dataset(self, engineer_with_temp_data):
        """Test finalization of features dataset"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        engineer.create_fixture_difficulty_features()
        engineer.create_minutes_likelihood_features()
        engineer.create_position_and_price_features()
        engineer.create_form_features()
        
        result_df = engineer.finalize_features_dataset()
        
        # Check essential columns are present
        essential_columns = ['player_id', 'gameweek', 'total_points', 'position']
        for col in essential_columns:
            assert col in result_df.columns
        
        # Check data types and no critical missing values
        assert not result_df[essential_columns].isna().any().any()
        assert len(result_df) > 0
        
        # Check sorting
        assert result_df['gameweek'].is_monotonic_increasing
    
    def test_validate_features_success(self, engineer_with_temp_data):
        """Test successful features validation"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        engineer.create_fixture_difficulty_features()
        engineer.create_minutes_likelihood_features()
        engineer.create_position_and_price_features()
        engineer.create_form_features()
        engineer.finalize_features_dataset()
        
        validation_result = engineer.validate_features()
        
        assert validation_result is True
        assert hasattr(engineer, 'features_df')
        assert len(engineer.features_df) > 0
    
    def test_save_features(self, engineer_with_temp_data):
        """Test saving features to CSV"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        engineer.create_fixture_difficulty_features()
        engineer.create_minutes_likelihood_features()
        engineer.create_position_and_price_features()
        engineer.create_form_features()
        engineer.finalize_features_dataset()
        
        output_path = engineer.save_features()
        
        # Check file was created
        assert output_path.exists()
        
        # Check file contents
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(engineer.features_df)
        assert list(saved_df.columns) == list(engineer.features_df.columns)
    
    def test_full_pipeline_integration(self, engineer_with_temp_data):
        """Test the complete feature engineering pipeline"""
        engineer = engineer_with_temp_data
        
        output_path = engineer.run_feature_engineering()
        
        # Check pipeline completed successfully
        assert output_path.exists()
        
        # Load and validate output
        features_df = pd.read_csv(output_path)
        
        # Check essential structure
        assert len(features_df) > 0
        assert 'player_id' in features_df.columns
        assert 'gameweek' in features_df.columns
        assert 'total_points' in features_df.columns
        
        # Check lagged features are present (key anti-leakage requirement)
        lagged_features = [col for col in features_df.columns if '_lag' in col]
        assert len(lagged_features) > 0
        
        # Check feature diversity
        assert len(features_df.columns) >= 15  # Should have many engineered features
    
    def test_error_handling_empty_data(self, temp_data_dir):
        """Test error handling with empty data files"""
        raw_dir = temp_data_dir / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create empty CSV files
        pd.DataFrame().to_csv(raw_dir / "players.csv", index=False)
        pd.DataFrame().to_csv(raw_dir / "fixtures.csv", index=False)
        pd.DataFrame().to_csv(raw_dir / "results.csv", index=False)
        
        engineer = FPLFeatureEngineer()
        engineer.raw_dir = raw_dir
        engineer.features_dir = temp_data_dir / "features"
        engineer.features_dir.mkdir(exist_ok=True)
        
        with pytest.raises(Exception):  # Should fail gracefully
            engineer.run_feature_engineering()
    
    def test_data_leakage_prevention(self, engineer_with_temp_data):
        """Test that lagged features prevent data leakage"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        
        # For any given gameweek, lagged features should only use data from previous gameweeks
        for gw in engineer.results_df['gameweek'].unique():
            gw_data = engineer.results_df[engineer.results_df['gameweek'] == gw]
            
            if gw == 1:
                # First gameweek should have NaN lagged features
                assert gw_data['total_points_rolling_3_lag'].isna().all()
            else:
                # Later gameweeks should have lagged features that don't include current GW
                for player_id in gw_data['player_id'].unique():
                    player_current = gw_data[gw_data['player_id'] == player_id].iloc[0]
                    player_history = engineer.results_df[
                        (engineer.results_df['player_id'] == player_id) & 
                        (engineer.results_df['gameweek'] < gw)
                    ]
                    
                    if len(player_history) > 0:
                        expected_lag = player_history['total_points'].tail(3).mean()
                        actual_lag = player_current['total_points_rolling_3_lag']
                        
                        if not pd.isna(expected_lag) and not pd.isna(actual_lag):
                            assert abs(expected_lag - actual_lag) < 0.01
    
    def test_missing_data_handling(self, engineer_with_temp_data):
        """Test handling of missing and invalid data"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        
        # Introduce various data quality issues
        engineer.results_df.loc[0, 'total_points'] = -10  # Negative points
        engineer.results_df.loc[1, 'minutes'] = None  # Missing minutes
        engineer.results_df.loc[2, 'goals_scored'] = -1  # Negative goals
        engineer.results_df.loc[3, 'total_points'] = 1000  # Unrealistic high points
        
        engineer.clean_and_normalize_data()
        
        # Check data cleaning worked
        assert (engineer.results_df['total_points'] >= 0).all()
        assert not engineer.results_df['minutes'].isna().any()
        assert (engineer.results_df['goals_scored'] >= 0).all()
        assert (engineer.results_df['total_points'] <= 50).all()  # Reasonable max
    
    def test_insufficient_data_scenarios(self, temp_data_dir):
        """Test behavior with insufficient data for rolling features"""
        # Create minimal data
        minimal_players = pd.DataFrame({
            'id': [1, 2], 'web_name': ['P1', 'P2'], 'element_type': [1, 2],
            'team': [1, 1], 'now_cost': [50, 60], 'total_points': [10, 15]
        })
        minimal_fixtures = pd.DataFrame({
            'id': [1], 'event': [1], 'team_h': [1], 'team_a': [2],
            'team_h_difficulty': [3], 'team_a_difficulty': [4],
            'kickoff_time': ['2024-08-17T14:00:00Z']
        })
        minimal_results = pd.DataFrame({
            'player_id': [1, 2], 'gameweek': [1, 1],
            'total_points': [5, 8], 'minutes': [90, 60],
            'goals_scored': [0, 1], 'assists': [0, 0],
            'clean_sheets': [0, 0], 'bonus': [0, 2], 'bps': [20, 35]
        })
        
        # Save minimal data
        raw_dir = temp_data_dir / "raw"
        raw_dir.mkdir(parents=True)
        minimal_players.to_csv(raw_dir / "players.csv", index=False)
        minimal_fixtures.to_csv(raw_dir / "fixtures.csv", index=False)
        minimal_results.to_csv(raw_dir / "results.csv", index=False)
        
        # Create engineer and run
        engineer = FPLFeatureEngineer()
        engineer.data_dir = temp_data_dir
        engineer.raw_dir = raw_dir
        engineer.features_dir = temp_data_dir / "features"
        engineer.features_dir.mkdir(exist_ok=True)
        
        # Should handle insufficient data gracefully
        try:
            output_path = engineer.run_feature_engineering()
            assert output_path.exists()
            
            # Load and check results
            df = pd.read_csv(output_path)
            assert len(df) >= 2  # At least the original data
            
        except Exception as e:
            # Should fail gracefully with informative error
            assert "insufficient" in str(e).lower() or "minimum" in str(e).lower()
    
    def test_multiple_gameweeks_rolling_features(self, engineer_with_temp_data):
        """Test rolling features with multiple gameweeks"""
        engineer = engineer_with_temp_data
        
        # Add more gameweeks of data
        additional_results = pd.DataFrame({
            'player_id': [1, 2, 3, 4] * 3,  # 3 more gameweeks
            'gameweek': [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5],
            'total_points': [12, 8, 6, 9, 15, 2, 14, 11, 8, 6, 10, 13],
            'minutes': [90, 90, 80, 70, 90, 20, 90, 85, 90, 90, 75, 90],
            'goals_scored': [1, 0, 0, 1, 2, 0, 1, 1, 0, 0, 1, 1],
            'assists': [0, 1, 1, 0, 1, 0, 2, 0, 1, 0, 0, 2],
            'clean_sheets': [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
            'bonus': [3, 1, 0, 2, 3, 0, 3, 1, 1, 0, 2, 3],
            'bps': [40, 25, 20, 35, 45, 10, 40, 30, 25, 20, 35, 45]
        })
        
        engineer.load_raw_data()
        engineer.results_df = pd.concat([engineer.results_df, additional_results], ignore_index=True)
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        
        # Test 3-gameweek rolling average for player 1 at GW 5
        player1_gw5 = engineer.results_df[
            (engineer.results_df['player_id'] == 1) & 
            (engineer.results_df['gameweek'] == 5)
        ].iloc[0]
        
        # Should average GW 2, 3, 4 (excluding current GW 5)
        expected_3gw_lag = (8 + 12 + 15) / 3  # GW 2, 3, 4 points
        actual_3gw_lag = player1_gw5['total_points_rolling_3_lag']
        
        assert abs(expected_3gw_lag - actual_3gw_lag) < 0.01
        
        # Test 5-gameweek rolling average
        expected_5gw_lag = (10 + 8 + 12 + 15) / 4  # GW 1, 2, 3, 4 (only 4 available)
        actual_5gw_lag = player1_gw5['total_points_rolling_5_lag']
        
        assert abs(expected_5gw_lag - actual_5gw_lag) < 0.01
    
    def test_fixture_difficulty_edge_cases(self, engineer_with_temp_data):
        """Test fixture difficulty handling with edge cases"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        
        # Add some edge case fixture data
        engineer.fixtures_df.loc[len(engineer.fixtures_df)] = {
            'id': 5, 'event': 2, 'team_h': 1, 'team_a': 3,
            'team_h_difficulty': None, 'team_a_difficulty': 3,  # Missing home difficulty
            'kickoff_time': '2024-08-24T14:00:00Z'
        }
        
        engineer.clean_and_normalize_data()
        engineer.create_fixture_difficulty_features()
        
        # Should handle missing difficulty gracefully
        assert not engineer.results_df['difficulty'].isna().any()
        assert engineer.results_df['difficulty'].between(1, 5).all()
    
    def test_rolling_feature_edge_cases(self, engineer_with_temp_data):
        """Test rolling features with edge cases"""
        engineer = engineer_with_temp_data
        engineer.load_raw_data()
        
        # Create single gameweek data (edge case)
        engineer.results_df = engineer.results_df[engineer.results_df['gameweek'] == 1]
        
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        
        # All lagged features should be NaN for first gameweek
        assert engineer.results_df['total_points_rolling_3_lag'].isna().all()
        
        # Current rolling features should equal actual values
        assert (engineer.results_df['total_points_rolling_3'] == 
               engineer.results_df['total_points']).all()
    
    def test_feature_correlation_sanity_check(self, engineer_with_temp_data):
        """Test that engineered features have reasonable correlations"""
        engineer = engineer_with_temp_data
        
        # Add more data for better correlation analysis
        additional_results = pd.DataFrame({
            'player_id': [1, 2, 3, 4] * 3,
            'gameweek': [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5],
            'total_points': [12, 8, 6, 9, 15, 2, 14, 11, 8, 6, 10, 13],
            'minutes': [90, 90, 80, 70, 90, 20, 90, 85, 90, 90, 75, 90],
            'goals_scored': [1, 0, 0, 1, 2, 0, 1, 1, 0, 0, 1, 1],
            'assists': [0, 1, 1, 0, 1, 0, 2, 0, 1, 0, 0, 2],
            'clean_sheets': [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
            'bonus': [3, 1, 0, 2, 3, 0, 3, 1, 1, 0, 2, 3],
            'bps': [40, 25, 20, 35, 45, 10, 40, 30, 25, 20, 35, 45]
        })
        
        engineer.load_raw_data()
        engineer.results_df = pd.concat([engineer.results_df, additional_results], ignore_index=True)
        engineer.clean_and_normalize_data()
        engineer.create_rolling_features()
        engineer.create_fixture_difficulty_features()
        engineer.create_minutes_likelihood_features()
        engineer.create_position_and_price_features()
        engineer.create_form_features()
        
        final_df = engineer.finalize_features_dataset()
        
        # Test reasonable correlations
        # Goals and total points should be positively correlated
        goals_points_corr = final_df['goals_scored'].corr(final_df['total_points'])
        assert goals_points_corr > 0.1  # Should be positive
        
        # Minutes and total points should be positively correlated
        minutes_points_corr = final_df['minutes'].corr(final_df['total_points'])
        assert minutes_points_corr > 0.1  # Should be positive
        
        # Rolling features should correlate with current performance
        if 'total_points_rolling_3_lag' in final_df.columns:
            rolling_corr = final_df['total_points_rolling_3_lag'].corr(final_df['total_points'])
            # Should have some positive correlation but not too high (would indicate leakage)
            assert 0.1 < rolling_corr < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])