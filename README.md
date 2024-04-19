battleship_solver
======

BATTLESHIP puts you in the admiral's seat.
--

This project is an extension (and simplification) of work concerning the use of partially observable Markov decision processes (POMDPs) for information leakage games. 
This project is a comparative strategy evaluator for the basic game with customisable boards.
The user selects a strategy and designs their board parameters, and then runs an experiment which automatically applies the strategy to every possible instantiation of the board, and presents statistics. 
Any number of ships of different sizes can be added and the board may be any dimension.

![Experiments being performed](https://github.com/gunass/battleship/blob/main/imgs/exp.png)

![Experiment results](https://github.com/gunass/battleship/blob/main/imgs/exp_results.png)

Optionally, the user can also simply play the game themselves, for fun. 

Run the code using `python3 battleship_solver.py`. 
The UI is adequately user-friendly.

Strategies
--

Four strategies are implemented currently:
- `PMax`: solver guesses the square with the highest probability of containing a ship;
- `PMed`: solver guesses the square with the highest entropy (closest to 50);
- `Rand`: solver guesses a random square with some probability of containing a ship;
- `RandFast`: solver guesses any random square that has not yet been guessed.

The first three strategies rely on the notion of a *belief*, which is a structure related to POMDPs that generalises inference about hidden information. 
To compute beliefs, all possible boards are generated, and their relative probabilities are modified based on new feedback from the system as it arises through user interaction. 
A major result of the supporting work is that when the interactive system under test behaves deterministically, this inference can always be modelled as a set of possible remaining boards, *without losing information about the relative probabilities* of each board position.
As a consequence of this result, automated solving can be highly efficient, as the program shows. 

Future
--

Currently, using 3 ships, boards of approximately 6x6 are the upper limit of tractability for the belief-based strategies.
This is a promising result, since belief computations are intrinsically extremely complex. 
In future work we hope to rewrite the core game-playing engine in C, or leverage the parallelised tensor computations of PyTorch to optimise the generation of beliefs. 
We hope that the code can eventually be used to tractably model full-size Battleship games (10x10) with the full set of ships (2, 3, 3, 4, 5). 
