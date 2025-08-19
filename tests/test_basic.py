
import pandas as pd
import pulp
from optimiser.solver import build_squad_lp, extract_solution

def test_build_and_solve_small_lp():
    rows = []
    pid = 1
    def add(n, etype, team, cost, pts):
        nonlocal pid
        for _ in range(n):
            rows.append(dict(id=pid, team=team, element_type=etype, now_cost=cost, exp_pts=pts))
            pid += 1
    add(2,1,1,45,3.0)   # GK
    add(5,2,2,45,4.0)   # DEF
    add(5,3,3,50,4.5)   # MID
    add(3,4,4,55,5.0)   # FWD

    players = pd.DataFrame(rows)
    model, x = build_squad_lp(players, budget_m=100.0, max_per_team=15)
    status = model.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"
    squad = extract_solution(players, x)
    assert len(squad) == 15
