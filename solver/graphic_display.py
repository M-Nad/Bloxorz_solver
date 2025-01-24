import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps, ImageDraw
import numpy as np

color_mapping = {0 : [0, 0, 0],  # Black
                 1 : [128, 128, 128],  # Grey
                 2 : [255, 0, 0],  # Red
                 3 : [255, 255, 0],  # Yellow
                 4 : [255, 255, 0],  # Yellow
                 5 : [255, 255, 0],  # Yellow
                 6 : [255, 165, 0],  # Orange
                 7 : [128, 128, 128],  # Grey
                 8 : [128, 128, 128], # Grey
                 9 : [50,205,50]} # Green

color_mapping_bis = color_mapping.copy()
color_mapping_bis[1] = [110, 110, 110]  # Darker Grey
color_mapping_bis[6] = [235, 155, 0]  # Darker Orange
color_mapping_bis[7] = [110, 110, 110]  # Darker Grey
color_mapping_bis[8] = [110, 110, 110]  # Darker Grey

def f_colorizer(arg):
    x, color_switch = arg
    return color_mapping[int(x)] if color_switch else color_mapping_bis[int(x)]

def draw_x_button(draw, x, y, scale, outline_color):
    # Draw an 'x' marker on the array (e.g., at pixel (3, 4))
    marker_x, marker_y = x*scale + scale//2, y*scale + scale//2 
    marker_size = scale//2 - 2  # Size of the 'x' arms
    draw.line(
        [(marker_x - marker_size-1, marker_y - marker_size-1), (marker_x + marker_size, marker_y + marker_size)],
        fill=outline_color,  # Line color for the first diagonal
        width=2  # Line thickness
    )
    draw.line(
        [(marker_x - marker_size, marker_y + marker_size), (marker_x + marker_size+1, marker_y - marker_size-1)],
        fill=outline_color,  # Line color for the second diagonal
        width=2  # Line thickness
    )
    
def draw_o_button(draw, x, y,  scale, fill_color, outline_color):
    pixel_x, pixel_y = x*scale + scale//2, y*scale + scale//2  # Coordinates for the circle's center
    radius = scale//2-1  # Circle radius in pixels
    draw.ellipse(
    (pixel_x - radius, pixel_y - radius, pixel_x + radius, pixel_y + radius),
    outline=outline_color,  # Circle outline color
    fill=fill_color,  # Circle fill color
    width=1  # Thickness of the circle outline
    )
    
def draw_cell_outline(draw, x, y,  width, scale, outline_color):
    pixel_x, pixel_y = x*scale, y*scale
    pixel_x_, pixel_y_ = (x+1)*scale, (y+1)*scale
    draw.rectangle(
    (pixel_x, pixel_y, pixel_x_, pixel_y_),
    outline=outline_color,  # outline color
    width=width  # Thickness of the outline
    )

