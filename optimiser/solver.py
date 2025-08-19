
from __future__ import annotations
import logging
from typing import Dict, List, Tuple
import pandas as pd
import pulp

logger = logging.getLogger(__name__)
POSITION_MAP = {1:'GK',2:'DEF',3:'MID',4:'FWD'}

def build_squad_lp(players: pd.DataFrame, budget_m: float, max_per_team: int) -> Tuple[pulp.LpProblem, Dict[int, pulp.LpVariable]]:
    model = pulp.LpProblem("FPL_Squad_Optimisation", sense=pulp.LpMaximize)
    x = {int(row.id): pulp.LpVariable(f"x_{int(row.id)}", cat='Binary') for _, row in players.iterrows()}
    model += pulp.lpSum(x[int(r.id)] * float(r.exp_pts) for _, r in players.iterrows())
    model += pulp.lpSum(x[int(r.id)] * (float(r.now_cost)/10.0) for _, r in players.iterrows()) <= budget_m, "Budget"
    model += pulp.lpSum(x.values()) == 15, "SquadSize"
    for etype, required in [(1,2),(2,5),(3,5),(4,3)]:
        model += pulp.lpSum(x[int(r.id)] for _, r in players[players['element_type']==etype].iterrows()) == required, f"Count_{POSITION_MAP[etype]}")
    for team_id, group in players.groupby('team'):
        model += pulp.lpSum(x[int(r.id)] for _, r in group.iterrows()) <= max_per_team, f"TeamLimit_{int(team_id)}"
    return model, x

def extract_solution(players: pd.DataFrame, x_vars: Dict[int, pulp.LpVariable]) -> pd.DataFrame:
    chosen = [pid for pid,var in x_vars.items() if var.value() is not None and var.value()>0.5]
    return players[players['id'].isin(chosen)].copy()

def pick_starting_xi(squad: pd.DataFrame, formations: List[List[int]]):
    gk = squad[squad['element_type']==1].sort_values('exp_pts', ascending=False).head(1)
    best, best_form = None, None
    for d_need, m_need, f_need in formations:
        d = squad[squad['element_type']==2].sort_values('exp_pts', ascending=False).head(d_need)
        m = squad[squad['element_type']==3].sort_values('exp_pts', ascending=False).head(m_need)
        f = squad[squad['element_type']==4].sort_values('exp_pts', ascending=False).head(f_need)
        xi = pd.concat([gk,d,m,f], ignore_index=True)
        if len(xi)==1+d_need+m_need+f_need:
            if best is None or xi['exp_pts'].sum() > best['exp_pts'].sum():
                best, best_form = xi, [d_need,m_need,f_need]
    if best is None:
        best, best_form = squad.sort_values('exp_pts', ascending=False).head(11), [-1,-1,-1]
    return best, best_form
