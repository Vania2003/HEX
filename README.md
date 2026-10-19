# Hex Game (PyQt6)

A **Hex** board game written in Python with PyQt6, used as the base for a
computational-intelligence project comparing game-playing agents.

Game modes:

- Player vs. Player
- Player vs. Bot

---

## 📦 Installation and Launch

1. Make sure you have **Python 3.10 or newer**.
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # Linux/Mac
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the game **from the project root**:

   ```bash
   python -m hex_game.main
   ```

   The package uses absolute imports, so `python hex_game/main.py` will fail
   with `ModuleNotFoundError: No module named 'hex_game'`.

In VS Code the bundled launch configuration **Hex Game** (`F5`) does the same
thing with the right working directory.

### Building a standalone `.exe`

```bash
pip install pyinstaller
python -m PyInstaller main.spec
```

The result lands in `dist/`. Build outputs are not tracked by git.

---

## 🎮 How to Play

1. Set up the game in the start dialog: player names, board size (7–13), mode,
   who moves first, the bot's algorithm and difficulty, and whether the swap
   rule applies.
2. **Objective**:
   - Player `X` connects the **left** and **right** edges.
   - Player `O` connects the **top** and **bottom** edges.
3. Click a hexagon to place your stone.
4. When someone wins, the winning chain is outlined and a message appears.

Hex can never end in a draw: on a full board exactly one player has connected
their two sides, which is checked by the test suite.

---

## ✨ Features

- Board sizes from 7×7 to 13×13.
- **Swap rule (pie rule)** — the second player may claim the opening stone
  instead of answering it, which offsets the first player's advantage. The
  players exchange seats; the stone itself never moves.
- **Undo** (`Ctrl+Z`) — takes back a move, or the swap; against a bot it hands
  the human back their own turn in one step.
- Save and load games (`Ctrl+S` / `Ctrl+O`), plus an autosave on exit.
- The bot searches on a worker thread, so the window stays responsive.
- Difficulty is a time budget per move: easy 0.2 s, normal 1 s, hard 3 s.
- Zoom the board with the mouse wheel.

---

## 🤖 Agents

| Agent | Idea |
| --- | --- |
| `minimax` | Alpha-beta with iterative deepening under a time budget. Positions are scored by the difference of *connection distances*: how many empty cells each player still has to fill to join their two borders, with own stones free and opponent stones impassable. |

Agents are registered in `hex_game/players/registry.py`.

---

## 🧱 Architecture

```
hex_game/
├── engine/
│   ├── geometry.py    # the only module that knows about adjacency
│   ├── union_find.py  # disjoint sets with undoable unions
│   ├── board.py       # stones, incremental connectivity, undo
│   └── game.py        # turns, swap rule, undo, persistence
├── players/
│   ├── bot_minimax.py
│   └── registry.py    # agent catalogue and difficulty presets
└── ui/
    ├── qt_main.py          # window, menus, side panel
    ├── qt_board_widget.py  # board rendering and input
    ├── bot_worker.py       # runs a search off the GUI thread
    └── game_setup_dialog.py
```

Two details are worth knowing before changing the engine:

**Geometry.** Cells are stored in a flat array addressed by `row * size + col`.
Storage coordinates are an even-q offset projection of axial coordinates
(`q = col`, `r = row - col // 2`), so the parity-dependent neighbour offsets in
`geometry.py` are exactly the six fixed axial directions. Nothing outside that
module may hard-code neighbour deltas.

**Seats vs. players.** `'X'` and `'O'` are *seats* with fixed target borders,
and the move history records seats. `player_x` / `player_o` only say who
currently occupies each seat. The swap rule exchanges the occupants, which is
why it needs no change to the board.

---

## 🧪 Tests

```bash
pip install pytest
pytest
```

The suite covers the geometry (including an independent check that the parity
rule equals the six axial directions), undo and rollback, win detection against
a brute-force reference, the no-draw property, and the swap/undo/save rules.

---

## 📜 Requirements

- Python 3.10+
- PyQt6
