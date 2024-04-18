from PyQt6.QtCore import QAbstractListModel, QModelIndex, QVariant, QAbstractItemModel, QStringListModel, pyqtSignal, \
    QObject
from PyQt6.QtWidgets import QListView, QPushButton, QDialog, QVBoxLayout, QLabel

from bship_board_factory import BoardFactory
from bship_game import BShipGame

import threading
from time import perf_counter

HEIGHT_DEFAULT = 5
WIDTH_DEFAULT = 5
SHIPS_DEFAULT = ["3","4", "5"]

UI_UPDATE_STAGGER = 10

class ExperimentThread(threading.Thread):

    def __init__(self, bf, strat,
                 hit_signal, miss_signal,
                 experiment_complete_signal, experiment_aborted_signal,
                 experiment_rerender_signal, experiment_update_signal):
        super().__init__()
        self._stop_event = threading.Event()
        self._stop_showing_event = threading.Event()
        self.bf = bf
        self.strat = strat
        self.hit_signal = hit_signal
        self.miss_signal = miss_signal
        self.exp_complete_signal = experiment_complete_signal
        self.exp_aborted_signal = experiment_aborted_signal
        self.exp_rerender_signal = experiment_rerender_signal
        self.exp_update_progress_signal = experiment_update_signal

    def stop(self):
        self._stop_event.set()

    def start_showing(self):
        self._stop_showing_event.clear()

    def stop_showing(self):
        self._stop_showing_event.set()
        self.exp_rerender_signal.emit()

    def run(self):
        self.run_exp()

    def run_exp(self):
        scores = []
        i = 0
        for board in self.bf.default_boards:
            bg = BShipGame(board, self.bf, self.strat)
            exp_score = 0
            i += 1
            while (self.strat == 3 and not bg.detect_hit_win()) or (self.strat != 3 and not bg.detect_il_win()):
                g = bg.get_best_guess()
                exp_score += 1
                hit_succ = bg.real_hit(g)

                # Display guesses live, in the main thread
                if not (self._stop_showing_event.is_set()):
                    if hit_succ:
                        self.hit_signal.emit(g)
                    else:
                        self.miss_signal.emit(g)
                scores.append(exp_score)

            if not (self._stop_showing_event.is_set()):
                self.exp_rerender_signal.emit()

            # Staggered output to not overwhelm event loop and slow down UI responsiveness
            if i % UI_UPDATE_STAGGER == 0:
                self.exp_update_progress_signal.emit(i)

            if self._stop_event.is_set():
                break

        if len(scores) == 0:
            # exp failed
            return
        avgscore = sum(scores) / len(scores)

        if self._stop_event.is_set():
            self.exp_aborted_signal.emit()
        else:
            self.exp_complete_signal.emit(avgscore)


