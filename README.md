# Hex Game (PyQt6)

Gra planszowa **Hex** napisana w Pythonie z użyciem PyQt6.  
Obsługuje tryby gry:
- Gracz vs Gracz
- Gracz vs Bot (Minimax AI)

---

## 📦 Instalacja i uruchomienie

### Wersja źródłowa (Python)

1. Upewnij się, że masz zainstalowanego **Pythona 3.10 lub nowszego**.
2. (Opcjonalnie) Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   source venv/bin/activate # Linux/Mac
   ```
3. Zainstaluj wymagane biblioteki:
   ```bash
   pip install pyqt6
   ```
4. Uruchom grę:
   ```bash
   python hex_game/main.py
   ```

---

### Wersja `.exe` (Windows)

Jeśli masz gotowy plik `HexGame.exe` (w folderze `dist/`):

1. Przejdź do katalogu `dist/`.
2. Uruchom `HexGame.exe` (podwójne kliknięcie).

✅ **Nie musisz instalować Pythona ani bibliotek!**

---

## 🎮 Jak grać

1. Na starcie gry możesz:
   - Wybrać imiona graczy.
   - Wybrać tryb gry: **Gracz vs Gracz** lub **Gracz vs Bot**.
   - Określić, który gracz zaczyna (`X` lub `O`).

2. **Cel gry**:
   - Gracz `X` — połącz lewą i prawą krawędź planszy.
   - Gracz `O` — połącz górną i dolną krawędź planszy.

3. **Sterowanie**:
   - Klikaj na heksagony, aby stawiać swoje znaczniki (`X` lub `O`).

4. **Po wygranej**:
   - Ścieżka zwycięzcy zostaje automatycznie podświetlona.
   - Wyświetli się komunikat z gratulacjami.

---

## 💾 Funkcje dodatkowe

- 📂 Zapisywanie i wczytywanie stanu gry (`Plik -> Zapisz/Wczytaj`).
- 🧐 Tryb **Gracz vs Bot** z prostym AI (algorytm Minimax).
- 🔍 Zoomowanie planszy za pomocą kółka myszy.
- ✨ Animacje pól i podświetlanie zwycięskiej ścieżki.

---

## 📜 Wymagania

- Python 3.10+
- PyQt6

---
