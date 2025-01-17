import numpy as np
import os
from solver.clauses import VAR, AND, OR, IMPLIES

PATH_TO_CNF_FOLDER = r'./solver/cnf_folder'

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
    def __init__(self, level_dict:dict, Tmax:int):
        self.level_name = level_dict['level_name']
        self.level_array = np.array(level_dict['grid'], dtype=bool)
        self.level_start = tuple(level_dict['start'])
        self.level_end = tuple(level_dict['end'])
        self.level_red_grid = np.array(level_dict["red_grid"], dtype=bool) if "red_grid" in level_dict.keys() else None
        self.save_path = None
        assert Tmax >= 0
        self.Tmax = Tmax+1
        self.h, self.l = self.level_array.shape
        self.N =  int(self.level_array.sum())
        self.decode_pos = {id:tuple(coord) for id,coord in enumerate(np.argwhere(self.level_array).tolist())}
        self.encode_pos = {coord:id for id,coord in self.decode_pos.items()}
        
        self.nb_vars = self.Tmax * (3 * self.N + 4) - 4
        self.conjonctive_clauses = []
        
    def get_save_path(self):
        return self.save_path
    
    def get_level_name(self):
        return self.level_name
    
    def get_level_end(self):
        return self.level_end
    
    def get_level_array(self):
        return self.level_array.copy()
    
    def get_level_red_grid(self):
        if self.level_red_grid is None:
            return None
        else:
            return self.level_red_grid.copy()
        
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
        return coord[0]>=0 and coord[0]<self.h and coord[1]>=0 and coord[1]<self.l and self.level_array[coord]
        
    def can_be_in_state(self, coord, move, state): # Can the cell at coord end up in block state after move ?
        if state == BlockState.up:
            
            # The block cannot be in UP position on a red cell !
            if self.level_red_grid is not None and self.level_red_grid[coord]:
                return False
            
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
                coord = (i,j)
                if self.is_floor(coord):
                    c = self.encode_pos[coord]
                    init_clauses = AND()
                    if coord == self.level_start:
                        init_clauses.add_clause(VAR(c*3 + BlockState.up))
                        init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                        init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                    else: # no block here
                        init_clauses.add_clause(VAR(c*3 + BlockState.up).not_())
                        init_clauses.add_clause(VAR(c*3 + BlockState.down_horizontal).not_())
                        init_clauses.add_clause(VAR(c*3 + BlockState.down_vertical).not_())
                    init_cnf = init_clauses.get_cnf_list()
                    for clause in init_cnf:
                        self.conjonctive_clauses.append(self.list_to_str(clause))
        
        # objective
        objective_clauses = OR()
        c = self.encode_pos[self.level_end]
        # block up position on objective cell at Tmax
        objective_clauses.add_clause((self.Tmax-1)*(3 * self.N + 4) + c*3 + BlockState.up)
        objective_cnf = objective_clauses.get_cnf_list()
        assert len(objective_cnf) > 0 # at least one objective
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
                coord = (i,j)
                if self.is_floor(coord):
                    c = self.encode_pos[coord]
                    # transition to block UP
                    condition = None
                    consequence = VAR((3 * self.N + 4) + c*3 + BlockState.up)
                    # UP direction
                    if self.can_be_in_state(coord, Movements.up, BlockState.up):
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
                    if self.can_be_in_state(coord, Movements.down, BlockState.up):
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
                    if self.can_be_in_state(coord, Movements.left, BlockState.up):
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
                    if self.can_be_in_state(coord, Movements.right, BlockState.up):
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
                    if self.can_be_in_state(coord, Movements.up, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state(coord, Movements.down, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.down_horizontal
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state(coord, Movements.left, BlockState.down_horizontal):
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
                    if self.can_be_in_state(coord, Movements.right, BlockState.down_horizontal):
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
                    if self.can_be_in_state(coord, Movements.up, BlockState.down_vertical):
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
                    if self.can_be_in_state(coord, Movements.down, BlockState.down_vertical):
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
                    if self.can_be_in_state(coord, Movements.left, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.down_vertical
                        )
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state(coord, Movements.right, BlockState.down_vertical):
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
            path = os.path.join(PATH_TO_CNF_FOLDER,f'{self.level_name}.cnf')
            if not os.path.exists(PATH_TO_CNF_FOLDER):
                os.makedirs(PATH_TO_CNF_FOLDER)
        self.save_path = path
        with open(path, "w") as file:
            file.write("c Solveur pour Bloxorz\n")
            file.write(f"p cnf {self.nb_vars} {len(self.conjonctive_clauses)}\n")
            for clause in self.conjonctive_clauses:
                file.write(clause)