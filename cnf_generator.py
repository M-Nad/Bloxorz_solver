import numpy as np
import os
from clauses import VAR, AND, OR, IMPLIES

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
        assert Tmax >= 0
        self.Tmax = Tmax+1
        self.h, self.l = level_array.shape
        self.is_floor_array = level_array>0
        self.N =  int(self.is_floor_array.sum())
        self.decode_pos = {id:tuple(coord) for id,coord in enumerate(np.argwhere(self.is_floor_array).tolist())}
        self.encode_pos = {tuple(coord):id for id,coord in enumerate(np.argwhere(self.is_floor_array).tolist())}
        
        self.nb_vars = self.Tmax * (3 * self.N + 4) - 4
        self.conjonctive_clauses = []
        
    def decode_var(self,var:int):
        assert var>0
        var-=1
        t, var_ = divmod(var, 3 * self.N + 4)
        if var_ >= 3 * self.N: # direction
            move = var_ - 3 * self.N
            return "direction", (t,move+1)
        c, state = divmod(var_, 3) # block state
        return "state", (t,state+1,self.decode_pos[c])
    
    def list_to_str(self,l:list):
        if len(l)==0:
            return ""
        return " ".join(map(str,l+['0']))+"\n"
    
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
                    if coord[1]>0:
                        return self.is_floor((coord[0],coord[1]-1))
        return False
    
    def create_clauses(self):
        # initial layout
        for i in range(self.h):
            for j in range(self.l):
                if self.is_floor_array[i,j]:
                    c = self.encode_pos[(i,j)]
                    init_clauses = AND()
                    match self.level_array[i,j]:
                        case 1: # no block here
                            init_clauses.add_clause(VAR(c*3 + BlockState.up).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                        case 2: # no block here - objective cell
                            init_clauses.add_clause(VAR(c*3 + BlockState.up).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                        case 3: # initial block UP
                            init_clauses.add_clause(VAR(c*3 + BlockState.up))
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                        case 4: # initial block DOWN HORIZONTAL
                            init_clauses.add_clause(VAR(c*3 + BlockState.up).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal))
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                        case 5: # initial block DOWN VERTICAL
                            init_clauses.add_clause(VAR(c*3 + BlockState.up).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                            init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical))
                    init_cnf = init_clauses.get_cnf_list()
                    for clause in init_cnf:
                        self.conjonctive_clauses.append(self.list_to_str(clause))
                    
        # objective
        objective_clauses = OR()
        objective_cells = [tuple(cell) for cell in np.argwhere(self.level_array==2)]
        for cell in objective_cells:
            c = self.encode_pos[cell]
            # block up position on objective cell at Tmax
            objective_clauses.add_clause((self.Tmax-1)*(3 * self.N + 4) + c*3 + BlockState.up)
        objective_cnf = objective_clauses.get_cnf_list()
        assert len(objective_cnf) >0 # at least one objective
        for clause in objective_cnf:
            self.conjonctive_clauses.append(self.list_to_str(clause))
        
        # at each time step exacly one movement can be done
        move_list = [Movements.up, Movements.down, Movements.left, Movements.right]
        for t in range(self.Tmax-1): # range(Tmax-1) : No movement at last step Tmax
            move_clauses = AND()
            
            # at least one movement at time step t
            at_least_one_move_clause = OR()
            for move in move_list:
                at_least_one_move_clause.add_clause(t*(3 * self.N + 4) + 3 * self.N + move)
            move_clauses.add_clause(at_least_one_move_clause)
            
            # at most 1 one movement at time step t
            for i,move_1 in enumerate(move_list):
                for move_2 in move_list[i+1:]:
                    move_clauses.add_clause( OR(
                        VAR(t*(3 * self.N + 4) + 3 * self.N + move_1).not_(),
                        VAR(t*(3 * self.N + 4) + 3 * self.N + move_2).not_()
                    ) )
                    
            move_cnf = move_clauses.get_cnf_list()
            for clause in move_cnf:
                self.conjonctive_clauses.append(self.list_to_str(clause))
        
        # transition clauses
        for i in range(self.h):
            for j in range(self.l):
                if self.is_floor_array[i,j]:
                    c = self.encode_pos[(i,j)]
                    # transition to block UP
                    condition = None
                    consequence = VAR((3 * self.N + 4) + c*3 + BlockState.up)
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.up):
                        cond_ = AND(
                            3 * self.N + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.down_vertical,
                            self.encode_pos[(i+2,j)]*3 + BlockState.down_vertical
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.up):
                        cond_ = AND(
                            3 * self.N + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.down_vertical,
                            self.encode_pos[(i-2,j)]*3 + BlockState.down_vertical
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.up):
                        cond_ = AND(
                            3 * self.N + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.down_horizontal,
                            self.encode_pos[(i,j+2)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.up):
                        cond_ = AND(
                            3 * self.N + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.down_horizontal,
                            self.encode_pos[(i,j-2)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    if condition is None:
                        transition_clause = consequence.not_()
                    else:
                        # transition_clause = IMPLIES(condition, consequence)
                        transition_clause = AND(IMPLIES(condition, consequence), IMPLIES(consequence, condition))
                        
                        transition_cnf = transition_clause.get_cnf_list()
                        for t in range(self.Tmax-1):
                            time_step = t*(3 * self.N + 4)
                            transition_cnf_t = list(map(lambda l: [var+time_step if var>0 else var-time_step for var in l], transition_cnf.copy()))
                            for clause in transition_cnf_t:
                                self.conjonctive_clauses.append(self.list_to_str(clause))

                    # transition to block DOWN HORIZONTAL
                    condition = None
                    consequence = VAR((3 * self.N + 4) + c*3 + BlockState.down_horizontal)
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.up
                        )
                        if self.is_floor((i,j+2)):
                            alt_cond_ = AND(
                                3 * self.N + Movements.left,
                                self.encode_pos[(i,j+2)]*3 + BlockState.up
                            )
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.up
                        )
                        if self.is_floor((i,j-2)):
                            alt_cond_ = AND(
                                3 * self.N + Movements.right,
                                self.encode_pos[(i,j-2)]*3 + BlockState.up
                            )
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    if condition is None:
                        transition_clause = consequence.not_()
                    else:
                        # transition_clause = IMPLIES(condition, consequence)
                        transition_clause = AND(IMPLIES(condition, consequence), IMPLIES(consequence, condition))
                        
                        transition_cnf = transition_clause.get_cnf_list()
                        for t in range(self.Tmax-1):
                            time_step = t*(3 * self.N + 4)
                            transition_cnf_t = list(map(lambda l: [var+time_step if var>0 else var-time_step for var in l], transition_cnf.copy()))
                            for clause in transition_cnf_t:
                                self.conjonctive_clauses.append(self.list_to_str(clause))
                    
                    # transition to block DOWN VERTICAL
                    condition = None
                    consequence = VAR((3 * self.N + 4) + c*3 + BlockState.down_vertical)
                    # UP direction
                    if self.can_be_in_state((i,j), Movements.up, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.up
                        )
                        if self.is_floor((i+2,j)):
                            alt_cond_ = AND(
                                3 * self.N + Movements.up,
                                self.encode_pos[(i+2,j)]*3 + BlockState.up
                            )
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state((i,j), Movements.down, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.up
                        )
                        if self.is_floor((i-2,j)):
                            alt_cond_ = AND(
                                3 * self.N + Movements.down,
                                self.encode_pos[(i-2,j)]*3 + BlockState.up
                            )
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state((i,j), Movements.left, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.down_vertical
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state((i,j), Movements.right, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.down_vertical
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    if condition is None:
                        transition_clause = consequence.not_()
                    else:
                        # transition_clause = IMPLIES(condition, consequence)
                        transition_clause = AND(IMPLIES(condition, consequence), IMPLIES(consequence, condition))
                        
                        transition_cnf = transition_clause.get_cnf_list()
                        for t in range(self.Tmax-1):
                            time_step = t*(3 * self.N + 4)
                            transition_cnf_t = list(map(lambda l: [var+time_step if var>0 else var-time_step for var in l], transition_cnf.copy()))
                            for clause in transition_cnf_t:
                                self.conjonctive_clauses.append(self.list_to_str(clause))

    def write_cnf(self, path=None):
        assert len(self.conjonctive_clauses)>0
        if path is None:
            path = os.path.join(PATH_TO_CNF_FOLDER,f'level_{self.level_id}.cnf')
            if not os.path.exists(PATH_TO_CNF_FOLDER):
                os.makedirs(PATH_TO_CNF_FOLDER)
        with open(path, "w") as fichier:
            fichier.write("c Solveur pour Bloxorz\n")
            fichier.write(f"p cnf {self.nb_vars} {len(self.conjonctive_clauses)}\n")
            for clause in self.conjonctive_clauses:
                fichier.write(clause)