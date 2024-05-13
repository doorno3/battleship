from random import randint

from bship_board_factory import BoardFactory


class BShipGame:
    """
    One instance of a Battleship game
    """

    def __init__(self, ships: list, bf: BoardFactory, strategy: int = 0):
        # dimensions and ships
        self.w = bf.w
        self.h = bf.h
        self.shipdescr = bf.shipdescr

        # "actual" board being guessed: a list of ints
        self.ships = ships

        # trace of guesses
        self.trace = {}
        self.prob_beliefs = {}

        # board factory object
        self.bf = bf

        # set of candidate board indices
        self.beliefs = set(range(0, len(bf.default_boards)))

        # strategy (see get_best_guess())
        self.strategy = strategy

        self.update_prob_beliefs()

    def test_hit(self, coord: int):
        """
        Reveal whether guess is a hit
        """
        return coord in self.ships

    def real_hit(self, coord: int):
        """
        Make a guess; update trace; filter candidates by new information
        """
        success = self.test_hit(coord)
        self.trace[coord] = success
        self.filter_beliefs_by_guess(coord, success)
        return success

    def num_satisfying_boards(self):
        return len(self.beliefs)

    def filter_beliefs_by_guess(self, coord: int, success):

        if self.strategy == 3:
            return

        if success:
            self.beliefs = self.beliefs & self.bf.boards_containing[coord]
        else:
            self.beliefs = self.beliefs - self.bf.boards_containing[coord]
        self.update_prob_beliefs()

    def guess_data(self, coord: int) -> tuple:
        """
        calculate expected proportions of hits and misses
        """
        n = self.num_satisfying_boards()
        if self.strategy == 3:
            n_hits = n - 1
        else:
            n_hits = len(self.bf.boards_containing[coord] & self.beliefs)
        n_misses = n - n_hits
        return n, n_hits, n_misses

    def guess_chance(self, coord: int) -> float:
        """
        Return a float (0 <= x <= 100) percentage chance of hit at coord
        """
        n, n_hits, n_misses = self.guess_data(coord)
        pct = ((n_hits / n) * 100)
        return pct

    def update_prob_beliefs(self) -> None:
        """
        fill probabilistic beliefs with guess probabilities
        """
        for g in [c for c in range(self.w * self.h)]:
            self.prob_beliefs[g] = self.guess_chance(g)

    def get_best_guess(self) -> int:
        """
        Strategy function which returns a guess
        By default (via constructor) returns coord with closest hit% to 50
        """
        if self.strategy == 0:
            # Default strategy: hit% closest to 50 "PMed"
            best_g = -1
            best_q = 50
            for g, p in self.prob_beliefs.items():
                quality = abs(p - 50)
                if quality < best_q:
                    best_q = quality
                    best_g = g
            return best_g

        elif self.strategy == 1:
            # Comparison strategy: hit% highest "PMax"
            best_g = -1
            best_q = -1
            for g, p in self.prob_beliefs.items():
                quality = p
                if best_q < quality < 100:
                    best_q = quality
                    best_g = g
            return best_g

        elif self.strategy == 4:
            # Comparison strategy: hit% lowest "PMin"
            best_g = 100
            best_q = 100
            for g, p in self.prob_beliefs.items():
                quality = p
                if best_q > quality > 0:
                    best_q = quality
                    best_g = g
            return best_g

        elif self.strategy == 2:
            # Guess a random square not yet guessed "Rand/RandFast"
            squares = [g for g, p in self.prob_beliefs.items()
                       if g not in self.trace.keys()]
            return squares[randint(0, len(squares) - 1)]

        elif self.strategy == 3:
            squares = [g for g, p in self.prob_beliefs.items()
                       if g not in self.trace.keys()]
            if len(squares) == 0:
                return 0
            return squares[randint(0, len(squares) - 1)]

        else:
            print("Incompatible strategy, error...")
            return -1

    def detect_il_win(self) -> bool:
        """
        True if all squares have known (deduced) contents
        """
        for g, p in self.prob_beliefs.items():
            if 0 < p < 100:
                return False
        return True

    def detect_hit_win(self) -> bool:
        """
        True if all ships have been destroyed
        """
        w = (sum(self.shipdescr)
             == len([i for i in self.trace.items() if i[1]]))
        return w

    def autoplay(self) -> int:
        """
        Loops making guesses and adjusting beliefs until win condition
        """
        guesses = 0
        while not (self.detect_il_win() or self.detect_hit_win()):
            # for ultrafine debugging:
            #self.show_board_beliefs()

            self.real_hit(self.get_best_guess())
            guesses += 1
        return guesses

    def show_board_beliefs(self) -> None:
        """
        Print a board with beliefs
        """
        best_guess = self.get_best_guess()
        i = 0
        while i < self.w:
            print("__" + str(i) + "__", end="")
            i += 1
        print()
        i = 0
        while i < self.w * self.h:
            if i in self.trace.keys():
                if self.trace[i]:
                    printchar = "  X  "
                else:
                    printchar = "  O  "
            else:
                pct = self.prob_beliefs[i]
                if i != best_guess:
                    printchar = f' {pct:3.0f} '
                else:
                    printchar = f'>{pct:3.0f}<'

            print(printchar, end="")
            if i % self.w == self.w - 1:
                print(f'| {int(i / self.w)}')
            i += 1
        i = 0
        while i < self.w:
            print("-----", end="")
            i += 1
        print()

        print("Best guess:", best_guess)
