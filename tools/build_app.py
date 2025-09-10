#!/usr/bin/env python3
"""
Build Script for Academic Auto Grader
Creates distributable executables with proper metadata and resources
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
from datetime import datetime

# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
GUI_DIR = PROJECT_ROOT / "gui"
TOOLS_DIR = PROJECT_ROOT / "tools"
DIST_DIR = PROJECT_ROOT / "dist"

def get_version():
    """Get version from VERSION file"""
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"

def update_version_files(version):
    """Update version in all relevant files"""
    print(f"Updating version to {version}")
    
    # Update version_info.txt for Windows
    version_info_file = GUI_DIR / "version_info.txt"
    if version_info_file.exists():
        content = version_info_file.read_text()
        # Update version numbers (assumes format x.y.z)
        parts = version.split('.')
        while len(parts) < 4:
            parts.append('0')
        version_tuple = f"({', '.join(parts)})"
        
        # Replace version tuples
        content = content.replace("filevers=(1, 0, 0, 0)", f"filevers={version_tuple}")
        content = content.replace("prodvers=(1, 0, 0, 0)", f"prodvers={version_tuple}")
        content = content.replace("u'FileVersion', u'1.0.0.0'", f"u'FileVersion', u'{version}.0'")
        content = content.replace("u'ProductVersion', u'1.0.0.0'", f"u'ProductVersion', u'{version}.0'")
        
        version_info_file.write_text(content)
    
    # Update app manifest
    manifest_file = GUI_DIR / "app_manifest.xml"
    if manifest_file.exists():
        content = manifest_file.read_text()
        content = content.replace('version="1.0.0.0"', f'version="{version}.0"')
        manifest_file.write_text(content)

def run_command(cmd, cwd=None):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def build_icons():
    """Generate application icons"""
    print("Generating application icons...")
    icon_script = TOOLS_DIR / "create_icons.py"
    if icon_script.exists():
        if not run_command([sys.executable, str(icon_script)]):
            print("Warning: Failed to generate icons")
            return False
    else:
        print("Warning: Icon generation script not found")
    return True

def build_executable(platform=None, mode='onedir'):
    """Build executable using PyInstaller"""
    print(f"Building executable for {platform or 'current platform'} in {mode} mode...")
    
    # Ensure icons are built first
    if not build_icons():
        print("Continuing without icons...")
    
    # Change to GUI directory
    original_cwd = os.getcwd()
    os.chdir(GUI_DIR)
    
    try:
        # Prepare PyInstaller command
        spec_file = GUI_DIR / "academic_auto_grader.spec"
        cmd = [sys.executable, "-m", "PyInstaller"]
        
        if mode == 'onefile':
            cmd.append("--onefile")
        
        cmd.extend([
            "--clean",
            "--noconfirm",
            str(spec_file)
        ])
        
        # Run PyInstaller
        success = run_command(cmd, cwd=GUI_DIR)
        
        if success:
            print("Build completed successfully!")
            
            # Show output location
            dist_path = GUI_DIR / "dist"
            if dist_path.exists():
                print(f"Built application is in: {dist_path}")
                for item in dist_path.iterdir():
                    print(f"  - {item.name}")
        else:
            print("Build failed!")
            return False
    
    finally:
        os.chdir(original_cwd)
    
    return success

def clean_build():
    """Clean build artifacts"""
    print("Cleaning build artifacts...")
    
    dirs_to_clean = [
        GUI_DIR / "build",
        GUI_DIR / "dist",
        GUI_DIR / "__pycache__",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Removing {dir_path}")
            shutil.rmtree(dir_path)
    
    # Clean .pyc files
    for pyc_file in GUI_DIR.rglob("*.pyc"):
        pyc_file.unlink()
    
    print("Clean completed!")

def create_installer():
    """Create installer packages (placeholder)"""
    print("Creating installer packages...")
    print("Note: Installer creation not yet implemented")
    print("You can manually create installers using:")
    print("  - Windows: Inno Setup, NSIS, or WiX")
    print("  - macOS: create-dmg or productbuild")
    print("  - Linux: AppImage, Flatpak, or distribution packages")

def main():
    parser = argparse.ArgumentParser(description="Build Academic Auto Grader executable")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--version", help="Set version number")
    parser.add_argument("--mode", choices=["onedir", "onefile"], default="onedir",
                       help="Build mode (onedir or onefile)")
    parser.add_argument("--platform", help="Target platform")
    parser.add_argument("--installer", action="store_true", help="Create installer")
    parser.add_argument("--icons-only", action="store_true", help="Only generate icons")
    
    args = parser.parse_args()
    
    # Clean if requested
    if args.clean:
        clean_build()
        if not any([args.version, args.mode, args.installer, args.icons_only]):
            return
    
    # Get version
    version = args.version or get_version()
    
    # Update version files
    if args.version:
        update_version_files(version)
    
    # Generate icons only
    if args.icons_only:
        build_icons()
        return
    
    # Build executable
    if not build_executable(args.platform, args.mode):
        sys.exit(1)
    
    # Create installer
    if args.installer:
        create_installer()
    
    print(f"\nBuild process completed for version {version}!")
    print(f"Build timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()