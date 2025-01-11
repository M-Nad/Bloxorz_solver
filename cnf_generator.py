import numpy as np
import os

PATH_TO_CNF_FOLDER = r'./cnf_folder'

class Movements:
    up = 1
    down = 2
    left = 3
    right = 4
    
class BlockState:
    up = 1
    down_horizontal = 2
    down_vertical = 3

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
        
    def decode_var(self,var:int):
        assert var>0
        var-=1
        t, var_ = divmod(var, 3 * self.N + 4)
        if var_ >= 3 * self.N: # direction
            move = var_ - 3 * self.N
            return "direction", (t,move+1)
        c, state = divmod(var_, 3) # block state
        return "state", (t,state+1,self.decode_pos[c])
    
    def is_floor(self,coord:tuple[int,int]):
        return coord[0]>=0 and coord[0]<self.h and coord[1]>=0 and coord[1]<self.l and self.is_floor_array[coord]
        
    def can_be_in_state(self, coord, move, state): # Can the cell at coord end up in block state after move ?
        if state == BlockState.up:
            match move:
                case Movements.up:
                    if coord[0]<self.h-2:
                        return self.is_floor((coord[0]+1,coord[1])) and self.is_floor((coord[0]+2,coord[1]))
                case Movements.down:
                    if coord[0]>1:
                        return self.is_floor((coord[0]-1,coord[1])) and self.is_floor((coord[0]-2,coord[1]))
                case Movements.left:
                    if coord[1]<self.l-2:
                        return self.is_floor((coord[0],coord[1]+1)) and self.is_floor((coord[0],coord[1]+2))
                case Movements.right:
                    if coord[1]>1:
                        return self.is_floor((coord[0],coord[1]-1)) and self.is_floor((coord[0],coord[1]-2))
        else : # state is DOWN VERTICAL or DOWN HORIZONTAL
            match move:
                case Movements.up:
                    if coord[0]<self.h-1:
                        return self.is_floor((coord[0]+1,coord[1]))
                case Movements.down:
                    if coord[0]>0:
                        return self.is_floor((coord[0]-1,coord[1]))
                case Movements.left:
                    if coord[1]<self.l-1:
                        return self.is_floor((coord[0],coord[1]+1))
                case Movements.right:
                    if coord[1]>1:
                        return self.is_floor((coord[0],coord[1]-1))
        return False
    
    def create_clauses(self):
        # initial layout
        for i in range(self.h):
            for j in range(self.l):
                if self.is_floor_array[i,j]:
                    c = self.encode_pos[(i,j)]
                    match self.level_array[i,j]:
                        case 1: # no block here
                            self.clauses.append(str(-(c*3 + BlockState.up)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_horizontal)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_vertical)) + " 0\n")
                        case 2: # no block here - objective cell
                            self.clauses.append(str(-(c*3 + BlockState.up)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_horizontal)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_vertical)) + " 0\n")
                        case 3: # initial block UP
                            self.clauses.append(str(c*3 + BlockState.up) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_horizontal)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_vertical)) + " 0\n")
                        case 4: # initial block DOWN HORIZONTAL
                            self.clauses.append(str(-(c*3 + BlockState.up)) + " 0\n")
                            self.clauses.append(str(c*3 + BlockState.down_horizontal) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_vertical)) + " 0\n")
                        case 5: # initial block DOWN VERTICAL
                            self.clauses.append(str(-(c*3 + BlockState.up)) + " 0\n")
                            self.clauses.append(str(-(c*3 + BlockState.down_horizontal)) + " 0\n")
                            self.clauses.append(str(c*3 + BlockState.down_vertical) + " 0\n")
                    
        # objective
        line = ""
        objective_cells = [tuple(cell) for cell in np.argwhere(self.level_array==2)]
        for cell in objective_cells:
            c = self.encode_pos[cell]
            # block up position on objective cell at Tmax
            line += str((self.Tmax-1)*(3 * self.N + 4) + c*3 + BlockState.up) + " " 
        line += "0\n"
        self.clauses.append(line)
        
        # at each time step exacly one movement can be done
        move_list = [Movements.up, Movements.down, Movements.left, Movements.right]
        for t in range(self.Tmax-1): # range(Tmax-1) : No movement at last step Tmax
            
            # at least one movement at time step t
            line = ""
            for move in move_list:
                line += str(t*(3 * self.N + 4) + 3 * self.N + move) + " "
            line += "0\n"
            self.clauses.append(line)

            # at most 1 one movement at time step t
            for i,move_1 in enumerate(move_list):
                for move_2 in move_list[i+1:]:
                    line = ""
                    line += str(-(t*(3 * self.N + 4) + 3 * self.N + move_1)) + " "
                    line += str(-(t*(3 * self.N + 4) + 3 * self.N + move_2)) + " "
                    line += "0\n"
                    self.clauses.append(line)
        
        # transition clauses
        for i in range(self.h):
            for j in range(self.l):
                if self.is_floor_array[i,j]:
                    c = self.encode_pos[(i,j)]
                    # transition to block UP
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.up):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.up) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.up)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i+1,j)]*3 + BlockState.down_vertical)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i+2,j)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.up):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.up) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.down)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i-1,j)]*3 + BlockState.down_vertical)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i-2,j)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.up):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.up) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.left)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j+1)]*3 + BlockState.down_vertical)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j+2)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.up):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.up) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.right)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j-1)]*3 + BlockState.down_vertical)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j-2)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)

                    # transition to block DOWN HORIZONTAL
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.down_horizontal):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.up)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i+1,j)]*3 + BlockState.down_horizontal)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.down_horizontal):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.down)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i-1,j)]*3 + BlockState.down_horizontal)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.down_horizontal):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.left)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j+1)]*3 + BlockState.up)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                            if self.is_floor((i,j+2)):
                                line = ""
                                line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                                line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.left)) + " "
                                line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j+2)]*3 + BlockState.up)) + " "
                                line += "0\n"
                                self.clauses.append(line)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.down_horizontal):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.right)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j-1)]*3 + BlockState.up)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                            if self.is_floor((i,j-2)):
                                line = ""
                                line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_horizontal) + " "
                                line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.right)) + " "
                                line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j-2)]*3 + BlockState.up)) + " "
                                line += "0\n"
                                self.clauses.append(line)
                            
                    # transition to block DOWN VERTICAL
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.down_vertical):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.up)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i+1,j)]*3 + BlockState.up)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                            if self.is_floor((i+2,j)):
                                line = ""
                                line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                                line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.up)) + " "
                                line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i+2,j)]*3 + BlockState.up)) + " "
                                line += "0\n"
                                self.clauses.append(line)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.down_vertical):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.down)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i-1,j)]*3 + BlockState.up)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                            if self.is_floor((i-2,j)):
                                line = ""
                                line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                                line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.down)) + " "
                                line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i-2,j)]*3 + BlockState.up)) + " "
                                line += "0\n"
                                self.clauses.append(line)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.down_vertical):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.left)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j+1)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.down_vertical):
                        for t in range(self.Tmax-1):
                            line = ""
                            line += str((t+1)*(3 * self.N + 4) + c*3 + BlockState.down_vertical) + " "
                            line += str(-(t*(3 * self.N + 4) + 3 * self.N + Movements.right)) + " "
                            line += str(-(t*(3 * self.N + 4) + self.encode_pos[(i,j-1)]*3 + BlockState.down_vertical)) + " "
                            line += "0\n"
                            self.clauses.append(line)

    def write_cnf(self, path=None):
        assert len(self.clauses)>0
        if path is None:
            path = os.path.join(PATH_TO_CNF_FOLDER,f'level_{self.level_id}.cnf')
            if not os.path.exists(PATH_TO_CNF_FOLDER):
                os.makedirs(PATH_TO_CNF_FOLDER)
        with open(path, "w") as fichier:
            fichier.write("c Solveur pour Bloxorz\n")
            fichier.write(f"p cnf {self.nb_vars} {len(self.clauses)}\n")
            for clause in self.clauses:
                fichier.write(clause)