def display_graphics(arrays, next_moves = None, title="Graphical display of solution"):
    """
    Affiche une liste de tableaux numpy 2D dans une interface graphique avec un slider.

    Args:
        arrays (list of numpy.ndarray): Liste de tableaux 2D à afficher.
        cmap (str): Colormap à utiliser pour l'affichage.
        title (str): Titre de la fenêtre.
    """
    
    if not arrays:
        raise ValueError("La liste des tableaux est vide.")
    
    if next_moves is None:
        # Si next_moves n'est pas donné, on remplit par des chaînes vides
        next_moves = [""] * (len(arrays) - 1)
    
    if len(next_moves) != len(arrays) - 1:
        raise ValueError("La longueur de next_moves doit être égale à len(arrays) - 1.")
    
    # Check that all arrays have the same shape
    array_shape = arrays[0].shape
    for array in arrays:
        if array.shape != array_shape:
            raise ValueError("Tous les tableaux doivent avoir la même forme.")
    
    cross_pattern = np.fromfunction(lambda i, j: (i + j) % 2, array_shape, dtype=int).astype(bool)
    
    button_outline_color = (0,0,150)
    button_fill_color = (51,51,255)
    
    # Création de la fenêtre principale Tkinter
    root = tk.Tk()
    root.title(title)
    root.configure(bg="black")
    
    # Dimensions par défaut de la fenêtre
    root.geometry("500x400")  # Largeur x Hauteur
    
    # Configure grid layout
    root.grid_rowconfigure(1, weight=1)  # Make the image row expandable
    root.grid_columnconfigure(0, weight=1)  # Allow horizontal resizing
    
    # Ajout d'un label pour afficher l'étape T
    step_label = tk.Label(root, 
                          text="", 
                          font=("Courier New", 16),
                          bg="black", 
                          fg="white")
    step_label.grid(row=0, column=0, pady=10, sticky="n")  # Sticky 'n' keeps it at the top center

    # Image Label (inside a frame to handle resizing properly)
    image_frame = tk.Frame(root, bg="black")
    image_frame.grid(row=1, column=0, sticky="nsew")  # Expand to fill available space
    image_label = tk.Label(image_frame, bg="black")
    image_label.pack(fill="both", expand=True)
    
    # Ajout d'un label pour afficher le prochain mouvement
    move_label = tk.Label(root, 
                          text="", 
                          font=("Courier New", 16), 
                          bg="black", 
                          fg="white")
    move_label.grid(row=2, column=0, pady=5, sticky="n")  # Fixed below the image
    
    # Slider Frame
    slider_frame = tk.Frame(root, bg="black")
    slider_frame.grid(row=3, column=0, pady=10, sticky="ew")  # Slider spans horizontally
    root.grid_rowconfigure(3, weight=0)  # Make sure the slider does not expand
    
    # Label pour afficher les matrices
    image_label = tk.Label(image_frame, bg="black")  # Fond noir
    image_label.pack(fill="both", expand=True)

    # Fonction pour mettre à jour l'affichage en fonction de la valeur du slider
    def update_image(index):
        index = int(float(index))  # Convertit la valeur en entier
        array = arrays[index]

        # Convertit l'array en image
        concat_arr = np.concatenate([array[:, :, np.newaxis], cross_pattern[:, :, np.newaxis]],axis=2)
        array_3d = np.apply_along_axis(f_colorizer, 2, concat_arr)
        arr_rgb = np.array([tuple(row) for row in array_3d.reshape(-1, array_3d.shape[-1])], dtype=[('r', 'u1'), ('g', 'u1'), ('b', 'u1')]).reshape(array.shape)

        image = Image.fromarray(arr_rgb, 'RGB')
        SCALE = 11
        image = image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST)
        
        draw = ImageDraw.Draw(image)
        
        for coord in np.argwhere(array == 2):
            y, x = coord
            draw_cell_outline(draw, x, y, 2, SCALE, 'black')
        
        for coord in np.argwhere(array == 7):
            y, x = coord
            draw_x_button(draw, x, y, SCALE, button_outline_color)
            
        for coord in np.argwhere(array == 8):
            y, x = coord
            draw_o_button(draw, x, y,  SCALE, button_fill_color, button_outline_color)
        
        # Ajout de bordures noires
        image_with_border = ImageOps.expand(image, border=10, fill="black")

        # Get the current size of the image label
        label_width = image_label.winfo_width()
        label_height = image_label.winfo_height()

        # Ensure label dimensions are greater than 0
        if label_width <= 0 or label_height <= 0:
            return  # Exit early if label size is invalid

        # Calculate the aspect ratio of the image and label
        img_width, img_height = image_with_border.size
        img_aspect = img_width / img_height
        label_aspect = label_width / label_height

        # Adjust size to fit the label while maintaining aspect ratio
        if img_aspect > label_aspect:  # Fit to width
            new_width = label_width
            new_height = int(new_width / img_aspect)
        else:  # Fit to height
            new_height = label_height
            new_width = int(new_height * img_aspect)

        # Ensure the new dimensions are greater than 0
        if new_width <= 0 or new_height <= 0:
            return  # Exit early if calculated dimensions are invalid
        
        # Redimensionner l'image pour qu'elle s'adapte à la fenêtre
        resized_image = image_with_border.resize((new_width, new_height), Image.NEAREST)

        # Mise à jour de l'image dans Tkinter
        tk_image = ImageTk.PhotoImage(resized_image)
        image_label.config(image=tk_image)
        image_label.image = tk_image  # Prévention du garbage collector
        
        step_label.config(text=f"Step T = {index} / {len(arrays)-1}")
        
        # Mettre à jour l'affichage du prochain mouvement
        if index < len(next_moves):
            move_label.config(text=f"Next move: {next_moves[index]}")
        else:
            move_label.config(text="FINISHED")

    # Slider Widget
    slider = ttk.Scale(
        slider_frame,
        from_=0,
        to=len(arrays) - 1,
        orient="horizontal",
        command=update_image
        )
    slider.pack(fill="x", padx=10)
    
    # Handle resizing of the window to adjust the image size dynamically
    def on_resize(event):
        current_index = int(slider.get())
        update_image(current_index)

    root.bind("<Configure>", on_resize)  # Call on_resize whenever the window is resized

    # Initialisation de la première frame
    update_image(0)

    # Lancement de la boucle principale Tkinter
    root.mainloop()