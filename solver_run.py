import os
import subprocess
import re
import itertools

folder_cnf_path = r'./'

def execute_solver(path_to_solv='gophersat_win64.exe',path_to_file='graphe_col_0.cnf'):
    output = subprocess.run([path_to_solv, path_to_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
    if "UNSATISFIABLE" in output:
        print("--- UNSATISFIABLE ---")
        return None
    else :
        print("--- SATISFIABLE ---")
        s_ = output.split("v ")[-1]
        res_ = s_.split(" ")[:-1] # last number is 0 for seq_end
        return list(map(int,res_))