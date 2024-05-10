
import sys
import math

from PyQt6.QtCore import Qt, pyqtSignal

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTabWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QGridLayout, QLabel, QScrollArea, QLineEdit, QSpinBox, QCheckBox, QFrame,
                             QToolBar, QColumnView, QProgressBar, QComboBox, QListWidget, QListView, QAbstractItemView,
                             QDialog)

from battleship_model import BShipModel
from bship_game import BShipGame

model = BShipModel()
HEIGHT_DEFAULT = 5
WIDTH_DEFAULT = 5
INTERACTIVE_INDEX = 0
EXPERIMENTS_INDEX = 1

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BShip")

        self.opts = OptsWidget()
        self.tabs = TabWidget()

        self.superframe = QFrame()
        self.superlayout = QHBoxLayout()
        self.superframe.setLayout(self.superlayout)

        self.superlayout.addWidget(self.opts)
        self.superlayout.addWidget(self.tabs)

        self.setCentralWidget(self.superframe)

        # For UI tweaking. Remove for default OS style
        #self.setStyleSheet("border: 1px solid red")

        model.win_signal.connect(self.win_diag)
        model.experiment_complete_signal.connect(self.on_exp_complete)

    def win_diag(self):
        diag = QDialog()
        diag.setLayout(QVBoxLayout())
        diag.layout().addWidget(QLabel("All positions deducible."))
        diag.layout().addWidget(DynamicScoreLabel())
        exit_button = QPushButton("Ok cool")
        diag.layout().addWidget(exit_button)
        exit_button.pressed.connect(diag.close)
        diag.exec()

    def on_exp_complete(self, avgscore, maxscore):
        diag = QDialog()
        diag.setLayout(QVBoxLayout())
        diag.layout().addWidget(QLabel("Experiment complete!"))
        diag.layout().addWidget(QLabel("Number of tests = "+f'{model.boards_n:d}'))
        diag.layout().addWidget(QLabel("Average score = "+f'{avgscore:.2f}'))
        diag.layout().addWidget(QLabel("Maximum score = "+f'{maxscore:.2f}'))

        total_time = model.exp_complete_time - model.exp_start_time
        per_exp_time = total_time / model.boards_n
        diag.layout().addWidget(QLabel("Total time = "+f'{total_time:.5f}'))
        diag.layout().addWidget(QLabel("Average time = "+f'{per_exp_time:.5f}'))

        exit_button = QPushButton("Ok cool")
        diag.layout().addWidget(exit_button)
        exit_button.pressed.connect(diag.close)
        diag.exec()


class TabWidget(QTabWidget):
    # stub
    def __init__(self):
        super().__init__()
        int_tab = InteractiveTab()
        exp_tab = ExperimentTab()
        self.addTab(int_tab, "Play")
        self.addTab(exp_tab, "Test")

        self.currentChanged.connect(model.on_tab_changed)
        model.experiment_started_signal.connect(self.on_experiment_start)
        model.experiment_complete_signal.connect(self.on_experiment_end)
        model.experiment_aborted_signal.connect(self.on_experiment_end)
        model.experiment_failed_signal.connect(self.on_experiment_end)
        model.int_game_created_success.connect(self.on_experiment_start)
        model.int_game_reset_success.connect(self.on_experiment_end)

    def on_experiment_start(self):
        self.tabBar().setDisabled(True)

    def on_experiment_end(self):
        self.tabBar().setEnabled(True)


class OptsWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.options_layout = QVBoxLayout()
        self.options_layout.addWidget(self.size_field())
        self.options_layout.addWidget(self.ships_box())

        self.go_button = QPushButton("Go")
        self.go_button.pressed.connect(model.on_go_pressed)
        model.widgets["GoButton"] = self.go_button

        self.reset_button = QPushButton("Reset")
        self.reset_button.pressed.connect(model.on_reset_pressed)
        model.widgets["ResetButton"] = self.reset_button
        self.reset_button.hide()

        go_button_frame = QFrame()
        go_button_frame.setLayout(QHBoxLayout())
        go_button_frame.layout().addWidget(self.go_button)
        go_button_frame.layout().addWidget(self.reset_button)

        self.options_layout.addWidget(go_button_frame)
        self.setLayout(self.options_layout)

    def size_field(self):

        wh = QWidget()
        whl = QHBoxLayout()
        whl.setContentsMargins(0,0,0,0)
        wh.setLayout(whl)
        hlabel = QLabel("Height")
        hlabel.setMinimumWidth(60)
        hfield = QSpinBox()
        hfield.setMinimum(2)
        hfield.setMaximum(20)
        hfield.setValue(HEIGHT_DEFAULT)
        wlabel = QLabel("Width")
        hlabel.setMinimumWidth(60)
        wfield = QSpinBox()
        wfield.setMinimum(2)
        wfield.setMaximum(20)
        wfield.setValue(WIDTH_DEFAULT)
        wh.layout().addWidget(hlabel)
        wh.layout().addWidget(hfield)
        wh.layout().addWidget(wlabel)
        wh.layout().addWidget(wfield)
        wh.setFixedWidth(175)
        wh.setFixedHeight(30)

        model.widgets["HeightField"] = hfield
        model.widgets["WidthField"] = wfield

        # connect fields to slots on change
        wfield.valueChanged.connect(model.on_width_changed)
        hfield.valueChanged.connect(model.on_height_changed)
        wfield.valueChanged.connect(self.constrain_size_entry)
        hfield.valueChanged.connect(self.constrain_size_entry)

        return wh

    def on_game_started(self):
        self.setDisabled(True)

    def on_game_reset(self):
        self.setEnabled(True)

    def constrain_size_entry(self):
        if "ShipsSizeEntry" in model.widgets.keys():
            se = model.widgets["ShipsSizeEntry"]
            se.setMaximum(max(model.widgets["HeightField"].value(),
                              model.widgets["WidthField"].value()))

    def ships_box(self):
        ships = QFrame()
        ships_tools = QToolBar()
        ships_tools.addWidget(QLabel("Ships"))
        plus_button = QPushButton("+")
        minus_button = QPushButton("-")
        size_entry = QSpinBox()
        size_entry.setMinimum(1)
        ships_tools.addWidget(size_entry)
        ships_tools.addWidget(plus_button)
        ships_tools.addWidget(minus_button)

        plus_button.pressed.connect(model.on_add_ship)
        minus_button.pressed.connect(model.on_del_ship)

        ships_colview = QListView()
        ships_colview.setModel(model.ships)
        ships_colview.setEditTriggers(QAbstractItemView.EditTrigger(0))

        ships_layout = QVBoxLayout()
        ships_layout.addWidget(ships_tools)
        ships_layout.addWidget(ships_colview)
        ships.setLayout(ships_layout)
        ships.setMinimumHeight(100)
        ships.setFixedWidth(175)

        model.widgets["ShipsFrame"] = ships
        model.widgets["ShipsColumnView"] = ships_colview
        model.widgets["ShipsAddButton"] = plus_button
        model.widgets["ShipsRemoveButton"] = minus_button
        model.widgets["ShipsSizeEntry"] = size_entry

        self.constrain_size_entry()

        return ships

class BShipTab(QFrame):
    """Abstract tab class"""
    def __init__(self):
        super().__init__()
        self.tab_layout = QHBoxLayout()
        self.gameplay_layout = QVBoxLayout()

        self.tab_layout.addLayout(self.gameplay_layout)
        self.setLayout(self.tab_layout)
        self.populate_gameplay_box()

    def populate_gameplay_box(self):
        pass


class DynamicParLabel(QLabel):

    pretext = "Par = "

    def __init__(self):
        super().__init__(self.pretext + str(model.par))

        model.int_game_created_success.connect(self.update_)
        model.int_game_reset_success.connect(self.update_)

    def update_(self):
        self.setText(self.pretext + str(model.par))
        self.update()

class DynamicProgressLabel(QLabel):

    def __init__(self):
        super().__init__()
        self.n = 0
        self.i = 0
        self.maxlen = 0
        self.update_max_text_len()
        self.on_experiment_started(0)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        model.experiment_started_signal.connect(self.on_experiment_started)
        model.experiment_update_signal.connect(self.on_experiment_updated)
        model.experiment_complete_signal.connect(self.on_experiment_completed)

    def display_text(self):
        return f'{self.i}/{self.n}'.rjust(self.maxlen)

    def update_max_text_len(self):
        self.maxlen = len(f'{self.n}/{self.n}')

    def on_experiment_started(self, n):
        self.n = n
        self.i = 0
        self.update_max_text_len()
        self.setText(self.display_text())

    def on_experiment_updated(self, i):
        self.i = i
        self.setText(self.display_text())

    def on_experiment_completed(self, ignored):
        self.on_experiment_updated(self.n)



class DynamicScoreLabel(QLabel):

    pretext = "Score = "

    def __init__(self):
        super().__init__(self.pretext + str(model.score))
        model.hit_signal.connect(self.on_score_changed)
        model.miss_signal.connect(self.on_score_changed)
        model.int_game_created_success.connect(self.on_score_changed)
        model.int_game_reset_success.connect(self.on_score_changed)

    def on_score_changed(self):
        self.setText(self.pretext + str(model.score))
        self.update()

