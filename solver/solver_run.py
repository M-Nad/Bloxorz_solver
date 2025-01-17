import os
import subprocess

PATH_TO_SOLVER = os.path.join('gophersat','gophersat_win64.exe')

def execute_solver(path_to_file:str, path_to_solver:str=PATH_TO_SOLVER, verbose:bool=False, mute_error=False):
    command = [path_to_solver, path_to_file]
    try:
        # Gophersat execution
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # get output result
        output = result.stdout
        
        # is the problem satisfaisable ?
        if "s SATISFIABLE" in output:
            if verbose: print("--- SATISFIABLE ---")
            
            # extract variables value
            for line in output.splitlines():
                if line.startswith("v "):  # ligne that contains variables
                    variables = line[2:].split()
                    return list(map(int,variables))

        elif "s UNSATISFIABLE" in output:
            if verbose: print("--- UNSATISFIABLE ---")

        else:
            if not mute_error: print("Unexpected result :", output)

    except subprocess.CalledProcessError as e:
        
        if verbose : print("--- SOLVER ERROR ---")
        if not mute_error: print("Error during Gophersat execution :", e.stderr)
