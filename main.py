from level_manager import load_levels, convert_vars_to_sequence, display_solution
# from cnf_generator import CNF, PATH_TO_CNF_FOLDER
from cnf_generator import CNF, PATH_TO_CNF_FOLDER
from solver_run import execute_solver
import os

# -------[PARAMETERS TO MODIFY]-------
LEVEL_ID = 3
T_MAX = 20
T_MIN = 1
# ------------------------------------

def main(level_id:int, t_max:int=T_MAX):
    level_dict = load_levels()
    assert level_id in level_dict.keys()
    cnf = CNF(level_dict[level_id], level_id, t_max)
    cnf.create_clauses()
    cnf.write_cnf()
    res = execute_solver(path_to_file=os.path.join(PATH_TO_CNF_FOLDER,f'level_{level_id}.cnf'), verbose=True)
    if res is not None:
        sequence_dict = convert_vars_to_sequence(res, cnf)
        print(f'Movement sequence : {sequence_dict["movement_sequence"]}')
        display_solution(sequence_dict)
        return True # SATISFIABLE
    return False # UNSATISFIABLE

if __name__ == "__main__":
    level_id = LEVEL_ID
    satisfiable = False
    t_max = T_MIN-1
    while not(satisfiable) and t_max<T_MAX:
        print(f"T_MAX = {t_max} / {T_MAX}",end=" ")
        t_max+=1
        satisfiable = main(level_id, t_max)
        print()