
"""Expected points plugin system."""

import pandas as pd

class BaseEPModel:
    def compute(self, players_df: pd.DataFrame, fixtures_df: pd.DataFrame, horizon: int, config: dict) -> pd.Series:
        raise NotImplementedError

class FPLEpNextModel(BaseEPModel):
    """Use official FPL `ep_next` field."""
    def compute(self, players_df, fixtures_df, horizon, config):
        s = pd.to_numeric(players_df.get("ep_next", pd.Series([0.0] * len(players_df))), errors="coerce").fillna(0.0)
        return s

class FormPPGBlendModel(BaseEPModel):
    """Blend of form and points-per-game."""
    def compute(self, players_df, fixtures_df, horizon, config):
        form = pd.to_numeric(players_df.get("form", pd.Series([0.0] * len(players_df))), errors="coerce").fillna(0.0)
        ppg = pd.to_numeric(players_df.get("points_per_game", pd.Series([0.0] * len(players_df))), errors="coerce").fillna(0.0)
        return 0.6 * form + 0.4 * ppg

def get_ep_model(name: str) -> BaseEPModel:
    if name == "fpl_ep_next":
        return FPLEpNextModel()
    elif name == "form_ppg_blend":
        return FormPPGBlendModel()
    else:
        raise ValueError(f"Unknown EP model: {name}")
