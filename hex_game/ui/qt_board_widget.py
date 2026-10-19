# File: hex_game/ui/qt_board_widget.py

import math

from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QMouseEvent
from PyQt6.QtCore import Qt, QPointF, QTimer

from hex_game.engine.geometry import EMPTY, O, X

COLORS = {
    EMPTY: QColor(50, 50, 50),
    X: QColor(0, 170, 255),
    O: QColor(255, 64, 129),
}
HOVER_COLOR = QColor(80, 80, 80, 150)
GRID_PEN = QPen(QColor(80, 80, 80), 1)
WIN_PEN = QPen(QColor(255, 255, 255), 3)

MARGIN_RATIO = 0.05
ANIMATION_STEP = 25


class BoardWidget(QWidget):
    """Flat-top even-q rendering of the board.

    Layout is recomputed only when the widget size, the zoom or the board size
    actually changes, and hex outlines are cached between frames.  Previously
    every mouse move rebuilt 121 polygons twice and repainted the whole board
    even when the cursor had not left the current cell.
    """

    def __init__(self, game, main_window=None):
        super().__init__()
        self.game = game
        self.main_window = main_window
        self.hovered = None
        self.anim_alpha = {}

        self.anim_timer = QTimer()
        self.anim_timer.setInterval(30)
        self.anim_timer.timeout.connect(self.update_animation)

        self.setMouseTracking(True)

        self.zoom_factor = 1.0
        self.hex_radius = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._layout_key = None
        self._polygons = []

    # ------------------------------------------------------------------
    # layout
    # ------------------------------------------------------------------

    def _ensure_layout(self):
        size = self.game.board.size
        key = (self.width(), self.height(), round(self.zoom_factor, 4), size)
        if key == self._layout_key:
            return
        self._layout_key = key

        width, height = self.width(), self.height()
        safe_w = width * (1 - 2 * MARGIN_RATIO)
        safe_h = height * (1 - 2 * MARGIN_RATIO)

        max_r_x = safe_w / (1.5 * size + 0.5)
        max_r_y = safe_h / (math.sqrt(3) * (size + 0.5))
        self.hex_radius = self.zoom_factor * min(max_r_x, max_r_y)

        board_width = 1.5 * self.hex_radius * (size - 1) + 2 * self.hex_radius
        board_height = math.sqrt(3) * self.hex_radius * (size + 0.5)
        # Pixel centre of cell (0, 0); every other centre is a step from here.
        self.offset_x = (width - board_width) / 2 + self.hex_radius
        self.offset_y = (height - board_height) / 2 + math.sqrt(3) * self.hex_radius / 2

        self._polygons = [
            self.hex_corners(*self.axial_to_pixel(index % size, index // size))
            for index in range(size * size)
        ]

    def axial_to_pixel(self, col, row):
        x = self.hex_radius * 1.5 * col
        y = self.hex_radius * math.sqrt(3) * (row + 0.5 * (col % 2))
        return x + self.offset_x, y + self.offset_y

    def hex_corners(self, cx, cy):
        r = self.hex_radius
        return QPolygonF([
            QPointF(cx + r * math.cos(i * math.pi / 3),
                    cy + r * math.sin(i * math.pi / 3))
            for i in range(6)
        ])

    # ------------------------------------------------------------------
    # painting
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        board = self.game.board
        size = board.size
        if not size:
            return

        self._ensure_layout()

        cells = board.cells
        winning = set()
        if self.game.get_winner():
            winning = {
                row * size + col for col, row in self.game.get_winning_path()
            }
        hovered_index = None
        if self.hovered is not None:
            hovered_index = self.hovered[1] * size + self.hovered[0]

        for index in range(size * size):
            polygon = self._polygons[index]
            color = COLORS[cells[index]]
            alpha = self.anim_alpha.get(index)
            if alpha is not None:
                color = QColor(color)
                color.setAlpha(alpha)

            painter.setPen(WIN_PEN if index in winning else GRID_PEN)
            painter.setBrush(QBrush(color))
            painter.drawPolygon(polygon)

            if index == hovered_index:
                painter.setBrush(QBrush(HOVER_COLOR))
                painter.drawPolygon(polygon)

    # ------------------------------------------------------------------
    # interaction
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, ev: QMouseEvent):
        hovered = self.find_cell_under_cursor(ev.position())
        if hovered != self.hovered:
            self.hovered = hovered
            self.update()

    def mousePressEvent(self, ev: QMouseEvent):
        if self.game.get_winner() or not self._human_may_play():
            return
        coords = self.find_cell_under_cursor(ev.position())
        if coords is None:
            return
        x, y = coords
        if not self.game.make_move(x, y):
            return
        self.animate_cell(x, y)
        self.update()
        if self.main_window:
            self.main_window.update_status()
            self.main_window.check_bot_move()
        if self.game.get_winner():
            self.show_winner(self.game.get_winner_name())

    def _human_may_play(self):
        """A click must not steal the bot's turn while it is thinking."""
        window = self.main_window
        if window is None:
            return True
        return not window.bot_busy and not window.bot_to_move()

    def find_cell_under_cursor(self, pos):
        """Nearest hex centre, then one exact containment test."""
        self._ensure_layout()
        size = self.game.board.size
        radius = self.hex_radius
        if radius <= 0:
            return None

        approx_col = round((pos.x() - self.offset_x) / (1.5 * radius))
        best_index = None
        best_distance = None
        for col in range(max(0, approx_col - 1), min(size, approx_col + 2)):
            approx_row = round(
                (pos.y() - self.offset_y) / (math.sqrt(3) * radius) - 0.5 * (col % 2)
            )
            for row in range(max(0, approx_row - 1), min(size, approx_row + 2)):
                cx, cy = self.axial_to_pixel(col, row)
                distance = (cx - pos.x()) ** 2 + (cy - pos.y()) ** 2
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_index = row * size + col

        if best_index is None:
            return None
        if not self._polygons[best_index].containsPoint(pos, Qt.FillRule.WindingFill):
            return None
        return best_index % size, best_index // size

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.zoom_factor *= 1.05
        elif angle < 0:
            self.zoom_factor /= 1.05
        self.zoom_factor = max(0.4, min(2.5, self.zoom_factor))
        self.update()

    # ------------------------------------------------------------------
    # animation
    # ------------------------------------------------------------------

    def animate_cell(self, x, y):
        self.anim_alpha[y * self.game.board.size + x] = 0
        if not self.anim_timer.isActive():
            self.anim_timer.start()

    def update_animation(self):
        if not self.anim_alpha:
            self.anim_timer.stop()
            return
        for index in list(self.anim_alpha):
            alpha = self.anim_alpha[index] + ANIMATION_STEP
            if alpha >= 255:
                del self.anim_alpha[index]
            else:
                self.anim_alpha[index] = alpha
        self.update()

    def show_winner(self, w):
        QMessageBox.information(self, "Koniec gry", f"Gracz {w} wygrał!")

    def set_game(self, game):
        self.game = game
        self.anim_alpha.clear()
        self.hovered = None
        self._layout_key = None
        self.update()
