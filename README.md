# Hex Game (PyQt6)

A **Hex** board game written in Python using PyQt6.
It supports the following game modes:
- Player vs. Player
- Player vs. Bot (Minimax AI)

---

## 📦 Installation and Launch

### Source Version (Python)

1.  Make sure you have **Python 3.10 or newer** installed.
2.  (Optional) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    venv\Scripts\activate   # Windows
    source venv/bin/activate # Linux/Mac
    ```
3.  Install the required libraries:
    ```bash
    pip install pyqt6
    ```
4.  Run the game:
    ```bash
    python hex_game/main.py
    ```

---

### `.exe` Version (Windows)

If you have the `HexGame.exe` file (in the `dist/` folder):

1.  Navigate to the `dist/` directory.
2.  Run `HexGame.exe` (by double-clicking).

✅ **You don't need to install Python or any libraries!**

---

## 🎮 How to Play

1.  When the game starts, you can:
    -   Choose player names.
    -   Select the game mode: **Player vs. Player** or **Player vs. Bot**.
    -   Specify which player starts (`X` or `O`).

2.  **Objective**:
    -   Player `X` — connect the left and right edges of the board.
    -   Player `O` — connect the top and bottom edges of the board.

3.  **Controls**:
    -   Click on the hexagons to place your markers (`X` or `O`).

4.  **After a win**:
    -   The winner's path is automatically highlighted.
    -   A congratulatory message is displayed.

---

## 💾 Additional Features

-   📂 Save and load game state (`File -> Save/Load`).
-   🧐 **Player vs. Bot** mode with a simple AI (Minimax algorithm).
-   🔍 Zoom the board using the mouse wheel.
-   ✨ Tile animations and highlighting of the winning path.

---

## 📜 Requirements

-   Python 3.10+
-   PyQt6