class InteractiveTab(BShipTab):
    """
    This class represents a page which allows the user to play a (custom)
    game of Battleship.
    Initially, the user should see a gridsize setting (nums), and a set of
    ships to play with, which can be changed.
    When the game is started, the user should then see a grid and be able
    to click on each square to guess.
    Guesses are tallied and displayed as SCORE.

    Additionally, the user should be able to click a button to visualise
    the possible remaining ships & get a hint for the probabilities/optimal guess.

    Optionally, the optimal solver's score on the specific generated board
    can be shown... to encourage the user to beat it ;)
    """
    def __init__(self):
        super().__init__()

    def populate_gameplay_box(self):
        gl = self.gameplay_layout

        self.gamebox = GameBox()
        gl.addWidget(self.gamebox)
        self.gamebox.populate()
        model.widgets["InteractiveGamebox"] = self.gamebox

        self.game_buttons = QWidget()
        self.game_buttons.setLayout(QHBoxLayout())
        score = DynamicScoreLabel()

        par = DynamicParLabel()
        self.game_buttons.setFixedHeight(40)

        checkie = QPushButton("Show Heatmap")
        checkie.pressed.connect(self.gamebox.show_heat)

        for w in [score, par, checkie]:
            w.setMinimumWidth(80)
            self.game_buttons.layout().addWidget(w)

        gl.addWidget(self.game_buttons)


class GameBoxButton(QPushButton):

    press_trigger = pyqtSignal(int)
    hit_color = "rgb(200, 50, 50)"
    miss_color = "rgb(50, 50, 200)"
    blank_color = "rgb(150, 150, 150)"
    disabled_color = "rgb(210, 210, 210)"


    def __init__(self, enabled, text, x, y):
        super().__init__()
        self.set_enabled(enabled)
        self.setMinimumSize(10, 10)
        self.setMaximumSize(1000, 1000)
        self.is_guessed = False
        self.scalar = xy_to_coord((x, y))
        self.pressed.connect(self.on_press)
        self.press_trigger.connect(model.on_game_button_pressed)

    def on_press(self):
        self.press_trigger.emit(self.scalar)
        self.is_guessed = True

    def enable(self):
        self.setEnabled(True)
        self.setStyleSheet("background-color : " + self.blank_color)

    def disable(self):
        self.setDisabled(True)
        self.setStyleSheet("background-color : " + self.disabled_color)

    def set_enabled(self, enabled):
        if enabled:
            self.enable()
            self.is_guessed = False
        else:
            self.disable()

    def set_hit(self):
        self.setStyleSheet("background-color : " + self.hit_color)

    def set_miss(self):
        self.setStyleSheet("background-color : " + self.miss_color)


def xy_to_coord(t: tuple) -> int:
    """
    Convert paired (x,y) coordinate to scalar coordinate
    """
    return t[0] + (t[1] * model.width)


def coord_to_xy(coord: int):
    """
    Convert scalar coordinate to paired (x,y) coordinate
    """
    x = coord % model.width
    y = math.floor(coord / model.width)
    return x, y


