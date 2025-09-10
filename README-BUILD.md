# Academic Auto Grader - Build Instructions

This document provides instructions for building the Academic Auto Grader GUI application for distribution.

## Prerequisites

### Required Software
- Python 3.8 or higher
- PyInstaller 6.0.0 or higher
- Git (for version control)

### Optional (Recommended)
- UPX (Universal Packer for eXecutables) - for smaller build sizes
- Platform-specific tools:
  - **Windows**: Visual Studio Build Tools
  - **macOS**: Xcode Command Line Tools
  - **Linux**: Standard development tools (gcc, make)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/michael-borck/academic-auto-grader.git
   cd academic-auto-grader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Flet installation**:
   ```bash
   python -c "import flet; print('Flet version:', flet.__version__)"
   ```

## Building

### Quick Build (Current Platform)

The easiest way to build is using the provided build scripts:

**Linux/macOS**:
```bash
./build.sh
```

**Windows**:
```cmd
build.bat
```

**Python (all platforms)**:
```bash
python build.py
```

### Advanced Build Options

```bash
# Clean build (removes previous artifacts)
python build.py --clean

# Debug build (includes debug information)
python build.py --debug

# Build without UPX compression
python build.py --no-upx

# Create distribution packages
python build.py --package

# Cross-platform build (specify target)
python build.py --platform windows
python build.py --platform macos
python build.py --platform linux
```

### Platform-Specific Builds

#### Windows Build
```bash
python -m PyInstaller build-windows.spec --clean
```

**Output**: `dist/AcademicAutoGrader/` directory with executable

#### macOS Build
```bash
python -m PyInstaller build-macos.spec --clean
```

**Output**: `dist/AcademicAutoGrader.app/` application bundle

#### Linux Build
```bash
python -m PyInstaller build-linux.spec --clean
```

**Output**: `dist/AcademicAutoGrader/` directory with executable

## Build Outputs

After a successful build, you'll find the following in the `dist/` directory:

### Windows
- `AcademicAutoGrader.exe` - Main executable
- Supporting libraries and data files
- Typical size: 80-120 MB

### macOS
- `AcademicAutoGrader.app` - Application bundle
- Can be dragged to Applications folder
- Typical size: 90-130 MB

### Linux
- `AcademicAutoGrader` - Executable binary
- Supporting libraries and data files
- Typical size: 85-125 MB

## Distribution

### Packaging for Distribution

1. **Test the build**:
   ```bash
   # Navigate to dist directory and run the application
   cd dist/AcademicAutoGrader  # or AcademicAutoGrader.app on macOS
   ./AcademicAutoGrader        # or open -a AcademicAutoGrader.app on macOS
   ```

2. **Create distribution archives**:
   ```bash
   # Windows
   zip -r AcademicAutoGrader-1.0.0-windows.zip AcademicAutoGrader/
   
   # macOS
   hdiutil create -volname "Academic Auto Grader" -srcfolder AcademicAutoGrader.app -ov -format UDZO AcademicAutoGrader-1.0.0-macos.dmg
   
   # Linux
   tar -czf AcademicAutoGrader-1.0.0-linux.tar.gz AcademicAutoGrader/
   ```

### Code Signing (Recommended for Distribution)

#### Windows
```bash
# Sign with signtool (requires certificate)
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist/AcademicAutoGrader/AcademicAutoGrader.exe
```

#### macOS
```bash
# Sign the application (requires Apple Developer certificate)
codesign --sign "Developer ID Application: Your Name" --deep --force --options runtime dist/AcademicAutoGrader.app

# Notarize for Gatekeeper
xcrun notarytool submit AcademicAutoGrader-1.0.0-macos.dmg --keychain-profile "notarytool-profile" --wait
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   - Check that all dependencies are installed
   - Verify the spec file includes all necessary hiddenimports

2. **Large build sizes**:
   - Install UPX for compression
   - Review excludes list in spec files
   - Consider removing unused dependencies

3. **Slow startup times**:
   - Use directory mode instead of onefile mode
   - Optimize Python imports in the application

4. **Missing data files**:
   - Verify datas list in spec files
   - Check that file paths are correct

### Build Optimization

To reduce build size:

1. **Use UPX compression**:
   ```bash
   # Install UPX
   # Ubuntu/Debian: sudo apt install upx
   # macOS: brew install upx
   # Windows: Download from https://upx.github.io/
   ```

2. **Exclude unnecessary modules**:
   Edit the `excludes` list in the spec files to remove unused libraries.

3. **Minimize included data**:
   Only include essential templates and sample assignments.

### Performance Tips

1. **Faster builds**:
   - Use `--clean` only when necessary
   - Keep the `build/` directory for incremental builds

2. **Smaller executables**:
   - Enable UPX compression
   - Remove debug symbols in production builds
   - Exclude development dependencies

## File Structure

```
academic-auto-grader/
├── build.py                 # Main build script
├── build.sh                 # Unix build wrapper
├── build.bat                # Windows build wrapper
├── academic-auto-grader.spec # Cross-platform spec
├── build-windows.spec       # Windows-specific spec
├── build-macos.spec         # macOS-specific spec
├── build-linux.spec         # Linux-specific spec
├── version_info.txt         # Windows version information
├── pyinstaller-hooks/       # Custom PyInstaller hooks
│   ├── hook-flet.py
│   └── hook-gui.py
├── gui/                     # GUI application code
├── cli/                     # CLI application code
├── assignments/             # Sample assignments
└── dist/                    # Build output (created during build)
```

## Support

For build issues:

1. Check the [PyInstaller documentation](https://pyinstaller.readthedocs.io/)
2. Review the [Flet packaging guide](https://flet.dev/docs/getting-started/python#packaging-as-a-desktop-app)
3. Open an issue on the [project repository](https://github.com/michael-borck/academic-auto-grader/issues)

## License

This build system is part of the Academic Auto Grader project and is subject to the same license terms.