"""
PyInstaller hook for Flet
Ensures all necessary Flet components are included in the build
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# Collect all Flet modules and data
datas, binaries, hiddenimports = collect_all('flet')

# Add specific Flet submodules that might be missed
hiddenimports += [
    'flet_core',
    'flet_runtime',
    'flet.auth',
    'flet.auth.providers',
    'flet.auth.providers.azure_ad',
    'flet.auth.providers.github',
    'flet.auth.providers.google',
]

# Collect additional data files
additional_datas = [
    # Any additional Flet data files
]

datas.extend(additional_datas)