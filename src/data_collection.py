#!/usr/bin/env python3
"""
FPL Data Collection Module

This module fetches data from the official Fantasy Premier League API and saves it
as structured CSV files for further processing.

API Endpoints:
- bootstrap-static: Players, teams, positions, gameweek data
- fixtures: Match fixtures with difficulty ratings  
- event/{GW}/live: Live gameweek scores and statistics

Output Files:
- data/raw/players.csv: Player information and season stats
- data/raw/fixtures.csv: Match fixtures with difficulty ratings
- data/raw/results.csv: Historical gameweek performance data
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class FPLDataCollector:
    """Collects data from the FPL API and saves to CSV files."""
    
    BASE_URL = "https://fantasy.premierleague.com/api"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, output_dir: str = "data/raw"):
        """Initialize the data collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.HEADERS)
        
    def fetch_json(self, endpoint: str) -> Dict:
        """Fetch JSON data from FPL API endpoint with error handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        print(f"Fetching: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            raise
            
    def collect_bootstrap_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Collect player and team data from bootstrap-static endpoint."""
        print("📊 Collecting bootstrap data (players, teams, positions)...")
        
        data = self.fetch_json("bootstrap-static/")
        
        # Extract players data
        players_data = []
        for player in data['elements']:
            # Flatten nested data and convert to snake_case
            player_record = {
                'player_id': player['id'],
                'web_name': player['web_name'],
                'first_name': player['first_name'], 
                'second_name': player['second_name'],
                'team_id': player['team'],
                'element_type': player['element_type'],  # Position (1=GK, 2=DEF, 3=MID, 4=FWD)
                'now_cost': player['now_cost'],  # Price in 0.1m units
                'total_points': player['total_points'],
                'minutes': player['minutes'],
                'goals_scored': player['goals_scored'],
                'assists': player['assists'],
                'clean_sheets': player['clean_sheets'],
                'goals_conceded': player['goals_conceded'],
                'own_goals': player['own_goals'],
                'penalties_saved': player['penalties_saved'],
                'penalties_missed': player['penalties_missed'],
                'yellow_cards': player['yellow_cards'],
                'red_cards': player['red_cards'],
                'saves': player['saves'],
                'bonus': player['bonus'],
                'bps': player['bps'],  # Bonus points system
                'influence': float(player['influence']) if player['influence'] else 0,
                'creativity': float(player['creativity']) if player['creativity'] else 0,
                'threat': float(player['threat']) if player['threat'] else 0,
                'ict_index': float(player['ict_index']) if player['ict_index'] else 0,
                'selected_by_percent': float(player['selected_by_percent']) if player['selected_by_percent'] else 0,
                'form': float(player['form']) if player['form'] else 0,
                'points_per_game': float(player['points_per_game']) if player['points_per_game'] else 0,
                'ep_next': float(player['ep_next']) if player['ep_next'] else 0,
                'ep_this': float(player['ep_this']) if player['ep_this'] else 0,
                'value_form': float(player['value_form']) if player['value_form'] else 0,
                'value_season': float(player['value_season']) if player['value_season'] else 0,
                'transfers_in': player['transfers_in'],
                'transfers_out': player['transfers_out'],
                'transfers_in_event': player['transfers_in_event'],
                'transfers_out_event': player['transfers_out_event'],
                'news': player['news'],
                'news_added': player['news_added'],
                'chance_of_playing_this_round': player['chance_of_playing_this_round'],
                'chance_of_playing_next_round': player['chance_of_playing_next_round'],
                'status': player['status']  # a=available, d=doubtful, i=injured, u=unavailable
            }
            players_data.append(player_record)
            
        players_df = pd.DataFrame(players_data)
        
        # Extract teams data for reference
        teams_data = []
        for team in data['teams']:
            team_record = {
                'team_id': team['id'],
                'team_name': team['name'],
                'short_name': team['short_name'],
                'strength': team['strength'],
                'strength_overall_home': team['strength_overall_home'],
                'strength_overall_away': team['strength_overall_away'], 
                'strength_attack_home': team['strength_attack_home'],
                'strength_attack_away': team['strength_attack_away'],
                'strength_defence_home': team['strength_defence_home'],
                'strength_defence_away': team['strength_defence_away']
            }
            teams_data.append(team_record)
            
        teams_df = pd.DataFrame(teams_data)
        
        # Add position names
        position_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        players_df['position'] = players_df['element_type'].map(position_map)
        
        # Add team names
        players_df = players_df.merge(
            teams_df[['team_id', 'team_name', 'short_name']], 
            on='team_id', 
            how='left'
        )
        
        print(f"✅ Collected {len(players_df)} players from {len(teams_df)} teams")
        return players_df, teams_df
        
    def collect_fixtures_data(self) -> pd.DataFrame:
        """Collect fixture data with difficulty ratings."""
        print("🏟️ Collecting fixtures data...")
        
        data = self.fetch_json("fixtures/")
        
        fixtures_data = []
        for fixture in data:
            # Only include fixtures that have been scheduled
            if fixture['event'] is not None:
                fixture_record = {
                    'fixture_id': fixture['id'],
                    'gameweek': fixture['event'],
                    'team_h': fixture['team_h'],  # Home team ID
                    'team_a': fixture['team_a'],  # Away team ID  
                    'team_h_difficulty': fixture['team_h_difficulty'],
                    'team_a_difficulty': fixture['team_a_difficulty'],
                    'kickoff_time': fixture['kickoff_time'],
                    'finished': fixture['finished'],
                    'started': fixture['started'],
                    'team_h_score': fixture['team_h_score'],
                    'team_a_score': fixture['team_a_score'],
                    'minutes': fixture['minutes'],
                    'provisional_start_time': fixture['provisional_start_time'],
                    'pulse_id': fixture['pulse_id']
                }
                fixtures_data.append(fixture_record)
                
        fixtures_df = pd.DataFrame(fixtures_data)
        
        # Convert kickoff_time to datetime
        fixtures_df['kickoff_time'] = pd.to_datetime(fixtures_df['kickoff_time'])
        
        print(f"✅ Collected {len(fixtures_df)} fixtures")
        return fixtures_df
        
    def collect_gameweek_data(self, max_gameweeks: int = 38) -> pd.DataFrame:
        """Collect historical gameweek performance data."""
        print(f"📈 Collecting gameweek data (up to GW{max_gameweeks})...")
        
        all_results = []
        
        for gw in range(1, max_gameweeks + 1):
            print(f"  Fetching GW{gw}...", end=" ")
            
            try:
                # Get live data for this gameweek
                live_data = self.fetch_json(f"event/{gw}/live/")
                
                # Extract player performance data
                for player_data in live_data['elements']:
                    stats = player_data.get('stats', {})
                    
                    result_record = {
                        'player_id': player_data.get('id'),
                        'gameweek': gw,
                        'minutes': stats.get('minutes', 0),
                        'goals_scored': stats.get('goals_scored', 0),
                        'assists': stats.get('assists', 0), 
                        'clean_sheets': stats.get('clean_sheets', 0),
                        'goals_conceded': stats.get('goals_conceded', 0),
                        'own_goals': stats.get('own_goals', 0),
                        'penalties_saved': stats.get('penalties_saved', 0),
                        'penalties_missed': stats.get('penalties_missed', 0),
                        'yellow_cards': stats.get('yellow_cards', 0),
                        'red_cards': stats.get('red_cards', 0),
                        'saves': stats.get('saves', 0),
                        'bonus': stats.get('bonus', 0),
                        'bps': stats.get('bps', 0),
                        'influence': float(stats.get('influence', 0)),
                        'creativity': float(stats.get('creativity', 0)), 
                        'threat': float(stats.get('threat', 0)),
                        'ict_index': float(stats.get('ict_index', 0)),
                        'total_points': stats.get('total_points', 0),
                        'in_dreamteam': stats.get('in_dreamteam', False)
                    }
                    all_results.append(result_record)
                    
                print("✓")
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"✗ (Error: {e})")
                # Continue with next gameweek if one fails
                continue
                
        results_df = pd.DataFrame(all_results)
        
        if len(results_df) > 0:
            # Sort by gameweek and player_id
            results_df = results_df.sort_values(['gameweek', 'player_id']).reset_index(drop=True)
            
        print(f"✅ Collected {len(results_df)} player-gameweek records")
        return results_df
        
    def save_dataframes(self, players_df: pd.DataFrame, fixtures_df: pd.DataFrame, 
                       results_df: pd.DataFrame) -> None:
        """Save DataFrames to CSV files."""
        print("💾 Saving data to CSV files...")
        
        # Save players data
        players_file = self.output_dir / "players.csv"
        players_df.to_csv(players_file, index=False)
        print(f"  Saved players: {players_file} ({len(players_df)} rows)")
        
        # Save fixtures data  
        fixtures_file = self.output_dir / "fixtures.csv"
        fixtures_df.to_csv(fixtures_file, index=False)
        print(f"  Saved fixtures: {fixtures_file} ({len(fixtures_df)} rows)")
        
        # Save results data
        results_file = self.output_dir / "results.csv"
        results_df.to_csv(results_file, index=False)
        print(f"  Saved results: {results_file} ({len(results_df)} rows)")
        
    def collect_all_data(self) -> None:
        """Main method to collect all FPL data."""
        print("🚀 Starting FPL data collection...")
        print("=" * 50)
        
        try:
            # Collect bootstrap data (players, teams)
            players_df, teams_df = self.collect_bootstrap_data()
            
            # Collect fixtures data
            fixtures_df = self.collect_fixtures_data()
            
            # Collect historical gameweek data
            # Note: This will only collect data for completed gameweeks
            results_df = self.collect_gameweek_data()
            
            # Save all data
            self.save_dataframes(players_df, fixtures_df, results_df)
            
            print("=" * 50)
            print("🎉 Data collection completed successfully!")
            print(f"📁 Files saved to: {self.output_dir}")
            
        except Exception as e:
            print(f"❌ Data collection failed: {e}")
            raise


def main():
    """Main entry point for data collection."""
    collector = FPLDataCollector()
    collector.collect_all_data()


if __name__ == "__main__":
    main()