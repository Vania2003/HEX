"""Filesystem locations that must not depend on the current working directory.

The previous code opened ``autosave.json`` relative to the cwd, so saving and
loading behaved differently depending on where the game was started from, and
broke entirely in a PyInstaller bundle.
"""

import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


AUTOSAVE_PATH = os.path.join(app_dir(), "autosave.json")
