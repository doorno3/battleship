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

        # optimisation to cache initial guesses
        self.achieved_hits = 0
        self.guesses = 0

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

        # Record hits for caching purposes etc.
        if success:
            self.achieved_hits += 1
        self.guesses += 1
        self.filter_beliefs_by_guess(coord, success)
        return success

    def num_satisfying_boards(self):
        return len(self.beliefs)

    def filter_beliefs_by_guess(self, coord: int, success):

        # RandFast strategy does not need to filter beliefs at all (note Rand does here but not probabilistically)
        if self.strategy == 3:
            return

        # Compute superposition of believed states and new observations
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
            # This line of code consumes about 95% of the operational
            # complexity of the program in experiments mode, without caching.
            # Luckily, there is a cache.
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
        using_prob_beliefs = self.strategy not in [2, 3]

        # Check cached beliefs if we are using a belief-based strategy
        # Cache doesn't make sense for randomised strategies
        if using_prob_beliefs and self.guesses in self.bf.miss_cache.keys():
            self.prob_beliefs = self.bf.miss_cache[self.guesses]
            return

        # Do the very expensive computation otherwise
        for g in [c for c in range(self.w * self.h)]:
            self.prob_beliefs[g] = self.guess_chance(g)

        # Cache belief if applicable
        if using_prob_beliefs and self.achieved_hits == 0 and self.guesses not in self.bf.miss_cache.keys():
            self.bf.add_to_miss_cache(self.prob_beliefs, self.guesses)

    def get_best_guess(self) -> int:
        """
        Strategy function which returns a guess
        By default (via constructor) returns coord with closest hit% to 50
        """

        best_g = -1

        if self.strategy == 0:
            # Default strategy: hit percentage closest to 50 "PMed"
            best_q = 50
            for g, p in self.prob_beliefs.items():
                quality = abs(p - 50)
                if quality < best_q:
                    best_q = quality
                    best_g = g

        elif self.strategy == 1:
            # Comparison strategy: hit percentage highest, but under 100, "PMax"
            best_q = -1
            for g, p in self.prob_beliefs.items():
                quality = p
                if best_q < quality < 100:
                    best_q = quality
                    best_g = g

        elif self.strategy == 4:
            # Comparison strategy: hit percentage being lowest, but over 0, "PMin"
            best_q = 100
            for g, p in self.prob_beliefs.items():
                quality = p
                if best_q > quality > 0:
                    best_q = quality
                    best_g = g

        elif self.strategy == 2:
            # Guess a random square not yet guessed "Rand"
            # We still need to track probabilistic beliefs to detect a win
            squares = [g for g in self.prob_beliefs.keys()
                       if g not in self.trace.keys()]
            return squares[randint(0, len(squares) - 1)]

        elif self.strategy == 3:
            # Guess a totally random square regardless of history "RandFast"
            # this strategy never modifies prob_beliefs hence "Fast"
            # it therefore requires fully sinking all ships
            return randint(0, (self.w * self.h)-1)

        return best_g

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
        while not (self.detect_il_win() or self.detect_hit_win()):
            # for ultrafine debugging:
            #self.show_board_beliefs()

            self.real_hit(self.get_best_guess())
        return self.guesses

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
