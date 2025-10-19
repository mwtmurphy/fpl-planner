"""Unit tests for data storage."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from fpl.core.models import Player, Fixture
from fpl.data.storage import DataStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage for testing."""
    return DataStorage(data_dir=tmp_path)


@pytest.fixture
def sample_players(sample_player_data):
    """Create sample player list."""
    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["web_name"] = "Salah"
    player2["total_points"] = 220

    return [Player(**sample_player_data), Player(**player2)]


@pytest.fixture
def sample_fixtures_list(sample_fixture_data):
    """Create sample fixture list."""
    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["team_h"] = 3
    fixture2["team_a"] = 4

    return [Fixture(**sample_fixture_data), Fixture(**fixture2)]


# Basic save/load tests


def test_storage_initialization(tmp_path):
    """Test storage initialization creates directory."""
    storage = DataStorage(data_dir=tmp_path / "test_data")
    assert storage.data_dir.exists()
    assert storage.data_dir.is_dir()


def test_save_and_load_players(temp_storage, sample_players):
    """Test saving and loading players."""
    temp_storage.save_players(sample_players)

    loaded = temp_storage.load_players()

    assert len(loaded) == 2
    assert loaded[0].id == 302
    assert loaded[1].id == 400
    assert loaded[0].web_name == "Saka"
    assert loaded[1].web_name == "Salah"


def test_load_players_empty(temp_storage):
    """Test loading players returns empty list when file doesn't exist."""
    players = temp_storage.load_players()
    assert players == []


def test_save_and_load_fixtures(temp_storage, sample_fixtures_list):
    """Test saving and loading fixtures."""
    temp_storage.save_fixtures(sample_fixtures_list)

    loaded = temp_storage.load_fixtures()

    assert len(loaded) == 2
    assert loaded[0].id == 1
    assert loaded[1].id == 2


def test_load_fixtures_empty(temp_storage):
    """Test loading fixtures returns empty list when file doesn't exist."""
    fixtures = temp_storage.load_fixtures()
    assert fixtures == []


# Cache management tests


def test_cache_set_and_get(temp_storage):
    """Test basic cache operations."""
    data = {"key": "value", "number": 42}

    temp_storage.set_cached("test", data)
    cached = temp_storage.get_cached("test")

    assert cached == data


def test_cache_get_missing(temp_storage):
    """Test getting non-existent cache returns None."""
    cached = temp_storage.get_cached("missing")
    assert cached is None


def test_cache_ttl_not_expired(temp_storage):
    """Test cache is valid within TTL."""
    data = {"test": "data"}

    temp_storage.set_cached("test", data, ttl_seconds=3600)
    cached = temp_storage.get_cached("test", ttl_seconds=3600)

    assert cached == data


def test_cache_ttl_expired(temp_storage):
    """Test cache expires after TTL."""
    data = {"test": "data"}

    # Set cache
    temp_storage.set_cached("test", data, ttl_seconds=1)

    # Wait for expiry
    time.sleep(1.1)

    # Should be expired
    cached = temp_storage.get_cached("test", ttl_seconds=1)
    assert cached is None

    # Cache file should be removed
    cache_file = temp_storage.data_dir / ".cache_test.json"
    assert not cache_file.exists()


def test_cache_no_ttl(temp_storage):
    """Test cache with no TTL never expires."""
    data = {"test": "data"}

    temp_storage.set_cached("test", data, ttl_seconds=None)

    # Even after time passes, should still be valid
    time.sleep(0.1)
    cached = temp_storage.get_cached("test", ttl_seconds=None)

    assert cached == data


def test_invalidate_cache(temp_storage):
    """Test cache invalidation."""
    data = {"test": "data"}

    temp_storage.set_cached("test", data)
    temp_storage.invalidate_cache("test")

    cached = temp_storage.get_cached("test")
    assert cached is None


def test_invalidate_missing_cache(temp_storage):
    """Test invalidating non-existent cache doesn't error."""
    # Should not raise error
    temp_storage.invalidate_cache("missing")


def test_clear_all_cache(temp_storage):
    """Test clearing all cache files."""
    temp_storage.set_cached("test1", {"a": 1})
    temp_storage.set_cached("test2", {"b": 2})
    temp_storage.set_cached("test3", {"c": 3})

    count = temp_storage.clear_all_cache()

    assert count == 3
    assert temp_storage.get_cached("test1") is None
    assert temp_storage.get_cached("test2") is None
    assert temp_storage.get_cached("test3") is None


# Timestamp tracking tests


