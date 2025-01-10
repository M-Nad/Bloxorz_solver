import numpy as np
import os

class CNF:
    def __init__(self, level_array:np.ndarray, level_id:int, Tmax:int):
        self.level_id = level_id
        self.level_array = level_array
        self.Tmax = Tmax
        self.h, self.l = level_array.shape
        self.is_floor_array = level_array>0
        self.N =  self.is_floor_array.sum()
        self.decode_pos = {id:tuple(coord) for id,coord in enumerate(np.argwhere(self.is_floor_array).tolist())}
        self.encode_pos = {tuple(coord):id for id,coord in enumerate(np.argwhere(self.is_floor_array).tolist())}
        
        self.nb_vars = Tmax * (3 * self.N + 4)
        self.clauses = []
        
    def create_clauses(self):
        # initial layout
        for i in range(self.h):
            for j in range(self.l):
                if self.is_floor_array[i,j]:
                    c = self.encode_pos((i,j))
                    line = ""
                    match self.level_array[i,j]:
                        case 1: # no block here
                            line += str(-(c*3 + 1)) + " "
                            line += str(-(c*3 + 2)) + " "
                            line += str(-(c*3 + 3)) + " "
                        case 2: # no block here
                            line += str(-(c*3 + 1)) + " "
                            line += str(-(c*3 + 2)) + " "
                            line += str(-(c*3 + 3)) + " "
                        case 3: # initial block UP
                            line += str(c*3 + 1) + " "
                            line += str(-(c*3 + 2)) + " "
                            line += str(-(c*3 + 3)) + " "
                        case 4: # initial block DOWN HORIZONTAL
                            line += str(c*3 + 2) + " "
                            line += str(-(c*3 + 1)) + " "
                            line += str(-(c*3 + 3)) + " "
                        case 4: # initial block DOWN VERTICAL
                            line += str(c*3 + 3) + " "
                            line += str(-(c*3 + 1)) + " "
                            line += str(-(c*3 + 2)) + " "
                    line += "0\n"
                    self.clauses.append(line)
        
        # at each time step exacly one movement can be done

        
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