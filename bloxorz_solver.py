from solver.level_manager import load_level, convert_vars_to_sequence, display_solution
from solver.cnf_generator import CNF, PATH_TO_CNF_FOLDER
from solver.solver_run import execute_solver
import argparse
import os

# ----------[DEFAULT PARAMETERS]----------
PATH_TO_LEVEL = r'./levels/level_1.json'
T_MAX = 50
T_MIN = 1
PATH_TO_SOLVER = r'./gophersat/gophersat_win64.exe'
# ----------------------------------------

def main(path_to_level: str, t_max: int, path_to_solver: str):
    level_dict = load_level(path_to_level)
    cnf = CNF(level_dict, t_max)
    cnf.create_clauses()
    cnf.write_cnf()
    path_to_cnf = cnf.get_save_path()
    res = execute_solver(
        path_to_file=path_to_cnf,
        path_to_solver=path_to_solver,
        verbose=True,
        mute_error=True
        )
    if res is not None:
        sequence_dict = convert_vars_to_sequence(res, cnf)
        print(f'\nSolution to {cnf.get_level_name()} :\n')
        print(f'Movement sequence : {sequence_dict["movement_sequence"]}')
        display_solution(sequence_dict)
        return True  # SATISFIABLE
    return False  # UNSATISFIABLE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Bloxorz level solver")
    parser.add_argument('--level', type=str, 
                        default=PATH_TO_LEVEL,
                        help='Path to the level JSON file')
    parser.add_argument('--t_max', type=int,
                        default=T_MAX,
                        help='Maximum value for T_MAX')
    parser.add_argument('--t_min', type=int,
                        default=T_MIN,
                        help='Minimum value for T_MAX')
    parser.add_argument('--solver', type=str, 
                        default=PATH_TO_SOLVER,
                        help='Path to the solver executable')

    args = parser.parse_args()

    satisfiable = False
    t_max = args.t_min - 1
    while not satisfiable and t_max < args.t_max:
        print(f"\nT_MAX = {t_max} / {args.t_max}", end=" ")
        t_max += 1
        satisfiable = main(args.level, t_max, args.solver)