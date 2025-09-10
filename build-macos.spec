# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Academic Auto Grader GUI - macOS Build
Optimized for macOS deployment with app bundle and signing support
"""

import os
import sys
from pathlib import Path

# Get the project root directory
block_cipher = None
project_root = Path(SPECPATH)

# Application info
app_name = "AcademicAutoGrader"
app_version = "1.0.0"
app_description = "Academic Auto Grader - Automated assignment grading with AI"
app_author = "Academic Auto Grader Team"

# Define paths
gui_main = project_root / "gui" / "main.py"
cli_core = project_root / "cli" / "core"
gui_app = project_root / "gui" / "app"
assignments_dir = project_root / "assignments"
templates_dir = project_root / "cli" / "templates"
assets_dir = project_root / "gui" / "assets"

# Data files to include
datas = [
    # CLI templates
    (str(templates_dir), "cli/templates"),
    # Sample assignments
    (str(assignments_dir), "assignments"),
    # GUI assets
    (str(assets_dir), "gui/assets"),
    # GUI app modules
    (str(gui_app), "gui/app"),
    # CLI core modules
    (str(cli_core), "cli/core"),
]

# macOS-specific hidden imports
hiddenimports = [
    # Flet and dependencies
    'flet',
    'flet.auth',
    'flet.auth.providers',
    'flet_core',
    'flet_runtime',
    
    # GUI modules
    'gui.app.pages.welcome',
    'gui.app.pages.file_selection',
    'gui.app.pages.configuration',
    'gui.app.pages.processing',
    'gui.app.pages.results',
    'gui.app.pages.assignment_editor',
    'gui.app.pages.assignment_wizard',
    'gui.app.pages.config_validator',
    'gui.app.pages.api_key_manager',
    'gui.app.pages.user_preferences',
    'gui.app.pages.application_settings',
    'gui.app.services.config_service',
    'gui.app.services.grader_service',
    'gui.app.services.export_service',
    'gui.app.services.validation_service',
    'gui.app.services.api_key_service',
    'gui.app.services.preferences_service',
    'gui.app.services.application_settings_service',
    'gui.app.services.localization_service',
    'gui.app.components.file_picker',
    'gui.app.components.assignment_selector',
    'gui.app.components.cost_estimator',
    'gui.app.components.progress_bar',
    'gui.app.router',
    
    # CLI modules
    'cli.core.auto_grader',
    'cli.core.config_loader',
    'cli.core.github_scanner',
    'cli.core.prompt_builder',
    'cli.preprocessing.clean_zip_files',
    'cli.preprocessing.consolidate_assignments',
    'cli.tools.assignment_generator',
    'cli.tools.config_validator',
    
    # Third-party dependencies
    'yaml',
    'jinja2',
    'pandas',
    'openpyxl',
    'openai',
    'anthropic',
    'nbformat',
    'docx',
    'PyPDF2',
    'requests',
    'keyring',
    'send2trash',
    'psutil',
    
    # macOS-specific
    'AppKit',
    'Foundation',
    'Cocoa',
    'objc',
    'Security',
    'CoreFoundation',
    'SystemConfiguration',
]

# Binaries (empty for most applications)
binaries = []

# Modules to exclude (reduce size)
excludes = [
    # Development tools
    'pytest',
    'pytest-cov',
    'coverage',
    'black',
    'flake8',
    'mypy',
    'pylint',
    
    # Jupyter (if not needed)
    'jupyter',
    'notebook',
    'ipython',
    
    # Unused GUI frameworks
    'tkinter',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',
    'kivy',
    
    # Windows-specific
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'winsound',
    'msvcrt',
    'winreg',
    'ctypes.wintypes',
]

a = Analysis(
    [str(gui_main)],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Set this for code signing
    entitlements_file=None,  # Set this for sandboxing
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Create macOS app bundle
app = BUNDLE(
    coll,
    name=f'{app_name}.app',
    icon='gui/assets/icons/grader.icns',
    bundle_identifier='com.academicautograder.app',
    version=app_version,
    info_plist={
        'CFBundleName': app_name,
        'CFBundleDisplayName': 'Academic Auto Grader',
        'CFBundleShortVersionString': app_version,
        'CFBundleVersion': app_version,
        'CFBundleExecutable': app_name,
        'CFBundleIdentifier': 'com.academicautograder.app',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'AGRD',
        'CFBundleInfoDictionaryVersion': '6.0',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'NSAppleEventsUsageDescription': 'This app needs Apple Events access for automation features.',
        'NSFileProviderPresenceUsageDescription': 'This app needs file access to grade student assignments.',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'YAML Configuration',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['yaml', 'yml'],
                'CFBundleTypeMIMETypes': ['application/x-yaml', 'text/yaml'],
                'CFBundleTypeIconFile': 'grader',
            }
        ],
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'com.academicautograder.assignment',
                'CFBundleURLSchemes': ['autograder'],
            }
        ],
        'LSApplicationCategoryType': 'public.app-category.education',
        'NSHumanReadableCopyright': f'© 2024 {app_author}. All rights reserved.',
    },
)