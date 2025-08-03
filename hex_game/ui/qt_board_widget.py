# File: hex_game/ui/qt_board_widget.py

import math
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QMouseEvent
from PyQt6.QtCore import Qt, QPointF, QTimer

COLORS = {
    '.': QColor(50, 50, 50),
    'X': QColor(0, 170, 255),
    'O': QColor(255, 64, 129),
}
HOVER_COLOR = QColor(80, 80, 80, 150)
SPACING = 4  # odstęp między heksami

class BoardWidget(QWidget):
    def __init__(self, game, main_window=None):
        super().__init__()
        self.game = game
        self.main_window = main_window
        self.hovered = None
        self.anim_cells = []

        self.anim_timer = QTimer()
        self.anim_timer.setInterval(30)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start()

        self.setMouseTracking(True)

        self.zoom_factor = 1.0

    def axial_to_pixel(self, q, r):
        x = self.hex_radius * 3 / 2 * q
        y = self.hex_radius * math.sqrt(3) * (r + 0.5 * (q % 2))
        return x + self.offset_x, y + self.offset_y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        board = self.game.get_board_state()
        if not board:
            return

        rows = len(board)
        cols = len(board[0])
        w, h = self.width(), self.height()

        # MARGINES KAMERY – logiczne oddalenie planszy
        margin_ratio = 0.05  # 5% margines z każdej strony
        safe_w = w * (1 - 2 * margin_ratio)
        safe_h = h * (1 - 2 * margin_ratio)

        # Oblicz optymalny promień heksa (flat-top even-q)
        max_r_x = safe_w / (1.5 * cols + 0.5)
        max_r_y = safe_h / (math.sqrt(3) * (rows + 0.5))
        self.hex_radius = self.zoom_factor * min(max_r_x, max_r_y)

        # Rozmiar planszy w pikselach
        board_width = 1.5 * self.hex_radius * (cols - 1) + 2 * self.hex_radius
        board_height = math.sqrt(3) * self.hex_radius * (rows + 0.5)

        # Wycentrowanie
        self.offset_x = (w - board_width) / 2
        self.offset_y = (h - board_height) / 2

        # Rysuj planszę
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                cx, cy = self.axial_to_pixel(x, y)
                poly = self.hex_corners(cx, cy, self.hex_radius)

                color = QColor(COLORS[cell])
                for anim in self.anim_cells:
                    if anim['x'] == x and anim['y'] == y:
                        color.setAlpha(min(anim['alpha'], 255))

                # ✨ NOWOŚĆ: podświetlenie zwycięskiej ścieżki
                if self.game.get_winner() and (x, y) in self.game.get_winning_path():
                    painter.setPen(QPen(QColor(255, 255, 255), 3))
                else:
                    painter.setPen(QPen(QColor(80, 80, 80), 1))

                painter.setBrush(QBrush(color))
                painter.drawPolygon(poly)

                if self.hovered == (x, y):
                    painter.setBrush(QBrush(HOVER_COLOR))
                    painter.drawPolygon(poly)

    def hex_corners(self, cx, cy, r):
        return QPolygonF([
            QPointF(cx + r * math.cos(i * math.pi / 3),
                    cy + r * math.sin(i * math.pi / 3))
            for i in range(6)
        ])

    def mouseMoveEvent(self, ev: QMouseEvent):
        pos = ev.position()
        self.hovered = self.find_cell_under_cursor(pos)
        self.update()

    def mousePressEvent(self, ev: QMouseEvent):
        if self.game.get_winner():
            return
        pos = ev.position()
        coords = self.find_cell_under_cursor(pos)
        if coords is None:
            return
        x, y = coords
        if self.game.make_move(x, y):
            self.animate_cell(x, y)
            self.update()
            if self.main_window:
                self.main_window.update_status()
                self.main_window.check_bot_move()
            if self.game.get_winner():
                self.show_winner(self.game.get_winner())

    def find_cell_under_cursor(self, pos):
        board = self.game.get_board_state()

        for y, row in enumerate(board):
            for x, _ in enumerate(row):
                cx, cy = self.axial_to_pixel(x, y)
                poly = self.hex_corners(cx, cy, self.hex_radius)

                if poly.containsPoint(pos, Qt.FillRule.WindingFill):
                    return (x, y)
        return None

    def show_winner(self, w):
        QMessageBox.information(self, "Koniec gry", f"Gracz {w} wygrał!")

    def set_game(self, game):
        self.game = game
        self.update()

    def animate_cell(self, x, y):
        self.anim_cells.append({'x': x, 'y': y, 'alpha': 0})

    def update_animation(self):
        updated = False
        for cell in self.anim_cells:
            if cell['alpha'] < 255:
                cell['alpha'] += 25
                updated = True
        if updated:
            self.update()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.zoom_factor *= 1.05  # powiększ
        elif angle < 0:
            self.zoom_factor /= 1.05  # pomniejsz

        self.zoom_factor = max(0.4, min(2.5, self.zoom_factor))  # limit zoomu
        self.update()
