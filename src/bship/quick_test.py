

from bship_board_factory import BoardFactory
from bship_game import BShipGame

bf = BoardFactory(3, 3, (2, 3))
bg = BShipGame(bf.get_random_board(), bf)

score = bg.autoplay()
print("Score =", score)
print("Board was :", bg.ships)
