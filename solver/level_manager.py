import numpy as np
from solver.cnf_generator import CNF, Movements, BlockState
import json
import os

LEVELS_PATH = r"levels.txt"

chr_index_dict = {' ':0,
                  '#':1,
                  'X':2,
                  'O':3,
                  '-':4,
                  '|':5}
index_chr_dict = {index:chr for chr,index in chr_index_dict.items()}

def is_grid(grid:list[list]):
    if len(grid)>0 and len(grid[0])>0:
        length = len(grid[0])
        for l in grid:
            if len(l) != length:
                return False
        return True
    return False
            
def load_level(path):
    with open(path) as json_file:
        level_dict = json.load(json_file)
        assert is_grid(level_dict['grid'])
        level_dict['level_name'] = os.path.basename(os.path.splitext(path)[0])
        return level_dict

def display_array(arr:np.ndarray):
    h, l = arr.shape
    print("┌" + "─"*l + "┐")
    for i in range(h):
        print("│", end="")
        for j in range(l):
            print(index_chr_dict[arr[i,j]],end="")
        print("│")
    print("└" + "─"*l + "┘")

def display_level(level_dict, num=None):
    if num is None: # Display all levels
        for lvl_id, lvl_arr in level_dict.items():
            print(f"Level {lvl_id}:")
            display_array(lvl_arr)
    else :
        assert num in level_dict.keys()
        print(f"Level {lvl_id}:")
        display_array(lvl_arr)

def convert_vars_to_sequence(var_list:list,cnf:CNF):
    sequence_dict={}
    Tmax = cnf.Tmax
    h, l = cnf.h, cnf.l
    layout_array = cnf.get_level_array().astype(np.int8)
    objective_cells =  [tuple(cell) for cell in np.argwhere(cnf.level_array==2)]
    for cell in objective_cells:
        layout_array[cell] = 2
    index_movements_dict = {
        Movements.up:"UP",
        Movements.down:"DOWN",
        Movements.left:"LEFT",
        Movements.right:"RIGHT"
        }
    index_state_dict = {
        BlockState.up:3,
        BlockState.down_horizontal:4,
        BlockState.down_vertical:5
        }
    layouts = [layout_array.copy() for _ in range(Tmax)]
    movements = [None] * Tmax
    for var in var_list:
        if var>0:
            var_type, args = cnf.decode_var(var)
            match var_type:
                case "direction":
                    t,move = args
                    movements[t] = index_movements_dict[move]
                case "state":
                    t,state,coord = args
                    layouts[t][coord] = index_state_dict[state]
                case _:
                    pass
    sequence_dict={"movement_sequence":movements,
                   "layout_sequence":layouts}
    return sequence_dict

def display_solution(sequence_dict:dict):
    assert "movement_sequence" in sequence_dict.keys()
    assert "layout_sequence" in sequence_dict.keys()
    movements = sequence_dict["movement_sequence"]
    layouts = sequence_dict["layout_sequence"]
    assert len(movements) == len(layouts)
    Tmax = len(movements)
    for t in range(Tmax):
        print(f'T = {t} | Direction : {movements[t]}')
        display_array(layouts[t])