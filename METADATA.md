# Application Metadata and Versioning

This document describes the comprehensive metadata and versioning system implemented for the Academic Auto Grader application.

## Overview

The application now includes a robust metadata and versioning system that provides:
- Centralized version management
- Professional application branding
- Build and deployment metadata
- Cross-platform executable support
- Professional UI components with dynamic metadata

## Key Components

### 1. Version Management (`gui/app/version.py`)

**Features:**
- Centralized version information from `VERSION` file
- Git integration for commit and branch information
- Build metadata (date, type, bundled status)
- System information collection
- Comprehensive application metadata

**Key Functions:**
- `get_version()` - Get version from VERSION file or git tags
- `get_build_info()` - Get build metadata including git info
- `get_system_info()` - Get system and runtime information
- `get_app_metadata()` - Get complete application metadata
- `print_version_info()` - Command-line version display

### 2. Application Metadata

**Application Details:**
- Name: "Academic Auto Grader"
- Description: "Automated Assignment Grading with AI"
- Author: "Academic Auto Grader Team"
- License: "MIT"
- URL: "https://github.com/michael-borck/academic-auto-grader"

**Dynamic Metadata:**
- Version from VERSION file
- Git commit hash and branch
- Build date and type
- System information
- Runtime environment details

### 3. Professional Icons and Branding

**Icon System (`gui/assets/icons/`):**
- Professional SVG source design
- Multiple PNG formats (16x16 to 1024x1024)
- Windows ICO format
- macOS ICNS format
- Cross-platform compatibility

**Generated Icons:**
- `grader.svg` - Vector source (2.8 KB)
- `grader.png` - Main icon (8.4 KB)
- `grader.ico` - Windows executable icon
- `grader.icns` - macOS app bundle icon
- Multiple PNG sizes for different use cases

### 4. Build and Packaging System

**PyInstaller Specification (`gui/academic_auto_grader.spec`):**
- Complete application packaging configuration
- Windows executable metadata
- macOS app bundle configuration
- Icon and resource inclusion
- Dependency management

**Build Script (`tools/build_app.py`):**
- Automated build process
- Version management
- Icon generation
- Clean and rebuild options
- Cross-platform support

**Windows Metadata (`gui/version_info.txt`):**
- File version information
- Company and product details
- Copyright information
- Description and comments

**Application Manifest (`gui/app_manifest.xml`):**
- Windows compatibility settings
- DPI awareness configuration
- Security permissions
- Modern Windows support

### 5. Enhanced UI Components

**Splash Screen (`gui/app/components/splash_screen.py`):**
- Dynamic application name and version
- Professional loading animation
- Branded design elements
- Metadata-driven content

**About Dialog (`gui/app/components/about_dialog.py`):**
- Comprehensive application information
- Real-time system information
- Build and version details
- Professional tabbed interface
- Direct links to project resources

**App Bar Integration:**
- About button in application bar
- Version display in window title
- Professional branding elements

### 6. Cross-Platform Support

**Linux Desktop Integration:**
- Desktop entry file (`gui/academic-auto-grader.desktop`)
- AppImage configuration (`gui/AppImageBuilder.yml`)
- System integration metadata

**macOS App Bundle:**
- Info.plist configuration in PyInstaller spec
- Bundle identifier and metadata
- macOS-specific settings

**Windows Executable:**
- Version information resource
- Application manifest for modern Windows
- Professional executable metadata

### 7. Main Application Integration

**Enhanced Main Application (`gui/main.py`):**
- Version system integration
- Dynamic window title with version
- Application icon loading
- Metadata-driven initialization

## Usage Examples

### Command Line Version Info
```bash
python gui/app/version.py
```

### Build Icons Only
```bash
python tools/build_app.py --icons-only
```

### Build Executable
```bash
python tools/build_app.py --mode onedir
```

### Build with Version Update
```bash
python tools/build_app.py --version 1.1.0
```

### Clean Build
```bash
python tools/build_app.py --clean
```

## Metadata in Action

### Version Display
- Window title: "Academic Auto Grader v1.0.0"
- About dialog shows complete version information
- Splash screen displays current version
- Command-line version output available

### System Information
- Python version and executable path
- Operating system and architecture
- Flet framework version
- Bundle status (development vs. packaged)
- Git information (commit, branch, build type)

### Build Information
- Build date and timestamp
- Git commit hash and branch
- Development vs. release build type
- Bundled application detection

## Professional Features

### Icon System
- Scalable vector graphics source
- Professional design with education theme
- Multiple format support for all platforms
- Automated generation process

### Branding Integration
- Consistent application name across all components
- Professional color scheme (blue theme)
- Comprehensive copyright and author information
- Direct links to project resources

### Metadata Accuracy
- Real-time system information
- Automatic version detection
- Git integration for development builds
- Professional application packaging

## Benefits

1. **Professional Appearance**: Consistent branding and professional icons
2. **Version Management**: Centralized version control and display
3. **Build Automation**: Streamlined build and packaging process
4. **Cross-Platform Support**: Works on Windows, macOS, and Linux
5. **Development Support**: Git integration and build information
6. **User Experience**: Professional UI with comprehensive about information
7. **Maintenance**: Easy version updates and metadata management

## Future Enhancements

- Code signing for Windows and macOS
- Automatic update checking
- Installer package creation
- Distribution-specific packaging (DEB, RPM, MSI)
- CI/CD integration for automated builds

This metadata system provides a professional foundation for the Academic Auto Grader application, supporting both development and distribution needs while maintaining consistent branding and version management across all platforms.