import numpy as np
from solver.cnf_generator import CNF, Movements, BlockState
import json
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import ListedColormap


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
    objective_cell = cnf.get_level_end()
    layout_array[objective_cell] = 2
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

def display_solution(sequence_dict:dict, graphical_display=True):
    assert "movement_sequence" in sequence_dict.keys()
    assert "layout_sequence" in sequence_dict.keys()
    movements = sequence_dict["movement_sequence"]
    layouts = sequence_dict["layout_sequence"]
    assert len(movements) == len(layouts)
    Tmax = len(movements)
    if graphical_display:
        # The parametrized function to be plotted
        def f(i):
            return layouts[int(i)]

        colors = ['black', 'grey', 'red', 'yellow', 'yellow', 'yellow']
        cmap = ListedColormap(colors)
        
        bounds = [0, 1, 2, 3, 4, 5]  # Une limite supplémentaire pour inclure le dernier intervalle
        norm = plt.matplotlib.colors.BoundaryNorm(bounds, cmap.N)

        
        # Create the figure and the line that we will manipulate
        fig, ax = plt.subplots()
        ax.set_axis_off()
        im = ax.imshow(f(0), interpolation='nearest', cmap=cmap, norm=norm)

        # adjust the main plot to make room for the sliders
        fig.subplots_adjust(left=0.25)

        # Make a vertically oriented slider to control the amplitude
        ax_t = fig.add_axes([0.1, 0.25, 0.0225, 0.63])
        t_slider = Slider(
            ax=ax_t,
            label="Step",
            valmin=0,
            valmax=Tmax-1,
            valinit=0,
            valstep=1,
            orientation="vertical"
        )

        # The function to be called anytime a slider's value changes
        def update(val):
            im = ax.imshow(f(val), interpolation='none', cmap=cmap, norm=norm)
            fig.canvas.draw_idle()

        # register the update function with each slider
        t_slider.on_changed(update)

        # Create a matplotlib.widgets.Button to reset the sliders to initial values.
        resetax = fig.add_axes([0.8, 0.025, 0.1, 0.04])
        button = Button(resetax, 'Reset', hovercolor='0.975')

        def reset(event):
            t_slider.reset()
        button.on_clicked(reset)

        plt.show()
    else:
        for t in range(Tmax):
            print(f'T = {t} | Direction : {movements[t]}')
            display_array(layouts[t])