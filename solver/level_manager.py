import numpy as np
from solver.cnf_generator import CNF, Movements, BlockState
from solver.graphic_display import display_graphics
import json
import os


LEVELS_PATH = r"levels.txt"

chr_index_dict = {' ':0,
                  '#':1,
                  'X':2,
                  'O':3,
                  '-':4,
                  '|':5,
                  '@':6,
                  'x':7,
                  'o':8,
                  '%':9}

index_chr_dict = {index:chr for chr,index in chr_index_dict.items()}

def is_grid(grid:list[list]):
    if len(grid)>0 and len(grid[0])>0:
        length = len(grid[0])
        for l in grid:
            if len(l) != length:
                return False
        return True
    return False
            
def load_level(path, verbose=True):
    try:
        with open(path) as json_file:
            level_dict = json.load(json_file)
            check_format(level_dict)
            level_dict['level_name'] = os.path.basename(os.path.splitext(path)[0])
            return level_dict

    except json.JSONDecodeError as e:
        if verbose:
            print("--- JSON DECODE ERROR ---")
            print("Error decoding JSON:", path)
            print("JSON decode error:", e)
        return -1 # Stop iterations
    
    except AssertionError as e:
        if verbose:
            print("--- JSON CONTENT ERROR ---")
            print("Value 'grid' contains size inconsistencies")
        return -1 # Stop iterations

    except KeyError as e:
        if verbose:
            print("--- JSON KEY ERROR ---")
            print(f"Missing key: {e}")
        return -1 # Stop iterations
    
def check_format(level_dict:dict):
    for key in ['grid', 'start', 'end']:
        if key not in level_dict.keys():
            raise KeyError(key)

    if 'controls' in level_dict.keys():
        for key in ['buttons', 'controlled_cells']:
            if key not in level_dict['controls'].keys():
                raise KeyError(key)
            if key == 'buttons':
                for button_dict in level_dict['controls']['buttons']:
                    for key in ['position', 'switch_type', 'activation', 'controls']:
                        if key not in button_dict.keys():
                            raise KeyError(key)
            elif key == 'controlled_cells':
                for controlled_cells_dict in level_dict['controls']['controlled_cells']:
                    for key in ['position', 'state']:
                        if key not in controlled_cells_dict.keys():
                            raise KeyError(key)

    if 'red_grid' in level_dict.keys():
        assert is_grid(level_dict['red_grid'])

    assert is_grid(level_dict['grid'])

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
    objective_cell = cnf.get_level_end()
    layout_array[objective_cell] = 2
    level_red_grid = cnf.get_level_red_grid()
    if level_red_grid is not None:
        layout_array[level_red_grid] = 6
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
    base_layout_array = layout_array.copy()
    if cnf.has_controls:
        sequence_dict["activation_status"] = [{} for _ in range(Tmax)]
        for button in cnf.buttons:
            coord, activation_type = tuple(button["position"]), button["activation"]
            match activation_type:
                case "any_pos":
                    base_layout_array[coord] = 8
                case "stand_only":
                    base_layout_array[coord] = 7
                case _:
                    pass
    sequence_dict["layout_sequence"] = [base_layout_array.copy() for _ in range(Tmax)]
    sequence_dict["movement_sequence"] = [None] * Tmax
            
    for var in var_list:
        if var!=0:
            var_type, args = cnf.decode_var(var)
            match var_type:
                case "direction":
                    t,move = args
                    sequence_dict["movement_sequence"][t] = index_movements_dict[move]
                case "state":
                    t,state,coord = args
                    sequence_dict["layout_sequence"][t][coord] = index_state_dict[state]
                case "controlled_cell_ON":
                    t,coord = args
                    if sequence_dict["layout_sequence"][t][coord] < 2 : # no block state overlapping
                        sequence_dict["layout_sequence"][t][coord] = 9
                    sequence_dict["activation_status"][t][coord] = "ON"
                case "controlled_cell_OFF":
                    t,coord = args
                    if sequence_dict["layout_sequence"][t][coord] < 2 : # no block state overlapping
                        sequence_dict["layout_sequence"][t][coord] = 0
                    sequence_dict["activation_status"][t][coord] = "OFF"
                case _:
                    pass
    return sequence_dict

def display_solution(sequence_dict:dict, graphical_display=True):
    assert "movement_sequence" in sequence_dict.keys()
    assert "layout_sequence" in sequence_dict.keys()
    movements = sequence_dict["movement_sequence"]
    layouts = sequence_dict["layout_sequence"]
    activation_status = None
    if "activation_status" in sequence_dict.keys():
        activation_status = sequence_dict["activation_status"]
    assert len(movements) == len(layouts)
    Tmax = len(movements)
    if graphical_display:
        display_graphics(layouts, movements[:-1])
    else:
        for t in range(Tmax):
            print(f'T = {t} | Direction : {movements[t]}')
            if activation_status is not None:
                print("Controlled cells status :", activation_status[t])
            display_array(layouts[t])