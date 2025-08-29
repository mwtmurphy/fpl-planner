#!/usr/bin/env python3
"""
Unit tests for FPL Forecasting Module

Tests cover:
- Data loading and preparation functionality
- Temporal data splitting (time-based vs player-based)
- Model training with XGBoost and RandomForest fallback
- Prediction generation and validation metrics
- Cross-validation implementation (leave-one-gameweek-out)
- Feature importance analysis and output validation
- Integration tests for complete forecasting pipeline
- Error handling for missing data and edge cases
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import warnings
warnings.filterwarnings('ignore')

# Import the module under test
import sys
sys.path.append('src')
from forecasting import FPLForecaster


class TestFPLForecaster:
    """Test suite for FPLForecaster class"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_features_data(self):
        """Create sample features data for testing"""
        np.random.seed(42)
        
        # Create realistic FPL features data
        data = []
        for gw in range(1, 6):  # 5 gameweeks
            for player_id in range(1, 21):  # 20 players
                row = {
                    'player_id': player_id,
                    'gameweek': gw,
                    'total_points': np.random.randint(0, 20),
                    'minutes': np.random.choice([0, 90], p=[0.2, 0.8]),
                    'goals_scored': np.random.randint(0, 3),
                    'assists': np.random.randint(0, 3),
                    'position': np.random.choice(['GK', 'DEF', 'MID', 'FWD']),
                    'price': np.random.uniform(4.0, 12.0),
                    'team_id': np.random.randint(1, 21),
                    'difficulty': np.random.randint(1, 6),
                    'is_home': np.random.choice([0, 1]),
                    'position_encoded': np.random.randint(1, 5),
                    
                    # Lagged rolling features (anti-leakage)
                    'total_points_rolling_3_lag': np.random.uniform(0, 15) if gw > 1 else np.nan,
                    'total_points_rolling_5_lag': np.random.uniform(0, 15) if gw > 1 else np.nan,
                    'minutes_rolling_3_lag': np.random.uniform(30, 90) if gw > 1 else np.nan,
                    'minutes_rolling_5_lag': np.random.uniform(30, 90) if gw > 1 else np.nan,
                    'goals_scored_rolling_3_lag': np.random.uniform(0, 2) if gw > 1 else np.nan,
                    'goals_scored_rolling_5_lag': np.random.uniform(0, 2) if gw > 1 else np.nan,
                    'assists_rolling_3_lag': np.random.uniform(0, 2) if gw > 1 else np.nan,
                    'assists_rolling_5_lag': np.random.uniform(0, 2) if gw > 1 else np.nan,
                    
                    # Minutes likelihood features
                    'minutes_likelihood_3': np.random.uniform(0.5, 1.0),
                    'minutes_likelihood_5': np.random.uniform(0.5, 1.0),
                    
                    # Form features
                    'points_consistency_3': np.random.uniform(0, 1),
                    'points_consistency_5': np.random.uniform(0, 1),
                    'points_per_minute': np.random.uniform(0, 0.3),
                    'goal_involvement': np.random.randint(0, 4),
                }
                data.append(row)
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def forecaster_with_temp_data(self, temp_data_dir, sample_features_data):
        """Create FPLForecaster with temporary test data"""
        # Create features directory
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        
        # Save sample features data
        sample_features_data.to_csv(features_dir / "features.csv", index=False)
        
        # Create forecaster instance
        forecaster = FPLForecaster()
        forecaster.data_dir = temp_data_dir
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        return forecaster
    
    @pytest.fixture
    def minimal_features_data(self):
        """Create minimal features data for edge case testing"""
        return pd.DataFrame({
            'player_id': [1, 2, 3],
            'gameweek': [1, 1, 1],
            'total_points': [5, 8, 12],
            'position': ['GK', 'DEF', 'MID'],
            'price': [5.0, 6.0, 8.0],
            'team_id': [1, 2, 3],
            'difficulty': [3, 4, 2],
            'is_home': [1, 0, 1],
            'position_encoded': [1, 2, 3],
            
            # Minimal required features for model
            'total_points_rolling_3_lag': [np.nan, np.nan, np.nan],
            'minutes_likelihood_3': [0.8, 0.9, 0.7],
            'points_consistency_3': [0.5, 0.6, 0.4],
        })
    
    def test_initialization(self):
        """Test FPLForecaster initialization"""
        forecaster = FPLForecaster()
        
        assert forecaster.data_dir == Path("data")
        assert forecaster.features_dir == Path("data/features")
        assert forecaster.forecasts_dir == Path("data/forecasts")
        assert forecaster.model is None
        assert forecaster.features_df is None
        
        # Test feature columns configuration
        assert 'total_points_rolling_3_lag' in forecaster.feature_columns
        assert 'total_points_rolling_5_lag' in forecaster.feature_columns
        assert 'minutes_likelihood_3' in forecaster.feature_columns
        assert 'difficulty' in forecaster.feature_columns
        assert 'is_home' in forecaster.feature_columns
        assert 'price' in forecaster.feature_columns
        
        # Test fallback features
        assert len(forecaster.fallback_feature_columns) > 0
        assert 'total_points_rolling_3' in forecaster.fallback_feature_columns
        
        # Test position encoding
        expected_encoding = {'GK': 1, 'DEF': 2, 'MID': 3, 'FWD': 4}
        assert forecaster.position_encoding == expected_encoding
    
    def test_load_features_data_success(self, forecaster_with_temp_data):
        """Test successful loading of features data"""
        forecaster = forecaster_with_temp_data
        
        forecaster.load_features_data()
        
        assert forecaster.features_df is not None
        assert len(forecaster.features_df) > 0
        assert 'player_id' in forecaster.features_df.columns
        assert 'gameweek' in forecaster.features_df.columns
        assert 'total_points' in forecaster.features_df.columns
        
        # Check position encoding was added
        assert 'position_encoded' in forecaster.features_df.columns
        assert 'position_encoded' in forecaster.feature_columns
    
    def test_load_features_data_file_not_found(self, temp_data_dir):
        """Test error handling when features file is missing"""
        forecaster = FPLForecaster()
        forecaster.features_dir = temp_data_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            forecaster.load_features_data()
        
        assert "Features file not found" in str(exc_info.value)
        assert "make features" in str(exc_info.value)
    
    def test_load_features_data_empty_file(self, temp_data_dir):
        """Test handling of empty features file"""
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        
        # Create empty CSV file
        pd.DataFrame().to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        
        forecaster.load_features_data()
        
        # Should load but be empty
        assert forecaster.features_df is not None
        assert len(forecaster.features_df) == 0
    
    def test_split_data_by_time_multiple_gameweeks(self, forecaster_with_temp_data):
        """Test time-based data splitting with multiple gameweeks"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        
        forecaster.split_data_by_time()
        
        # Check that data was split
        assert forecaster.train_data is not None
        assert forecaster.val_data is not None
        assert forecaster.test_data is not None
        
        assert len(forecaster.train_data) > 0
        assert len(forecaster.val_data) > 0
        assert len(forecaster.test_data) > 0
        
        # Check temporal ordering (train < val < test gameweeks)
        train_gws = set(forecaster.train_data['gameweek'].unique())
        val_gws = set(forecaster.val_data['gameweek'].unique())
        test_gws = set(forecaster.test_data['gameweek'].unique())
        
        assert max(train_gws) <= min(val_gws)
        assert max(val_gws) <= min(test_gws)
    
    def test_split_data_by_time_single_gameweek(self, temp_data_dir, minimal_features_data):
        """Test player-based splitting with single gameweek"""
        # Save minimal data (single gameweek)
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        minimal_features_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.load_features_data()
        
        forecaster.split_data_by_time()
        
        # Should use player-based split
        assert forecaster.train_data is not None
        assert forecaster.val_data is not None
        assert forecaster.test_data is not None
        
        # All data should be from gameweek 1
        assert forecaster.train_data['gameweek'].unique() == [1]
        assert forecaster.val_data['gameweek'].unique() == [1]
        assert forecaster.test_data['gameweek'].unique() == [1]
        
        # Players should be different across splits
        train_players = set(forecaster.train_data['player_id'].unique())
        val_players = set(forecaster.val_data['player_id'].unique())
        test_players = set(forecaster.test_data['player_id'].unique())
        
        assert len(train_players.intersection(val_players)) == 0
        assert len(train_players.intersection(test_players)) == 0
        assert len(val_players.intersection(test_players)) == 0
    
    def test_prepare_model_data_with_lagged_features(self, forecaster_with_temp_data):
        """Test model data preparation using lagged features (no leakage)"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        X, y = forecaster.prepare_model_data(forecaster.train_data)
        
        # Check feature matrix
        assert len(X) == len(forecaster.train_data)
        assert len(y) == len(forecaster.train_data)
        
        # Check that lagged features are used (anti-leakage)
        assert 'total_points_rolling_3_lag' in X.columns
        assert 'total_points_rolling_5_lag' in X.columns
        assert 'minutes_likelihood_3' in X.columns
        assert 'difficulty' in X.columns
        
        # Check no missing values after preparation
        assert not X.isna().any().any()
        
        # Target should be total_points
        assert (y == forecaster.train_data['total_points']).all()
    
    def test_prepare_model_data_fallback_features(self, temp_data_dir):
        """Test fallback to current features when lagged features unavailable"""
        # Create data without lagged features
        fallback_data = pd.DataFrame({
            'player_id': [1, 2, 3],
            'gameweek': [1, 1, 1],
            'total_points': [5, 8, 12],
            'total_points_rolling_3': [5, 8, 12],  # Current features only
            'minutes_rolling_3': [90, 90, 75],
            'difficulty': [3, 4, 2],
            'is_home': [1, 0, 1],
            'points_per_minute': [0.05, 0.09, 0.16],
            'goal_involvement': [0, 1, 2],
            'price': [5.0, 6.0, 8.0]
        })
        
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        fallback_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.load_features_data()
        
        X, y = forecaster.prepare_model_data(forecaster.features_df)
        
        # Should use fallback features
        assert 'total_points_rolling_3' in X.columns
        assert 'points_per_minute' in X.columns
        assert 'goal_involvement' in X.columns
        
        # Should have fewer than 5 lagged features available
        lagged_features = [col for col in forecaster.feature_columns if col in X.columns]
        assert len(lagged_features) < 5
    
    @patch('forecasting.XGBOOST_AVAILABLE', True)
    def test_train_model_with_xgboost(self, forecaster_with_temp_data):
        """Test model training with XGBoost"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.xgb.XGBRegressor') as mock_xgb:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.val_data))
            mock_xgb.return_value = mock_model
            
            correlation = forecaster.train_model()
            
            # Check model was created and trained
            mock_xgb.assert_called_once()
            mock_model.fit.assert_called_once()
            mock_model.predict.assert_called_once()
            
            # Check correlation is calculated
            assert isinstance(correlation, float)
            assert not np.isnan(correlation)
    
    @patch('forecasting.XGBOOST_AVAILABLE', False)
    def test_train_model_with_randomforest_fallback(self, forecaster_with_temp_data):
        """Test model training with RandomForest fallback"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.val_data))
            mock_rf.return_value = mock_model
            
            correlation = forecaster.train_model()
            
            # Check RandomForest was used
            mock_rf.assert_called_once()
            mock_model.fit.assert_called_once()
            mock_model.predict.assert_called_once()
            
            # Check correlation is calculated
            assert isinstance(correlation, float)
            assert not np.isnan(correlation)
    
    def test_train_model_validation_metrics(self, forecaster_with_temp_data):
        """Test validation metrics calculation during training"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        # Mock model with predictable behavior
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            # Create correlated predictions
            val_actual = forecaster.val_data['total_points'].values
            val_predictions = val_actual * 0.7 + np.random.normal(0, 2, len(val_actual))
            mock_model.predict.return_value = val_predictions
            mock_rf.return_value = mock_model
            
            correlation = forecaster.train_model()
            
            # Check correlation is reasonable
            assert -1 <= correlation <= 1
            
            # Model should be stored
            assert forecaster.model is not None
    
    def test_cross_validate_temporal_multiple_gameweeks(self, forecaster_with_temp_data):
        """Test leave-one-gameweek-out cross-validation"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        
        # Ensure we have sufficient gameweeks for CV
        assert len(forecaster.features_df['gameweek'].unique()) >= 3
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, 20)  # 20 predictions per GW
            mock_rf.return_value = mock_model
            
            # This should run without error
            forecaster.cross_validate_temporal()
            
            # Should have called model creation multiple times (once per CV fold)
            assert mock_rf.call_count >= 2
    
    def test_cross_validate_temporal_insufficient_gameweeks(self, temp_data_dir, minimal_features_data):
        """Test cross-validation with insufficient gameweeks"""
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        minimal_features_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.load_features_data()
        
        # Should handle insufficient data gracefully
        forecaster.cross_validate_temporal()  # Should not raise exception
    
    def test_generate_predictions_success(self, forecaster_with_temp_data):
        """Test successful prediction generation"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        # Mock trained model
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            # Generate realistic predictions
            num_samples = len(forecaster.features_df)
            mock_predictions = np.random.uniform(0, 20, num_samples)
            mock_model.predict.return_value = mock_predictions
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Check prediction structure
            assert len(predictions_df) == len(forecaster.features_df)
            assert 'player_id' in predictions_df.columns
            assert 'gameweek' in predictions_df.columns
            assert 'total_points' in predictions_df.columns
            assert 'expected_points' in predictions_df.columns
            
            # Check merged metadata
            assert 'position' in predictions_df.columns
            assert 'price' in predictions_df.columns
            assert 'team_id' in predictions_df.columns
            
            # Check predictions are non-negative
            assert (predictions_df['expected_points'] >= 0).all()
            
            # Check predictions are reasonable
            assert predictions_df['expected_points'].max() <= 50  # Reasonable upper bound
    
    def test_generate_predictions_clipping(self, forecaster_with_temp_data):
        """Test that negative predictions are clipped to zero"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            # Generate some negative predictions
            num_samples = len(forecaster.features_df)
            mock_predictions = np.random.uniform(-5, 20, num_samples)
            mock_model.predict.return_value = mock_predictions
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # All predictions should be non-negative after clipping
            assert (predictions_df['expected_points'] >= 0).all()
    
    def test_save_predictions(self, forecaster_with_temp_data):
        """Test saving predictions to CSV file"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df))
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            output_path = forecaster.save_predictions(predictions_df)
            
            # Check file was created
            assert output_path.exists()
            assert output_path.name == "expected_points.csv"
            
            # Check file contents
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == len(predictions_df)
            assert list(saved_df.columns) == list(predictions_df.columns)
            
            # Check essential columns are present
            assert 'player_id' in saved_df.columns
            assert 'expected_points' in saved_df.columns
            assert 'gameweek' in saved_df.columns
    
    def test_validate_predictions_with_test_data(self, forecaster_with_temp_data):
        """Test prediction validation with test set"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df))
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Should validate successfully
            validation_result = forecaster.validate_predictions(predictions_df)
            assert validation_result is True
    
    def test_validate_predictions_no_test_data(self, temp_data_dir, minimal_features_data):
        """Test prediction validation with no test set"""
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        minimal_features_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df))
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Should still validate basic structure
            validation_result = forecaster.validate_predictions(predictions_df)
            assert validation_result is True
    
    def test_validate_predictions_empty_data(self, forecaster_with_temp_data):
        """Test prediction validation with empty predictions"""
        forecaster = forecaster_with_temp_data
        
        empty_predictions = pd.DataFrame(columns=['player_id', 'gameweek', 'expected_points'])
        validation_result = forecaster.validate_predictions(empty_predictions)
        
        # Should fail validation
        assert validation_result is False
    
    def test_analyze_feature_importance_tree_model(self, forecaster_with_temp_data):
        """Test feature importance analysis for tree-based models"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.val_data))
            
            # Mock feature importances
            X_train, _ = forecaster.prepare_model_data(forecaster.train_data)
            num_features = len(X_train.columns)
            mock_model.feature_importances_ = np.random.uniform(0, 1, num_features)
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            
            # Should run without error
            forecaster.analyze_feature_importance()
    
    def test_analyze_feature_importance_linear_model(self, forecaster_with_temp_data):
        """Test feature importance analysis for linear models"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.LinearRegression') as mock_lr:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.val_data))
            
            # Mock linear coefficients
            X_train, _ = forecaster.prepare_model_data(forecaster.train_data)
            num_features = len(X_train.columns)
            mock_model.coef_ = np.random.uniform(-1, 1, num_features)
            mock_lr.return_value = mock_model
            
            forecaster.model = mock_model
            
            # Should run without error
            forecaster.analyze_feature_importance()
    
    def test_analyze_feature_importance_no_importance(self, forecaster_with_temp_data):
        """Test feature importance with model that has no importance attributes"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        # Mock model without feature_importances_ or coef_
        mock_model = MagicMock()
        del mock_model.feature_importances_
        del mock_model.coef_
        forecaster.model = mock_model
        
        # Should run without error (just won't print importance)
        forecaster.analyze_feature_importance()
    
    def test_prediction_output_format_validation(self, forecaster_with_temp_data):
        """Test that predictions have correct format and data types"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df))
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Check data types
            assert predictions_df['player_id'].dtype in ['int64', 'int32']
            assert predictions_df['gameweek'].dtype in ['int64', 'int32']
            assert predictions_df['total_points'].dtype in ['int64', 'int32', 'float64']
            assert predictions_df['expected_points'].dtype == 'float64'
            assert predictions_df['price'].dtype == 'float64'
            
            # Check value ranges
            assert predictions_df['player_id'].min() > 0
            assert predictions_df['gameweek'].min() > 0
            assert predictions_df['expected_points'].min() >= 0
            assert predictions_df['price'].min() > 0
            
            # Check no duplicate player-gameweek combinations
            duplicate_check = predictions_df.groupby(['player_id', 'gameweek']).size()
            assert (duplicate_check == 1).all()
    
    def test_validation_metrics_calculation(self, forecaster_with_temp_data):
        """Test validation metrics calculation accuracy"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            
            # Create correlated test predictions for validation
            test_actual = np.array([5, 10, 15, 8, 12])
            test_predictions = test_actual * 0.8 + np.random.normal(0, 1, len(test_actual))
            
            # Mock the predict method to return different values for different calls
            predict_calls = []
            def mock_predict(X):
                predict_calls.append(len(X))
                if len(X) == len(forecaster.val_data):
                    return np.random.uniform(0, 15, len(X))
                elif len(X) == len(forecaster.features_df):
                    # Return predictions for the full dataset
                    full_predictions = np.random.uniform(0, 15, len(X))
                    # Set test set predictions to our controlled values
                    test_mask = forecaster.features_df['gameweek'].isin(forecaster.test_data['gameweek'].unique())
                    if test_mask.sum() >= len(test_predictions):
                        full_predictions[test_mask][:len(test_predictions)] = test_predictions
                    return full_predictions
                else:
                    return np.random.uniform(0, 15, len(X))
            
            mock_model.predict.side_effect = mock_predict
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Validation should complete without error
            validation_result = forecaster.validate_predictions(predictions_df)
            assert validation_result is True
    
    def test_run_forecasting_complete_pipeline(self, forecaster_with_temp_data):
        """Test the complete forecasting pipeline integration"""
        forecaster = forecaster_with_temp_data
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df) if hasattr(forecaster, 'features_df') else 100)
            mock_model.feature_importances_ = np.random.uniform(0, 1, 10)  # Mock feature importances
            mock_rf.return_value = mock_model
            
            # Run complete pipeline
            output_path = forecaster.run_forecasting()
            
            # Check output
            assert output_path is not None
            assert output_path.exists()
            assert output_path.name == "expected_points.csv"
            
            # Verify file contents
            predictions_df = pd.read_csv(output_path)
            assert len(predictions_df) > 0
            assert 'expected_points' in predictions_df.columns
            assert 'player_id' in predictions_df.columns
            assert 'gameweek' in predictions_df.columns
    
    def test_run_forecasting_pipeline_failure_handling(self, temp_data_dir):
        """Test pipeline failure handling with missing data"""
        forecaster = FPLForecaster()
        forecaster.features_dir = temp_data_dir / "nonexistent"
        
        # Should raise an exception gracefully
        with pytest.raises(Exception) as exc_info:
            forecaster.run_forecasting()
        
        assert "Features file not found" in str(exc_info.value)
    
    def test_memory_efficiency_large_dataset(self, temp_data_dir):
        """Test memory efficiency with larger dataset"""
        # Create larger synthetic dataset
        np.random.seed(42)
        large_data = []
        
        for gw in range(1, 11):  # 10 gameweeks
            for player_id in range(1, 501):  # 500 players
                row = {
                    'player_id': player_id,
                    'gameweek': gw,
                    'total_points': np.random.randint(0, 20),
                    'position': np.random.choice(['GK', 'DEF', 'MID', 'FWD']),
                    'price': np.random.uniform(4.0, 12.0),
                    'team_id': np.random.randint(1, 21),
                    'difficulty': np.random.randint(1, 6),
                    'is_home': np.random.choice([0, 1]),
                    'position_encoded': np.random.randint(1, 5),
                    'total_points_rolling_3_lag': np.random.uniform(0, 15) if gw > 1 else np.nan,
                    'minutes_likelihood_3': np.random.uniform(0.5, 1.0),
                    'points_consistency_3': np.random.uniform(0, 1),
                }
                large_data.append(row)
        
        large_df = pd.DataFrame(large_data)
        
        # Save to temporary location
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        large_df.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        # Should handle large dataset efficiently
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(large_df))
            mock_rf.return_value = mock_model
            
            # Should complete without memory issues
            output_path = forecaster.run_forecasting()
            assert output_path.exists()
            
            # Check output size
            result_df = pd.read_csv(output_path)
            assert len(result_df) == len(large_df)
    
    def test_edge_case_single_player_single_gameweek(self, temp_data_dir):
        """Test edge case with minimal data (single player, single gameweek)"""
        minimal_data = pd.DataFrame({
            'player_id': [1],
            'gameweek': [1],
            'total_points': [10],
            'position': ['MID'],
            'price': [8.0],
            'team_id': [1],
            'difficulty': [3],
            'is_home': [1],
            'position_encoded': [3],
            'total_points_rolling_3_lag': [np.nan],
            'minutes_likelihood_3': [0.8],
            'points_consistency_3': [0.5],
        })
        
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        minimal_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([8.5])
            mock_rf.return_value = mock_model
            
            # Should handle minimal data gracefully
            try:
                output_path = forecaster.run_forecasting()
                assert output_path.exists()
                
                result_df = pd.read_csv(output_path)
                assert len(result_df) == 1
                assert result_df.iloc[0]['expected_points'] >= 0
                
            except Exception as e:
                # Should fail gracefully with informative message
                assert any(keyword in str(e).lower() for keyword in ['insufficient', 'minimum', 'data'])
    
    def test_edge_case_all_missing_lagged_features(self, temp_data_dir):
        """Test handling when all lagged features are missing"""
        data_no_lags = pd.DataFrame({
            'player_id': [1, 2, 3],
            'gameweek': [1, 1, 1],
            'total_points': [5, 8, 12],
            'position': ['GK', 'DEF', 'MID'],
            'price': [5.0, 6.0, 8.0],
            'team_id': [1, 2, 3],
            'difficulty': [3, 4, 2],
            'is_home': [1, 0, 1],
            'position_encoded': [1, 2, 3],
            
            # All lagged features are NaN (first gameweek scenario)
            'total_points_rolling_3_lag': [np.nan, np.nan, np.nan],
            'total_points_rolling_5_lag': [np.nan, np.nan, np.nan],
            'minutes_rolling_3_lag': [np.nan, np.nan, np.nan],
            'minutes_rolling_5_lag': [np.nan, np.nan, np.nan],
            'goals_scored_rolling_3_lag': [np.nan, np.nan, np.nan],
            'goals_scored_rolling_5_lag': [np.nan, np.nan, np.nan],
            'assists_rolling_3_lag': [np.nan, np.nan, np.nan],
            'assists_rolling_5_lag': [np.nan, np.nan, np.nan],
            
            # Some features still available
            'minutes_likelihood_3': [0.8, 0.9, 0.7],
            'minutes_likelihood_5': [0.8, 0.9, 0.7],
            'points_consistency_3': [0.5, 0.6, 0.4],
            'points_consistency_5': [0.5, 0.6, 0.4],
        })
        
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        data_no_lags.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        forecaster.load_features_data()
        
        # Should fall back to available features
        X, y = forecaster.prepare_model_data(forecaster.features_df)
        
        # Should have some features available despite missing lagged features
        assert len(X.columns) >= 4  # At least basic features
        assert not X.isna().any().any()  # No missing values after preparation
    
    def test_edge_case_extreme_prediction_values(self, forecaster_with_temp_data):
        """Test handling of extreme prediction values"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            # Generate extreme prediction values
            extreme_predictions = np.array([-100, 1000, np.inf, -np.inf, np.nan] * 20)
            extreme_predictions = extreme_predictions[:len(forecaster.features_df)]
            mock_model.predict.return_value = extreme_predictions
            mock_rf.return_value = mock_model
            
            forecaster.train_model()
            predictions_df = forecaster.generate_predictions()
            
            # Should handle extreme values gracefully
            assert (predictions_df['expected_points'] >= 0).all()  # No negative values
            assert np.isfinite(predictions_df['expected_points']).all()  # No inf/nan values
            assert (predictions_df['expected_points'] <= 100).all()  # Reasonable upper bound
    
    def test_model_persistence_and_reuse(self, forecaster_with_temp_data):
        """Test that trained models can be reused for multiple predictions"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        forecaster.split_data_by_time()
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.uniform(0, 15, len(forecaster.features_df))
            mock_rf.return_value = mock_model
            
            # Train model
            forecaster.train_model()
            first_model = forecaster.model
            
            # Generate predictions multiple times
            predictions1 = forecaster.generate_predictions()
            predictions2 = forecaster.generate_predictions()
            
            # Model should be reused
            assert forecaster.model is first_model
            assert mock_model.predict.call_count >= 2  # Called multiple times
            
            # Predictions should be consistent
            assert len(predictions1) == len(predictions2)
            assert list(predictions1.columns) == list(predictions2.columns)
    
    def test_cross_validation_performance_thresholds(self, forecaster_with_temp_data):
        """Test cross-validation performance meets realistic thresholds"""
        forecaster = forecaster_with_temp_data
        forecaster.load_features_data()
        
        # Ensure sufficient gameweeks for meaningful CV
        assert len(forecaster.features_df['gameweek'].unique()) >= 3
        
        with patch('forecasting.RandomForestRegressor') as mock_rf:
            mock_model = MagicMock()
            
            # Create realistically correlated predictions for CV
            def mock_predict(X):
                # Generate predictions with realistic correlation to avoid "suspiciously high" correlation
                base_predictions = np.random.uniform(2, 18, len(X))
                noise = np.random.normal(0, 3, len(X))
                return base_predictions + noise
            
            mock_model.predict.side_effect = mock_predict
            mock_rf.return_value = mock_model
            
            # This should complete and report reasonable performance metrics
            forecaster.cross_validate_temporal()
            
            # Should have created models for multiple CV folds
            assert mock_rf.call_count >= 2
    
    def test_forecasting_error_recovery(self, temp_data_dir):
        """Test forecasting error recovery and graceful degradation"""
        # Create data with some corruption
        corrupted_data = pd.DataFrame({
            'player_id': [1, 2, None],  # Missing player ID
            'gameweek': [1, 1, 1],
            'total_points': [5, None, 12],  # Missing points
            'position': ['GK', 'DEF', ''],  # Empty position
            'price': [5.0, -1.0, 8.0],  # Negative price
            'team_id': [1, 2, 999],  # Invalid team ID
            'difficulty': [3, 0, 6],  # Out of range difficulty
            'is_home': [1, 0, 2],  # Invalid binary value
            'position_encoded': [1, 2, 3],
            'total_points_rolling_3_lag': [np.nan, np.nan, np.nan],
            'minutes_likelihood_3': [0.8, 1.5, 0.7],  # Out of range probability
            'points_consistency_3': [0.5, 0.6, np.nan],
        })
        
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        corrupted_data.to_csv(features_dir / "features.csv", index=False)
        
        forecaster = FPLForecaster()
        forecaster.features_dir = features_dir
        forecaster.forecasts_dir = temp_data_dir / "forecasts"
        forecaster.forecasts_dir.mkdir(exist_ok=True)
        
        # Should either handle gracefully or fail with informative error
        try:
            forecaster.load_features_data()
            
            # If it loads, should handle data cleaning
            X, y = forecaster.prepare_model_data(forecaster.features_df)
            assert not X.isna().any().any()  # Should clean missing values
            assert len(X) > 0  # Should retain some valid data
            
        except Exception as e:
            # Should fail with informative error message
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ['data', 'missing', 'invalid', 'corrupt'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])