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
        self.level_red_grid = None
        self.save_path = None
        
        assert Tmax >= 0
        self.Tmax = Tmax
        self.h, self.l = self.level_array.shape
        self.N =  int(self.level_array.sum())
        self.decode_pos = {id:tuple(coord) for id,coord in enumerate(np.argwhere(self.level_array).tolist())}
        self.encode_pos = {coord:id for id,coord in self.decode_pos.items()}
        self.conjonctive_clauses = []
        
        self.time_step = (3 * self.N + 4)
        self.has_controls = False
        self.nb_controlled_cells = 0
        if "controls" in level_dict : self.add_controls(level_dict["controls"]["buttons"], level_dict["controls"]["controlled_cells"])
        if "red_grid" in level_dict :
            self.level_red_grid = np.array(level_dict["red_grid"], dtype=bool)
            self.add_red_grid(self.level_red_grid)
        self.nb_vars = self.Tmax * self.time_step - 4
        
    def add_controls(self, buttons:list[dict], controlled_cells:list[dict]):
        self.has_controls = True
        self.nb_controlled_cells = len(controlled_cells)
        self.buttons = buttons
        self.time_step += self.nb_controlled_cells
        self.decode_controlled_cells = {}
        condition_to_switch_ON = {}
        condition_to_switch_OFF = {}
        
        # initial control state
        init_control_clauses = AND()
        for i,cell_dict in enumerate(controlled_cells):
            id = i+1
            coord = tuple(cell_dict["position"])
            condition_to_switch_ON[coord] = OR()
            condition_to_switch_OFF[coord] = OR()
            self.decode_controlled_cells[id] = coord
            state_var = 3 * self.N + id
            # Initial state of controlled floor cells
            if cell_dict["state"]:
                init_control_clauses.add_clause(VAR(state_var))
            else:
                init_control_clauses.add_clause(VAR(state_var).not_())
        init_control_cnf = init_control_clauses.get_cnf_list()
        for clause in init_control_cnf:
            self.conjonctive_clauses.append(self.list_to_str(clause))
        self.encode_controlled_cells = {coord:id for id,coord in self.decode_controlled_cells.items()}
            
        # control state transitions
        for button in buttons:
            button_coord = tuple(button["position"])
            c = self.encode_pos[button_coord]
            switch_type = button["switch_type"]
            activation_cond = button["activation"]
            target_cells = [tuple(cell) for cell in button["controls"]]
            for target_cell in target_cells:
                state_var = VAR(3 * self.N + self.encode_controlled_cells[target_cell])
                if switch_type in ["ON", "DUAL"]:
                    condition_to_switch_ON[target_cell].add_clause(
                        VAR(self.time_step + c*3 + BlockState.up)
                    )
                    if activation_cond == "any_pos":
                        condition_to_switch_ON[target_cell].add_clause(
                            VAR(self.time_step + c*3 + BlockState.down_horizontal)
                        )
                        condition_to_switch_ON[target_cell].add_clause(
                            VAR(self.time_step + c*3 + BlockState.down_vertical)
                        )
                if switch_type in ["OFF", "DUAL"]:
                    condition_to_switch_OFF[target_cell].add_clause(
                        VAR(self.time_step + c*3 + BlockState.up)
                    )
                    if activation_cond == "any_pos":
                        condition_to_switch_OFF[target_cell].add_clause(
                            VAR(self.time_step + c*3 + BlockState.down_horizontal)
                        )
                        condition_to_switch_OFF[target_cell].add_clause(
                            VAR(self.time_step + c*3 + BlockState.down_vertical)
                        )
        for target_cell in condition_to_switch_ON.keys():
            condition = OR(
                AND(
                    VAR(3 * self.N + self.encode_controlled_cells[target_cell]),
                    condition_to_switch_OFF[target_cell].not_()
                )
            )
            if not condition_to_switch_ON[target_cell].is_false():
                condition.add_clause(
                    AND(
                        VAR(3 * self.N + self.encode_controlled_cells[target_cell]).not_(),
                        condition_to_switch_ON[target_cell]
                        )
                )
            consequence = VAR(self.time_step + 3 * self.N + self.encode_controlled_cells[target_cell])
            transition_clause = AND(IMPLIES(condition, consequence), IMPLIES(consequence, condition))
            transition_cnf = transition_clause.get_cnf_list()
            for t in range(self.Tmax-1):
                time_gap = t*self.time_step
                transition_cnf_t = list(map(lambda l: [var+time_gap if var>0 else var-time_gap for var in l], transition_cnf.copy()))
                for clause in transition_cnf_t:
                    self.conjonctive_clauses.append(self.list_to_str(clause))
        for target_cell in condition_to_switch_OFF.keys():
            condition = OR(
                AND(
                    VAR(3 * self.N + self.encode_controlled_cells[target_cell]).not_(),
                    condition_to_switch_ON[target_cell].not_()
                )
            )
            if not condition_to_switch_OFF[target_cell].is_false():
                condition.add_clause(
                    AND(
                        VAR(3 * self.N + self.encode_controlled_cells[target_cell]),
                        condition_to_switch_OFF[target_cell]
                    )
                )
            consequence = VAR(self.time_step + 3 * self.N + self.encode_controlled_cells[target_cell]).not_()
            transition_clause = AND(IMPLIES(condition, consequence), IMPLIES(consequence, condition))
            transition_cnf = transition_clause.get_cnf_list()
            for t in range(self.Tmax-1):
                time_gap = t*self.time_step
                transition_cnf_t = list(map(lambda l: [var+time_gap if var>0 else var-time_gap for var in l], transition_cnf.copy()))
                for clause in transition_cnf_t:
                    self.conjonctive_clauses.append(self.list_to_str(clause))
    
    def add_red_grid(self, red_grid:np.ndarray): 
        red_cells = np.argwhere(red_grid)
        
        for cell in red_cells:
            coord = tuple(cell)
            c = self.encode_pos[coord]
            red_cell_clauses = AND()
            for t in range(self.Tmax):
                # no UP position on red cells
                red_cell_clauses.add_clause(
                    VAR(t*self.time_step + c*3 + BlockState.up).not_()
                )
            
            red_cell_cnf = red_cell_clauses.get_cnf_list()
            for clause in red_cell_cnf:
                self.conjonctive_clauses.append(self.list_to_str(clause))
    
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
        if var > 0:
            var-=1
            t, var_ = divmod(var, self.time_step)
            if var_ >= 3 * self.N: # direction or state
                var_ -= 3 * self.N
                if var_ >= self.nb_controlled_cells: # direction
                    move = var_ - self.nb_controlled_cells
                    return "direction", (t,move+1)
                else : # controlled cell ON
                    id = var_+1
                    return "controlled_cell_ON", (t, self.decode_controlled_cells[id])
            c, state = divmod(var_, 3) # block state
            return "state", (t,state+1,self.decode_pos[c])
        elif var < 0 and self.has_controls: # look for controlled cell OFF
            var_ = -var - 1
            t, var_ = divmod(var_, self.time_step)
            if var_ >= 3 * self.N and var_ < 3 * self.N + self.nb_controlled_cells:
                id = var_ - 3 * self.N + 1
                return "controlled_cell_OFF", (t, self.decode_controlled_cells[id])
        return None, None
    
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
        objective_clauses.add_clause((self.Tmax-1)*self.time_step + c*3 + BlockState.up)
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
                at_least_one_move_clause.add_clause(t*self.time_step + 3 * self.N + self.nb_controlled_cells + move)
            move_clauses.add_clause(at_least_one_move_clause)
            
            # at most 1 one movement at time step t
            for i,move_1 in enumerate(move_list):
                for move_2 in move_list[i+1:]:
                    move_clauses.add_clause( OR(
                        VAR(t*self.time_step + 3 * self.N + self.nb_controlled_cells + move_1).not_(),
                        VAR(t*self.time_step + 3 * self.N + self.nb_controlled_cells + move_2).not_()
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
                    consequence = VAR(self.time_step + c*3 + BlockState.up)
                    # UP direction
                    if self.can_be_in_state(coord, Movements.up, BlockState.up):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.down_vertical,
                            self.encode_pos[(i+2,j)]*3 + BlockState.down_vertical
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state(coord, Movements.down, BlockState.up):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.down_vertical,
                            self.encode_pos[(i-2,j)]*3 + BlockState.down_vertical
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state(coord, Movements.left, BlockState.up):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.down_horizontal,
                            self.encode_pos[(i,j+2)]*3 + BlockState.down_horizontal
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state(coord, Movements.right, BlockState.up):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.down_horizontal,
                            self.encode_pos[(i,j-2)]*3 + BlockState.down_horizontal
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
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
                        time_gap = t*self.time_step
                        transition_cnf_t = list(map(lambda l: [var+time_gap if var>0 else var-time_gap for var in l], transition_cnf.copy()))
                        for clause in transition_cnf_t:
                            self.conjonctive_clauses.append(self.list_to_str(clause))

                    # transition to block DOWN HORIZONTAL
                    condition = None
                    consequence = VAR(self.time_step + c*3 + BlockState.down_horizontal)
                    # UP direction
                    if self.can_be_in_state(coord, Movements.up, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.down_horizontal
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state(coord, Movements.down, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.down_horizontal
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state(coord, Movements.left, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.up
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if self.is_floor((i,j+2)):
                            alt_cond_ = AND(
                                3 * self.N + self.nb_controlled_cells + Movements.left,
                                self.encode_pos[(i,j+2)]*3 + BlockState.up
                            )
                            if self.has_controls and coord in self.encode_controlled_cells.keys():
                                alt_cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state(coord, Movements.right, BlockState.down_horizontal):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.up
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if self.is_floor((i,j-2)):
                            alt_cond_ = AND(
                                3 * self.N + self.nb_controlled_cells + Movements.right,
                                self.encode_pos[(i,j-2)]*3 + BlockState.up
                            )
                            if self.has_controls and coord in self.encode_controlled_cells.keys():
                                alt_cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
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
                        time_gap = t*self.time_step
                        transition_cnf_t = list(map(lambda l: [var+time_gap if var>0 else var-time_gap for var in l], transition_cnf.copy()))
                        for clause in transition_cnf_t:
                            self.conjonctive_clauses.append(self.list_to_str(clause))
                    
                    # transition to block DOWN VERTICAL
                    condition = None
                    consequence = VAR(self.time_step + c*3 + BlockState.down_vertical)
                    # UP direction
                    if self.can_be_in_state(coord, Movements.up, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.up,
                            self.encode_pos[(i+1,j)]*3 + BlockState.up
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                                cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if self.is_floor((i+2,j)):
                            alt_cond_ = AND(
                                3 * self.N + self.nb_controlled_cells + Movements.up,
                                self.encode_pos[(i+2,j)]*3 + BlockState.up
                            )
                            if self.has_controls and coord in self.encode_controlled_cells.keys():
                                alt_cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # DOWN direction
                    if self.can_be_in_state(coord, Movements.down, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.down,
                            self.encode_pos[(i-1,j)]*3 + BlockState.up
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                                cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if self.is_floor((i-2,j)):
                            alt_cond_ = AND(
                                3 * self.N + self.nb_controlled_cells + Movements.down,
                                self.encode_pos[(i-2,j)]*3 + BlockState.up
                            )
                            if self.has_controls and coord in self.encode_controlled_cells.keys():
                                alt_cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                            cond_ = OR(cond_, alt_cond_)
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # LEFT direction
                    if self.can_be_in_state(coord, Movements.left, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.left,
                            self.encode_pos[(i,j+1)]*3 + BlockState.down_vertical
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
                        if condition is None:
                            condition = OR(cond_)
                        else:
                            condition.add_clause(cond_)
                    # RIGHT direction
                    if self.can_be_in_state(coord, Movements.right, BlockState.down_vertical):
                        cond_ = AND(
                            3 * self.N + self.nb_controlled_cells + Movements.right,
                            self.encode_pos[(i,j-1)]*3 + BlockState.down_vertical
                        )
                        if self.has_controls and coord in self.encode_controlled_cells.keys():
                            cond_.add_clause(VAR(3 * self.N + self.encode_controlled_cells[coord]))
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
                        time_gap = t*self.time_step
                        transition_cnf_t = list(map(lambda l: [var+time_gap if var>0 else var-time_gap for var in l], transition_cnf.copy()))
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