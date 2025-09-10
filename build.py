#!/usr/bin/env python3
"""
Academic Auto Grader - Build Script
Cross-platform build automation using PyInstaller
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import argparse
import time

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_step(text):
    """Print a formatted step"""
    print(f"\n🔧 {text}")

def print_success(text):
    """Print a success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print a warning message"""
    print(f"⚠️  {text}")

def run_command(cmd, description="", check=True):
    """Run a command and handle errors"""
    if description:
        print_step(description)
    
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            check=check,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print("Output:", result.stdout.strip())
        
        if result.stderr and result.returncode == 0:
            print("Warnings:", result.stderr.strip())
        
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            print("stdout:", e.stdout)
        if e.stderr:
            print("stderr:", e.stderr)
        if check:
            sys.exit(1)
        return e

def get_platform_info():
    """Get platform-specific information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    return {
        'system': system,
        'machine': machine,
        'is_windows': system == 'windows',
        'is_macos': system == 'darwin',
        'is_linux': system == 'linux',
        'is_64bit': machine in ['x86_64', 'amd64', 'arm64'],
    }

def check_dependencies():
    """Check if required dependencies are installed"""
    print_step("Checking dependencies")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8 or higher is required")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} ✓")
    
    # Check PyInstaller
    try:
        result = run_command([sys.executable, "-m", "PyInstaller", "--version"], check=False)
        if result.returncode == 0:
            print_success(f"PyInstaller {result.stdout.strip()} ✓")
        else:
            print_error("PyInstaller not found. Install with: pip install pyinstaller")
            sys.exit(1)
    except FileNotFoundError:
        print_error("PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    
    # Check UPX (optional)
    try:
        result = run_command(["upx", "--version"], check=False)
        if result.returncode == 0:
            print_success("UPX available for compression ✓")
            return True
    except FileNotFoundError:
        print_warning("UPX not found - builds will be larger. Install UPX for compression.")
        return False
    
    return True

def clean_build_dirs(project_root):
    """Clean previous build artifacts"""
    print_step("Cleaning previous build artifacts")
    
    dirs_to_clean = [
        "build",
        "dist",
        "__pycache__",
    ]
    
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Removed {dir_path}")
    
    # Clean .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        pyc_file.unlink()
    
    print_success("Build directories cleaned")

def select_spec_file(platform_info, target_platform=None):
    """Select the appropriate spec file based on platform"""
    if target_platform:
        spec_file = f"build-{target_platform}.spec"
    elif platform_info['is_windows']:
        spec_file = "build-windows.spec"
    elif platform_info['is_macos']:
        spec_file = "build-macos.spec"
    elif platform_info['is_linux']:
        spec_file = "build-linux.spec"
    else:
        spec_file = "academic-auto-grader.spec"  # Fallback
    
    return spec_file

def build_application(project_root, platform_info, args):
    """Build the application using PyInstaller"""
    print_step("Building application")
    
    # Select spec file
    spec_file = select_spec_file(platform_info, args.platform)
    spec_path = project_root / spec_file
    
    if not spec_path.exists():
        print_error(f"Spec file not found: {spec_path}")
        sys.exit(1)
    
    print(f"Using spec file: {spec_file}")
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(spec_path),
        "--clean",
    ]
    
    if args.debug:
        cmd.append("--debug=all")
    
    # Note: --noupx and --onefile options are controlled by the spec file
    if args.no_upx:
        print_warning("UPX compression controlled by spec file settings")
    
    if args.onefile:
        print_warning("One-file mode controlled by spec file settings")
    
    # Run build
    start_time = time.time()
    result = run_command(cmd, "Building application with PyInstaller")
    build_time = time.time() - start_time
    
    if result.returncode == 0:
        print_success(f"Build completed in {build_time:.1f} seconds")
        return True
    else:
        print_error("Build failed")
        return False

def check_build_output(project_root, platform_info):
    """Check and report on build output"""
    print_step("Checking build output")
    
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        print_error("Build output directory not found")
        return False
    
    # Find the main executable
    app_name = "AcademicAutoGrader"
    
    if platform_info['is_windows']:
        executable = dist_dir / app_name / f"{app_name}.exe"
    elif platform_info['is_macos']:
        executable = dist_dir / f"{app_name}.app"
    else:
        executable = dist_dir / app_name / app_name
    
    if executable.exists():
        if executable.is_file():
            size_mb = executable.stat().st_size / (1024 * 1024)
            print_success(f"Executable created: {executable} ({size_mb:.1f} MB)")
        else:
            # Directory (macOS app bundle)
            print_success(f"Application bundle created: {executable}")
        
        return True
    else:
        print_error(f"Executable not found: {executable}")
        return False

def create_distribution_package(project_root, platform_info, args):
    """Create distribution package"""
    if not args.package:
        return
    
    print_step("Creating distribution package")
    
    # Implementation would create zip/tar.gz archives
    # For now, just report what would be done
    print("📦 Distribution packaging would create:")
    if platform_info['is_windows']:
        print("  - Windows installer (.msi)")
        print("  - Portable zip archive")
    elif platform_info['is_macos']:
        print("  - macOS disk image (.dmg)")
        print("  - Signed application bundle")
    elif platform_info['is_linux']:
        print("  - AppImage")
        print("  - Debian package (.deb)")
        print("  - RPM package (.rpm)")
    
    print_warning("Distribution packaging not yet implemented")

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description="Build Academic Auto Grader")
    parser.add_argument("--platform", choices=["windows", "macos", "linux"], 
                       help="Target platform (default: current platform)")
    parser.add_argument("--clean", action="store_true", 
                       help="Clean build artifacts before building")
    parser.add_argument("--debug", action="store_true", 
                       help="Build with debug information")
    parser.add_argument("--no-upx", action="store_true", 
                       help="Disable UPX compression")
    parser.add_argument("--onefile", action="store_true", 
                       help="Create one-file executable (not recommended)")
    parser.add_argument("--package", action="store_true", 
                       help="Create distribution packages")
    parser.add_argument("--test", action="store_true", 
                       help="Test the built application")
    
    args = parser.parse_args()
    
    # Get platform information
    platform_info = get_platform_info()
    project_root = Path(__file__).parent
    
    print_header("Academic Auto Grader - Build Script")
    print(f"Platform: {platform_info['system']} ({platform_info['machine']})")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Project: {project_root}")
    
    # Check dependencies
    upx_available = check_dependencies()
    
    # Clean if requested
    if args.clean:
        clean_build_dirs(project_root)
    
    # Build application
    success = build_application(project_root, platform_info, args)
    
    if success:
        # Check build output
        check_build_output(project_root, platform_info)
        
        # Create distribution package
        create_distribution_package(project_root, platform_info, args)
        
        # Test if requested
        if args.test:
            print_step("Testing built application")
            print_warning("Application testing not yet implemented")
        
        print_header("Build Completed Successfully!")
        print("📁 Build outputs are in the 'dist' directory")
        print("🚀 Ready for distribution!")
        
    else:
        print_header("Build Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()