class GameBox(QWidget):

    def __init__(self):
        super().__init__()

        self.display_boxes = []
        self.playing = False

        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)
        self.connect_to_model()

    def connect_to_model(self):
        model.hit_signal.connect(self.on_hit_received)
        model.miss_signal.connect(self.on_miss_received)
        model.experiment_rerender_signal.connect(self.on_game_started)
        self.on_game_terminated()

    def show_heat(self):
        if not model.bg:
            return
        #assert isinstance(model.bg, BShipGame)
        for w in self.display_boxes:
            for b in w:
                assert isinstance(b, GameBoxButton)
                if b.is_guessed:
                    continue
                coord = b.scalar
                prob_belief = model.bg.prob_beliefs[coord]
                redness = int((prob_belief / 100) * 255)
                print("Set redness of",coord,"to",redness)
                b.setStyleSheet(f"background-color : rgb({redness},100,100)")

    def hide_heat(self):
        for w in self.display_boxes:
            for b in w:
                assert isinstance(b, GameBoxButton)
                if b.is_guessed:
                    continue
                else:
                    b.setStyleSheet("background-color : "+b.blank_color)


    def populate(self):
        """
        Populate gamebox with dynamic GameBoxButtons and repaint etc.
        :return: None
        """
        if self.playing:
            return

        for w in self.display_boxes:
            for h in w:
                h.deleteLater()
        self.display_boxes = []

        for y in range(0, model.height):
            row_boxes = []
            for x in range(0, model.width):
                grid_box = GameBoxButton(self.playing, str(xy_to_coord((x, y))), x, y)
                row_boxes.append(grid_box)
                self.layout().addWidget(grid_box, y, x)
            self.display_boxes.append(row_boxes)

    def on_hit_received(self, scalar_coord):
        if not self.isVisible():
            return
        self.hide_heat()
        y,x = coord_to_xy(scalar_coord)
        self.box_at(x, y).set_hit()

    def on_miss_received(self, scalar_coord):
        if not self.isVisible():
            return
        self.hide_heat()
        y,x = coord_to_xy(scalar_coord)
        self.box_at(x, y).set_miss()

    def on_gridsize_changed(self):
        self.populate()

    def on_game_started(self):
        if not self.isVisible():
            return
        self.set_enabled_all(True)

    def on_game_terminated(self):
        self.set_enabled_all(False)

    def box_at(self, x, y) -> GameBoxButton:
        return self.display_boxes[x][y]

    def set_enabled_all(self, enabled):
        if not self.isVisible():
            return
        for y in self.display_boxes:
            for x in y:
                x.set_enabled(enabled)


class ExperimentProgressBar(QProgressBar):

    def __init__(self):
        super().__init__()
        self.setMinimum(0)
        self.setMaximum(1)

        model.experiment_started_signal.connect(self.on_experiment_started)
        model.experiment_update_signal.connect(self.on_experiment_updated)
        model.experiment_complete_signal.connect(self.on_experiment_completed)

    def on_experiment_started(self, num_boards):
        self.reset()
        self.setRange(0,num_boards)

    def on_experiment_updated(self, value):
        self.setValue(value)

    def on_experiment_completed(self, ignored):
        self.setValue(self.maximum())

class ExperimentTab(BShipTab):
    """
    This class represents a page where the user can run experiments on strategies.
    The user should see several selectable strategies, gridsize, ship set params.
    These can be changed.
    Then, we can select a % of randomised experiments to run.
    A GUI demonstration of the strategy should be displayed live.
    Similarly to when the game is played interactively.
    """

    show_changed = pyqtSignal(bool)

    def __init__(self):

        self.generate_gamebox()
        super().__init__()

    def generate_gamebox(self):
        self.gamebox = GameBox()
        self.gamebox.populate()
        self.gamebox.setContentsMargins(0,0,0,0)
        model.widgets["ExperimentsGamebox"] = self.gamebox

    def populate_gameplay_box(self):
        gl = self.gameplay_layout
        gl.addWidget(self.gamebox)

        self.game_buttons = QFrame()
        game_buttons_layout = QHBoxLayout()
        self.game_buttons.setLayout(game_buttons_layout)
        self.game_buttons.setContentsMargins(0,0,0,0)
        game_buttons_layout.setContentsMargins(0,0,0,0)

        progress_label = DynamicProgressLabel()

        self.show_box = QCheckBox("Show")
        self.show_box.setChecked(True)
        self.show_box.setFixedWidth(55)
        self.show_box.stateChanged.connect(self.on_show_changed)
        self.show_changed.connect(model.on_show_changed)

        strat_selector = self.strategy_selector()

        for w in [strat_selector, progress_label, self.show_box]:
            game_buttons_layout.addWidget(w)

        model.widgets["ShowExperimentButton"] = self.show_box
        model.widgets["StrategySelector"] = strat_selector

        progress = ExperimentProgressBar()
        gameinfo_layout = QVBoxLayout()

        model.widgets["ProgressBar"] = progress

        gameinfo_layout.addWidget(progress)
        gameinfo_layout.addWidget(self.game_buttons)
        gameinfo_layout.setContentsMargins(0,0,0,0)
        gameinfo_layout.setSpacing(0)

        gameinfo_frame = QFrame()
        gameinfo_frame.setLayout(gameinfo_layout)
        gameinfo_frame.setContentsMargins(0,0,0,0)
        gameinfo_frame.setFixedHeight(40)

        gl.addWidget(gameinfo_frame)

    def on_show_changed(self):
        self.gamebox.set_enabled_all(False)
        self.show_changed.emit(self.show_box.isChecked())

    def strategy_selector(self):
        selector = QComboBox()
        selector.setModel(model.strategies)
        selector.currentTextChanged.connect(model.on_strategy_changed)
        selector.setFixedWidth(100)
        return selector

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()























