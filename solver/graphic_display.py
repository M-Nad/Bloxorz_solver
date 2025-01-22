import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

colors = ['black', 'grey', 'red', 'yellow', 'yellow', 'yellow', 'orange']
custom_cmap = ListedColormap(colors)
norm = BoundaryNorm([b for b in range(len(colors)+1)], custom_cmap.N)

def display_graphics(arrays, next_moves = None, cmap=custom_cmap, norm=norm, title="Graphical display of solution"):
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

    # Fonction pour mettre à jour la figure lors du déplacement du slider
    def update_plot(frame):
        ax.clear()  # Efface l'axe précédent
        ax.imshow(arrays[frame], cmap=cmap, norm=norm)  # Affiche l'array correspondant
        ax.set_title(f"Step T = {frame} / {len(arrays)-1}", 
                     fontdict={"family":"Courier New", "size": 16},
                     pad=20,
                     color="white")
        ax.set_axis_off()
        ax.set_facecolor("black")
        
        # Mettre à jour l'affichage du prochain mouvement
        if frame < len(next_moves):
            move_label.config(text=f"Next move: {next_moves[frame]}")
        else:
            move_label.config(text="")
        
        canvas.draw()  # Redessine la figure

    # Création de la fenêtre principale Tkinter
    root = tk.Tk()
    root.title(title)
    root.configure(bg="black")

    # Création de la figure Matplotlib
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("black")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()
    
    # Ajout d'un label pour afficher le prochain mouvement
    move_label = tk.Label(root, text="", font=("Courier New", 16), bg="black", fg="white")
    move_label.pack(pady=5)

    # Ajout d'un slider pour naviguer entre les frames
    frame_slider = ttk.Scale(
        root, from_=0, to=len(arrays) - 1, orient="horizontal", 
        command=lambda v: update_plot(int(float(v)))
    )
    frame_slider.pack(fill="x", padx=10, pady=10)

    # Initialisation de la première frame
    update_plot(0)

    # Lancement de la boucle principale Tkinter
    root.mainloop()

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk