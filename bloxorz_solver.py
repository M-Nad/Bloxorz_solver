from solver.level_manager import load_level, convert_vars_to_sequence, display_solution
from solver.cnf_generator import CNF, PATH_TO_CNF_FOLDER
from solver.solver_run import execute_solver
import argparse
import os
import time

# ----------[DEFAULT PARAMETERS]----------
PATH_TO_LEVEL = r'./levels/level_1.json'
T_MAX = 50
T_MIN = 1
PATH_TO_SOLVER = r'./gophersat/gophersat_win64.exe'
# ----------------------------------------

def main(path_to_level: str, t_max: int, path_to_solver: str, graphical_display: bool, unmute_error : bool, time_execution : bool):
    t_end = None
    level_dict = load_level(path_to_level)
    if level_dict == -1: # Error, stop iterations
        exit()
    cnf = CNF(level_dict, t_max)
    cnf.create_clauses()
    cnf.write_cnf()
    path_to_cnf = cnf.get_save_path()
    res = execute_solver(
        path_to_file=path_to_cnf,
        path_to_solver=path_to_solver,
        verbose=True,
        mute_error= not(unmute_error)
        )
    if res == -1: # Error, stop iterations
        exit()
    elif res is not None:
        sequence_dict = convert_vars_to_sequence(res, cnf)
        if time_execution : t_end = time.time() # Solver end
        print(f'\nSolution to {cnf.get_level_name()} :\n')
        print(f'Movement sequence : {sequence_dict["movement_sequence"]}')
        display_solution(sequence_dict, graphical_display=graphical_display)
        return True, t_end # SATISFIABLE
    return False, t_end  # UNSATISFIABLE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Bloxorz level solver")
    parser.add_argument('-l', '--level', type=str, 
                        default=PATH_TO_LEVEL,
                        help='Path to the level JSON file')
    parser.add_argument('-t', '--time', 
                        action='store_true',
                        help='Time solver execution')
    parser.add_argument('-g', '--graphics', 
                        action='store_true',
                        help='Activate graphical display, instead of Terminal one')
    parser.add_argument('-e', '--unmute_error', 
                        action='store_true',
                        help='Display thrown errors in terminal')
    parser.add_argument('--t_max', type=int,
                        default=T_MAX,
                        help='Maximum value for T_MAX')
    parser.add_argument('--t_min', type=int,
                        default=T_MIN,
                        help='Minimum value for T_MAX')
    parser.add_argument('-s', '--solver', type=str, 
                        default=PATH_TO_SOLVER,
                        help='Path to the solver executable')

    args = parser.parse_args()

    satisfiable = False
    t_max = args.t_min
    if args.time : t_start = time.time() # Solver start
    while not satisfiable and t_max <= args.t_max:
        print(f"\nT_MAX = {t_max} / {args.t_max}", end=" ")
        t_max += 1
        satisfiable, t_end = main(args.level, t_max, args.solver, args.graphics, args.unmute_error, args.time)
    if args.time : print(f"Elapsed time : {t_end-t_start}")