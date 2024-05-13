
import math
from random import randint


class BoardFactory:
    def __init__(self, w: int, h: int, ship_descr: tuple):

        self.w = w
        self.h = h
        self.shipdescr = ship_descr
        self.default_boards = self.get_all_boards_from_shipdescr(self.shipdescr)
        self.boards_containing = {}
        self.miss_cache = {}

        self.populate_boards_containing()

    def add_to_miss_cache(self, beliefs: dict, at_index: int):
        """
        When a series of misses is recorded by the game object, we can save and record its beliefs
        Since a string of misses is very likely (and also very expensive to compute beliefs for)
            this is a very big performance improvement.
        """
        self.miss_cache[at_index] = beliefs.copy()

    def get_random_board(self):
        """
        Draws a random board from the generated boards
        """
        random_index = randint(0, len(self.default_boards))
        return self.default_boards[random_index]

    def populate_boards_containing(self):

        for i in range(0, self.w*self.h):
            self.boards_containing[i] = set()
            for j in range(0, len(self.default_boards)):
                if i in self.default_boards[j]:
                    self.boards_containing[i] |= {j}

    def show_board(self, np_board):
        """
        Print a board (for debugging)
        """
        board = list(np_board)
        i = 0
        while i < self.w:
            print("_"+str(i)+"_", end="")
            i += 1
        print()
        i = 0
        while i < self.w * self.h:
            hit = False
            root = False
            if i in board:
                hit = True
            if (i + 1) % self.w == 0:
                if hit:
                    print(" o |", (math.floor(i/self.w)))
                else:
                    print(" ~ |", (math.floor(i/self.w)))
            elif hit:
                print(" o ", end="")
            else:
                print(" ~ ", end="")
            i += 1
        i = 0
        while i < self.w:
            print("---", end="")
            i += 1
        print()
        print()

    def xy_to_coord(self, t: tuple):
        """
        Convert paired (x,y) coordinate to scalar coordinate
        """
        return (t[1] * self.h) + t[0]

    def coord_to_xy(self, coord: int):
        """
        Convert scalar coordinate to paired (x,y) coordinate
        """
        x = coord % self.w
        y = math.floor(coord / self.w)
        return x, y

    def evaluate_placement(self, ship: int, board_list: list, root: int, direction: int) -> bool:
        """
        Return true if the placement is valid; in-bounds and not colliding
        """
        if root > self.w * self.h - 1:
            # db("Out of bounds completely")
            return False
        if (self.coord_to_xy(root)[1] != self.coord_to_xy(root+ship-1)[1]
                and direction == 0):
            # db("Out of x bounds")
            return False
        if (self.coord_to_xy(root + (self.w * (ship-1)))[1] > self.h - 1
                and direction == 1):
            # db("Out of y bounds")
            return False

        for i in range(0, ship):
            if direction == 0:
                coord = root + i
            elif direction == 1:
                coord = root + (i * self.w)
            else:
                return False

            # collision check
            if coord in board_list:
                return False

        return True

    def find_all_fits(self, ship: int, board_list: list) -> list:
        """
        Given a board and a ship, return all positions where it is
        feasible to add the ship; as a Pylist
        """
        fits = []
        for r in range(0, self.w * self.h):
            for d in (0, 1):
                if self.evaluate_placement(ship, board_list, r, d):
                    fits.append((r, d))
        return fits

    def board_repr(self, root: int, ship: int, direction: int) -> list:
        """
        Given a root, length, dir, return a dense Pylist of coordinate positions
        """
        if direction == 0:
            return [root + i for i in range(0,ship)]
        if direction == 1:
            return [root + (i * self.w) for i in range(0, ship)]

    def get_all_resulting_boards(self, ship: int, board: list) -> list:
        """
        Accepts a ship and a board
        Returns a Pylist of boards which are possible placements for the ship.
        """
        boards = []
        for f in self.find_all_fits(ship, board):
            bship = self.board_repr(f[0], ship, f[1])
            boards += [board + bship]
        return boards

    def get_all_boards_from_shipdescr(self, ship_descr: tuple) -> list:
        """
        Given a tuple of ships, returns a Pylist of all possible boards that fit the ships.
        """
        boards = [[]]
        for s in ship_descr:
            boards_new = []
            for b in boards:
                boards_new += self.get_all_resulting_boards(s,b)
            boards = boards_new
        return boards