def test_set_and_get_last_update(temp_storage):
    """Test timestamp tracking."""
    before = datetime.now()

    temp_storage.set_last_update("players")

    after = datetime.now()
    last_update = temp_storage.get_last_update("players")

    assert last_update is not None
    assert before <= last_update <= after


def test_get_last_update_missing(temp_storage):
    """Test getting last update for never-updated type returns None."""
    last_update = temp_storage.get_last_update("never_updated")
    assert last_update is None


def test_set_last_update_custom_timestamp(temp_storage):
    """Test setting custom timestamp."""
    custom_time = datetime(2024, 8, 16, 12, 0, 0)

    temp_storage.set_last_update("players", custom_time)
    last_update = temp_storage.get_last_update("players")

    assert last_update == custom_time


def test_timestamp_persistence(temp_storage):
    """Test timestamps persist across storage instances."""
    temp_storage.set_last_update("players")
    timestamp1 = temp_storage.get_last_update("players")

    # Create new storage instance with same directory
    new_storage = DataStorage(data_dir=temp_storage.data_dir)
    timestamp2 = new_storage.get_last_update("players")

    assert timestamp1 == timestamp2


# Player price tracking tests


def test_save_and_get_player_prices(temp_storage):
    """Test player price tracking."""
    prices = {302: 95, 400: 130, 500: 75}

    temp_storage.save_player_prices(prices)
    loaded_prices = temp_storage.get_player_prices()

    assert loaded_prices == prices


def test_get_player_prices_empty(temp_storage):
    """Test getting prices when none saved returns empty dict."""
    prices = temp_storage.get_player_prices()
    assert prices == {}


def test_player_prices_persistence(temp_storage):
    """Test prices persist across storage instances."""
    prices = {302: 95, 400: 130}

    temp_storage.save_player_prices(prices)

    # Create new storage instance
    new_storage = DataStorage(data_dir=temp_storage.data_dir)
    loaded_prices = new_storage.get_player_prices()

    assert loaded_prices == prices


# CSV export tests


def test_save_players_csv(temp_storage, sample_players):
    """Test exporting players to CSV."""
    temp_storage.save_players_csv(sample_players)

    csv_file = temp_storage.data_dir / "players.csv"
    assert csv_file.exists()

    # Read and verify
    df = pd.read_csv(csv_file)
    assert len(df) == 2
    assert df["id"].tolist() == [302, 400]
    assert df["web_name"].tolist() == ["Saka", "Salah"]


def test_save_players_csv_custom_filename(temp_storage, sample_players):
    """Test CSV export with custom filename."""
    temp_storage.save_players_csv(sample_players, "custom_players.csv")

    csv_file = temp_storage.data_dir / "custom_players.csv"
    assert csv_file.exists()


def test_save_players_csv_empty(temp_storage):
    """Test saving empty player list doesn't create file."""
    temp_storage.save_players_csv([])

    csv_file = temp_storage.data_dir / "players.csv"
    assert not csv_file.exists()


def test_save_fixtures_csv(temp_storage, sample_fixtures_list):
    """Test exporting fixtures to CSV."""
    temp_storage.save_fixtures_csv(sample_fixtures_list)

    csv_file = temp_storage.data_dir / "fixtures.csv"
    assert csv_file.exists()

    # Read and verify
    df = pd.read_csv(csv_file)
    assert len(df) == 2
    assert df["id"].tolist() == [1, 2]


def test_save_fixtures_csv_empty(temp_storage):
    """Test saving empty fixture list doesn't create file."""
    temp_storage.save_fixtures_csv([])

    csv_file = temp_storage.data_dir / "fixtures.csv"
    assert not csv_file.exists()


# DataFrame export tests


def test_export_to_dataframe_players(temp_storage, sample_players):
    """Test converting players to DataFrame."""
    df = temp_storage.export_to_dataframe(sample_players)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "id" in df.columns
    assert "web_name" in df.columns
    assert df["id"].tolist() == [302, 400]


def test_export_to_dataframe_fixtures(temp_storage, sample_fixtures_list):
    """Test converting fixtures to DataFrame."""
    df = temp_storage.export_to_dataframe(sample_fixtures_list)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "id" in df.columns
    assert df["id"].tolist() == [1, 2]