class BShipModel(QObject):

    hit_signal = pyqtSignal(int)
    miss_signal = pyqtSignal(int)
    int_game_created_success = pyqtSignal()
    int_game_reset_success = pyqtSignal()
    win_signal = pyqtSignal()

    experiment_started_signal = pyqtSignal(int)
    experiment_rerender_signal = pyqtSignal()
    experiment_complete_signal = pyqtSignal(float)
    experiment_failed_signal = pyqtSignal()
    experiment_aborted_signal = pyqtSignal()
    experiment_score_signal = pyqtSignal(int)
    experiment_update_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.ships = QStringListModel()
        self.ships_list = SHIPS_DEFAULT
        self.ships.setStringList(self.ships_list)

        self.width = WIDTH_DEFAULT
        self.height = HEIGHT_DEFAULT

        self.par = 0
        self.score = 0

        self.current_tab = 0

        self.strategies = QStringListModel()
        self.strategies_list = ["PMax", "PMed", "Rand", "RandFast"]
        self.strategies.setStringList(self.strategies_list)
        self.strategy = "PMax"

        self.show_board = True # Each of these are currently stubs
        self.show_heatmap = False
        self.show_visualise = False

        self.widgets = {}

        self.bg = None
        self.bf = None
        self.exp = None

        self.boards_n = 0

        self.exp_start_time = 0
        self.exp_complete_time = 0

        self.experiment_complete_signal.connect(self.on_experiment_complete)

    def on_add_ship(self):
        desired_size = self.widgets["ShipsSizeEntry"].value()
        ships_strings = self.ships.stringList()
        self.ships.setStringList(ships_strings + [str(desired_size)])

    def on_del_ship(self):
        ships_view = self.widgets["ShipsColumnView"]
        assert isinstance(ships_view, QListView)
        for r in ships_view.selectedIndexes():
            self.ships.removeRow(r.row())


    def on_tab_changed(self, tab_index):
        print("Tab changed to", tab_index)
        self.current_tab = tab_index

    def on_width_changed(self, new_w):
        print("Width changed to ", new_w)
        self.width = new_w
        self.widgets["InteractiveGamebox"].populate()
        self.widgets["ExperimentsGamebox"].populate()
        if self.bg:
            self.reset_game()

    def on_height_changed(self,new_h):
        print("Height changed to ", new_h)
        self.height = new_h
        self.widgets["InteractiveGamebox"].populate()
        self.widgets["ExperimentsGamebox"].populate()
        if self.bg:
            self.reset_game()

    def on_show_heat_changed(self, new_sh):
        print("Heatmap bool changed to ", new_sh)
        self.show_heatmap = new_sh

    def on_show_vis_changed(self, new_vs):
        print("Vis bool changed to ", new_vs)
        self.show_visualise = new_vs

    def on_stop_pressed(self):
        print("Stop pressed")

    def on_strategy_changed(self, strat):
        print("Strategy changed to", strat)
        self.strategy = strat

    def on_show_changed(self, value: bool):
        self.show_board = value
        if self.exp and self.exp.is_alive():
            if value:
                self.exp.start_showing()
            else:
                self.exp.stop_showing()

    def translate_strategy(self, text_strat):
        if text_strat == "PMed":
            return 0
        elif text_strat == "PMax":
            return 1
        elif text_strat == "Rand":
            return 2
        elif text_strat == "RandFast":
            return 3

    def on_go_pressed(self):

        print("GO has been pressed. Current params:")
        print(f"w={self.width},h={self.height},tab={self.current_tab},ships={self.ships.stringList()},")

        try:
            rb = self.widgets["ResetButton"]
            gb = self.widgets["GoButton"]
            rb.show()
            gb.hide()

            if self.current_tab == 0:

                self.widgets["InteractiveGamebox"].on_game_started()
                self.bf = BoardFactory(self.width, self.height, tuple(int(i) for i in self.ships.stringList()))
                self.bg = BShipGame(self.bf.get_random_board(), self.bf, self.translate_strategy(self.strategy))
                bgp = BShipGame(self.bg.ships, self.bf, 0)
                self.score = 0
                self.par = bgp.autoplay()
                self.int_game_created_success.emit()

            if self.current_tab == 1:
                self.widgets["ExperimentsGamebox"].on_game_started()
                self.bf = BoardFactory(self.width, self.height, tuple(int(i) for i in self.ships.stringList()))
                strat = self.translate_strategy(self.strategy)

                self.exp = ExperimentThread(self.bf, strat, self.hit_signal, self.miss_signal,
                                            self.experiment_complete_signal, self.experiment_aborted_signal,
                                            self.experiment_rerender_signal, self.experiment_update_signal)

                if not self.show_board:
                    self.exp.stop_showing()
                self.exp.start()
                self.boards_n = len(self.bf.default_boards)
                self.experiment_started_signal.emit(self.boards_n)
                self.exp_start_time = perf_counter()
                if not self.show_board:
                    self.exp.stop_showing()

        except IndexError:
            print("Encountered an error, board is badly set up?")
            self.reset_game()

    def on_experiment_complete(self):
        self.exp_complete_time = perf_counter()
        self.reset_game()

    def reset_game(self):
        print("Game reset.")
        rb = self.widgets["ResetButton"]
        gb = self.widgets["GoButton"]
        rb.hide()
        gb.show()

        # call directly -- who cares
        self.widgets["InteractiveGamebox"].on_game_terminated()
        self.widgets["ExperimentsGamebox"].on_game_terminated()

        self.bf = None
        self.bg = None
        self.score = 0
        self.par = 0
        self.int_game_reset_success.emit()

    def on_reset_pressed(self):
        print("RESET has been pressed.")
        if self.exp and self.exp.is_alive():
            self.exp.stop()
        self.reset_game()


    def on_game_button_pressed(self, scalar_coord):
        print("Gamebox button",scalar_coord,"pressed")
        if (not self.bf) or (not self.bg):
            return None
        self.score += 1
        if self.bg.real_hit(scalar_coord):
            self.hit_signal.emit(scalar_coord)
        else:
            self.miss_signal.emit(scalar_coord)

        if self.bg.detect_il_win():
            self.win_signal.emit()
            self.reset_game()









