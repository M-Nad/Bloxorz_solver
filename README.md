# Project: SAT Solver for Bloxorz Level Classification

This project aims to solve levels of the strategy game **Bloxorz** using a SAT solver, specifically **Gophersat**. The objective is to model the game`s rules as logical constraints and then use Gophersat to determine an optimal solution under the constraint of a maximum number of movements.

## Project Description

**Bloxorz** is a game where the player controls a rectangular block that must be moved on a grid to reach a hole. Each move must comply with specific constraints:

- The block cannot fall off the grid.
- The block must end up vertically aligned in the hole to win.
- Certain grid tiles may have switches or obstacles.

This project models these constraints as a SAT problem and uses the **Gophersat** solver to find a valid solution.

<img src=./Images/lvl3solve.gif alt="Level 3" style="width:410px;"/>

*<ins>Example</ins> : Level 3 of the [original game](#additional-resources) (solution in 19 moves found by the solver)*

---

## Key Features

1. **Modeling Bloxorz Rules**:
   - Representation of the grid and block.
   - Encoding movement rules and valid states as logical clauses in conjunctive normal form ([**CNF**](https://en.wikipedia.org/wiki/Conjunctive_normal_form)).

2. **Using Gophersat**:
   - Generating a DIMACS file  (`*.cnf`) containing SAT clauses.
   - Calling the Gophersat solver to solve the planning problem.
   - Analyzing and interpreting the solution to generate the block`s movements.

3. **Simple User Interface**:
   - Loading predefined levels.
   - Visualizing the solution sequences.

---

## Prerequisites

- **Python** (>= 3.8)
- The following Python libraries:
  - `subprocess` (to call Gophersat)
  - `numpy` (to handle grids)
  - `matplotlib` (optional, for a graphical interface)
- SAT Solver: [Gophersat](#additional-resources)

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/bloxorz-sat-solver.git
   cd bloxorz-sat-solver
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the Gophersat binary and place it in the project directory.

---

## Usage

1. Define a Bloxorz level in a JSON file or another appropriate format (see the example in `levels/level_1.json`, or [Example Levels](#example-levels) section).

2. Run the main script:
   ```bash
   python bloxorz_solver.py --level levels/level_1.json
   ```

   <ins>Note #1</ins> : It is possible to use a graphic display istead of the console.

   ```bash
   python bloxorz_solver.py -l levels/level_1.json -g
   ```

   <ins>Note #2</ins> : It is possible to use a graphic display `-g` istead of the Terminal.

   ```bash
   python bloxorz_solver.py -l levels/level_1.json -g
   ```

3. The script generates a DIMACS file and uses Gophersat to solve the level. The solution is displayed as a sequence of moves.

---

## Project Structure

```plaintext
bloxorz-sat-solver/
├── levels/                 # Level definition files
├── solver/                 # Modules for constraint generation and Gophersat calls
├── examples/               # Examples of generated solutions
├── bloxorz_solver.py       # Main script
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## Example Levels

- ### Simple level - **[ Level 1 ]**

Example JSON file for a simple level:

```json
{
   "grid": [
      [1, 1, 1, 0, 0, 0, 0, 0, 0, 0], 
      [1, 1, 1, 1, 1, 1, 0, 0, 0, 0], 
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 0], 
      [0, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
      [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 1, 1, 1, 0]
      ],
   "start": [1, 1],
   "end": [5, 7]
}
```

The solver yields a **7** moves solution :

`RIGHT`, `DOWN`, `RIGHT`, `RIGHT`, `RIGHT`, `DOWN`, `DOWN`

<img src=./Images/lvl1solve_.gif alt="Level 1"/>

---

- ### Advanced level - **[ Level 7 ]**

Example JSON file for a more complex level: 

```json
{
   "grid": [
      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
      [1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1],
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1],
      [1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1],
      [1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1],
      [0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
   ],
   "start": [3, 1],
   "end": [3, 13],
   "controls": {
      "buttons": [
         {
            "position": [4, 9],
            "switch_type": "DUAL",
            "activation": "stand_only",
            "controls": [
               [6, 3]
            ]
         }
      ],
      "controlled_cells": [
         {"position": [6, 3], "state": 0}
      ]
   }
}
```

The solver yields a **47** moves solution :

`DOWN`, `LEFT`, `UP`, `RIGHT`, `RIGHT`, `RIGHT`, `RIGHT`, `RIGHT`, `DOWN`, `RIGHT`, `LEFT`, `UP`, `LEFT`, `LEFT`, `LEFT`, `LEFT`, `LEFT`, `DOWN`, `RIGHT`, `DOWN`, `RIGHT`, `DOWN`, `RIGHT`, `RIGHT`, `RIGHT`, `UP`, `UP`, `RIGHT`, `DOWN`, `LEFT`, `UP`, `RIGHT`, `UP`, `UP`, `RIGHT`, `RIGHT`, `RIGHT`, `DOWN`, `RIGHT`, `DOWN`, `RIGHT`, `DOWN`, `LEFT`, `UP`

<img src=./Images/lvl7solve_.gif alt="Level 7">

---

## Additional Resources

- [Gophersat (repository & documentation)](https://github.com/crillab/gophersat)
- [Bloxorz (original game)](https://www.coolmathgames.com/0-bloxorz)

---

## Authors

- **Marius NADALIN**
- **Antoine DIEU**
