import numpy as np
import os

class CNF:
    def __init__(self, level_array:np.ndarray, level_id:int, Tmax:int):
        self.level_id = level_id
        self.level_array = level_array
        self.h, self.l = level_array.shape
        self.nb_vars = 0
        self.clauses = []
        
    def write_cnf(self, path=None):
        assert len(self.clauses)>0
        if path is None:
            path = os.path.join('cnf_folder',f'level_{self.level_id}.cnf')
            if not os.path.exists('cnf_folder'):
                os.makedirs('cnf_folder')
        with open(path, "w") as fichier:
            fichier.write("c Solveur pour Bloxorz\n")
            fichier.write(f"p cnf {self.nb_vars} {len(self.clauses)}\n")
            for clause in self.clauses:
                fichier.write(clause)