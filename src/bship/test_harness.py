
from bship_board_factory import BoardFactory as bf
from bship_game import BShipGame as bg

from random import randint

class TestHarness:

    # Board dimensions and ship description
    large_w = 5
    large_h = 5
    large_shipdescr = (2,3,4)

    # Actual Battleship dimensions (extremely complex)
    battleship_w = 10
    battleship_h = 10
    battleship_shipdescr = (2,3,3,4,5)

    # Affects output logging
    verbose = True

    def test_automatic(self, width, height, shipdescr, coverage_pct=50, randomise=False, strategy=0):

        print(f'Generating with w={width},h={height},ships={shipdescr},'
              +f'coverage={coverage_pct}%,rand={randomise},strat={strategy}')

        if width > 8 or height > 8:
            print(f"Detected a large board ({width}x{height}). This may take some time to generate.",
                  "\nThe upper bound on the number of boards is roughly", (width*height)**len(shipdescr))

        factory = bf(width,height,shipdescr)

        all_boards = factory.get_all_boards_from_shipdescr(shipdescr)
        num_boards = len(all_boards)
        print(f'{num_boards} boards generated. '
              +f'{int(num_boards * (coverage_pct/100))} to test.')
        performance_list = []
        subsample = int(100 / coverage_pct)

        for i in range(0,num_boards,subsample):
            print(f'Evaluating board {i:>8d}...',end="")

            if randomise:
                b = factory.get_random_board()
            else:
                b = all_boards[i]

            try:
                the_game = bg(b,factory,strategy)
                perf = the_game.autoplay()
                performance_list.append(perf)
                print(f'({perf:>2d})')
                i += 1

            except KeyboardInterrupt:
                print("Terminated by user.")
                break
            except IndexError:
                print("IndexError resulted from board number ", i)
                break

        print("Mean number of guesses:",
              round((sum(performance_list)/len(performance_list)),2))


harness = TestHarness()
# Do a basic test of the game/generation logic to make sure things appear ok
harness.test_automatic(harness.battleship_w, harness.large_h, harness.large_shipdescr, 10)



