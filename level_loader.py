import numpy as np

LEVELS_PATH = r"levels.txt"

chr_index_dict = {' ':0,
                  '#':1,
                  'X':2,
                  'O':3,
                  '-':4,
                  '|':5}

def map_to_list(string):
    return [chr_index_dict[c] for c in string]

def load_levels(path=LEVELS_PATH):
    file = open(path, mode = 'r', encoding = 'utf-8')
    lines = file.readlines()
    file.close()
    level_dict={}
    current_lvl = None
    current_arr = []
    for line in lines:
        stripped_line = line.split('\n')[0]
        if "level" in stripped_line:
            current_lvl = int(stripped_line.split(' ')[-1])
        else:
            s_length = len(stripped_line)
            if s_length > 0 :
                index_list = map_to_list(stripped_line)
                current_arr.append(index_list)
            elif len(current_arr)>0:
                level_dict[current_lvl] = np.array(current_arr)
                current_arr = []
    if len(current_arr)>0:
                level_dict[current_lvl] = np.array(current_arr)
    return level_dict

def display_level(level_dict, num=None):
    if num is None: # Display all levels
        for lvl_id, lvl_arr in level_dict.items():
            print(f"Level {lvl_id}:")
            print(lvl_arr,'\n')
    else :
        assert num in level_dict.keys()
        print(f"Level {lvl_id}:")
        print(lvl_arr)
        