def test_export_to_dataframe_empty(temp_storage):
    """Test converting empty list returns empty DataFrame."""
    df = temp_storage.export_to_dataframe([])

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_save_dataframe_csv(temp_storage, sample_players):
    """Test saving DataFrame as CSV."""
    df = temp_storage.export_to_dataframe(sample_players)
    temp_storage.save_dataframe(df, "output.csv", format="csv")

    output_file = temp_storage.data_dir / "output.csv"
    assert output_file.exists()

    # Read and verify
    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 2


def test_save_dataframe_json(temp_storage, sample_players):
    """Test saving DataFrame as JSON."""
    df = temp_storage.export_to_dataframe(sample_players)
    temp_storage.save_dataframe(df, "output.json", format="json")

    output_file = temp_storage.data_dir / "output.json"
    assert output_file.exists()

    # Read and verify
    with output_file.open("r") as f:
        data = json.load(f)
    assert len(data) == 2


@pytest.mark.skipif(
    not hasattr(pd, "read_parquet"),
    reason="Parquet support requires pyarrow or fastparquet",
)
def test_save_dataframe_parquet(temp_storage, sample_players):
    """Test saving DataFrame as Parquet."""
    try:
        df = temp_storage.export_to_dataframe(sample_players)
        temp_storage.save_dataframe(df, "output.parquet", format="parquet")

        output_file = temp_storage.data_dir / "output.parquet"
        assert output_file.exists()

        # Read and verify
        loaded_df = pd.read_parquet(output_file)
        assert len(loaded_df) == 2
    except ImportError:
        pytest.skip("Parquet support not available (pyarrow/fastparquet not installed)")


def test_save_dataframe_invalid_format(temp_storage, sample_players):
    """Test saving DataFrame with invalid format raises error."""
    df = temp_storage.export_to_dataframe(sample_players)

    with pytest.raises(ValueError, match="Unsupported format"):
        temp_storage.save_dataframe(df, "output.xyz", format="xyz")


# Integration tests


def test_cache_workflow(temp_storage):
    """Test typical cache workflow."""
    # First request - cache miss
    cached = temp_storage.get_cached("players", ttl_seconds=3600)
    assert cached is None

    # Fetch and cache data
    data = {"players": [1, 2, 3]}
    temp_storage.set_cached("players", data, ttl_seconds=3600)

    # Second request - cache hit
    cached = temp_storage.get_cached("players", ttl_seconds=3600)
    assert cached == data

    # Invalidate and fetch again
    temp_storage.invalidate_cache("players")
    cached = temp_storage.get_cached("players", ttl_seconds=3600)
    assert cached is None


def test_timestamp_workflow(temp_storage):
    """Test typical timestamp tracking workflow."""
    # Check if never updated
    last_update = temp_storage.get_last_update("players")
    assert last_update is None

    # Update data and set timestamp
    temp_storage.set_last_update("players")
    last_update = temp_storage.get_last_update("players")
    assert last_update is not None

    # Check if update needed (e.g., after 1 day)
    age = datetime.now() - last_update
    needs_update = age > timedelta(days=1)
    assert not needs_update  # Just updated


def test_price_change_detection(temp_storage, sample_players):
    """Test detecting price changes."""
    # Save initial prices
    old_prices = {p.id: p.now_cost for p in sample_players}
    temp_storage.save_player_prices(old_prices)

    # Simulate price change
    sample_players[0].now_cost = 96  # Saka rises
    new_prices = {p.id: p.now_cost for p in sample_players}

    # Detect changes
    stored_prices = temp_storage.get_player_prices()
    changes = {
        pid: new_prices[pid] - stored_prices[pid]
        for pid in new_prices
        if pid in stored_prices and new_prices[pid] != stored_prices[pid]
    }

    assert len(changes) == 1
    assert 302 in changes
    assert changes[302] == 1  # +0.1m (in API units)


def test_full_data_pipeline(temp_storage, sample_players):
    """Test complete data pipeline: save JSON, export CSV, create DataFrame."""
    # Save as JSON
    temp_storage.save_players(sample_players)

    # Load from JSON
    loaded_players = temp_storage.load_players()
    assert len(loaded_players) == 2

    # Export to CSV
    temp_storage.save_players_csv(loaded_players, "export.csv")

    # Create DataFrame
    df = temp_storage.export_to_dataframe(loaded_players)
    assert isinstance(df, pd.DataFrame)

    # Save DataFrame
    temp_storage.save_dataframe(df, "dataframe_export.csv", format="csv")

    # Verify all files exist
    assert (temp_storage.data_dir / "players.json").exists()
    assert (temp_storage.data_dir / "export.csv").exists()
    assert (temp_storage.data_dir / "dataframe_export.csv").exists()
