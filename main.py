from level_manager import load_levels, display_solution
from cnf_generator import CNF, PATH_TO_CNF_FOLDER
from solver_run import execute_solver
import os

T_MAX = 4

def main(level_id:int):
    level_dict = load_levels()
    assert level_id in level_dict.keys()
    cnf = CNF(level_dict[level_id], level_id, T_MAX)
    cnf.create_clauses()
    cnf.write_cnf()
    res = execute_solver(path_to_file=os.path.join(PATH_TO_CNF_FOLDER,f'level_{level_id}.cnf'))
    print([r for r in res if r>0]) ##
    display_solution(res, cnf)

if __name__ == "__main__":
    main(1)