"""
PyInstaller hook for GUI modules
Ensures all GUI components are properly included
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

# Get the GUI directory path
gui_path = os.path.join(os.path.dirname(__file__), '..', 'gui')

# Collect all GUI submodules
hiddenimports = collect_submodules('gui')

# Additional specific imports
hiddenimports += [
    'gui.app',
    'gui.app.pages',
    'gui.app.services',
    'gui.app.components',
    'gui.app.models',
    'gui.main',
]

# Collect GUI data files
datas = []
if os.path.exists(gui_path):
    # Include any additional GUI data files
    pass