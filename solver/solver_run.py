import os
import subprocess

PATH_TO_SOLVER = os.path.join('gophersat','gophersat_win64.exe')

def execute_solver(path_to_file:str, path_to_solv:str=PATH_TO_SOLVER, verbose:bool=False):
    output = subprocess.run([path_to_solv, path_to_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
    if "UNSATISFIABLE" in output:
        if verbose: print("--- UNSATISFIABLE ---")
        return None
    else :
        if verbose: print("--- SATISFIABLE ---")
        s_ = output.split("v ")[-1]
        res_ = s_.split(" ")[:-1] # last number is 0 for seq_end
        return list(map(int,res_))