import os
import subprocess

def execute_solver(path_to_file:str, path_to_solver:str, verbose:bool=False, mute_error=False):
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
        
    except FileNotFoundError as e:
        if verbose : 
            if not os.path.exists(path_to_solver):
                print("--- SOLVER FILE NOT FOUND ---")
                print("Solver file not found:", path_to_solver)
                print("You can specify the correct path with the argument -s <path_to_solver>")
            if not os.path.exists(path_to_file):
                print("--- LEVEL FILE NOT FOUND ---")
                print("Level file not found:", path_to_file)
                print("You can specify the correct path with the argument -l <path_to_level>")

        if not mute_error: print("File not found error:", e)
        return -1 # Stop iterations

    except OSError as e:
        if verbose: 
            print("--- OS ERROR ---")
            print("Solver might not be valid:", path_to_solver)
            print("OS error:", e)
        return -1 # Stop iterations