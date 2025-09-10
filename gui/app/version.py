"""
Application Version and Metadata
Centralized version information for the Academic Auto Grader
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Application metadata
APP_NAME = "Academic Auto Grader"
APP_DESCRIPTION = "Automated Assignment Grading with AI"
APP_AUTHOR = "Academic Auto Grader Team"
APP_EMAIL = "support@academicautograder.com"
APP_URL = "https://github.com/michael-borck/academic-auto-grader"
APP_LICENSE = "MIT"

# Version information
def get_version() -> str:
    """Get application version from VERSION file or git tag"""
    try:
        version_file = PROJECT_ROOT / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        else:
            # Fallback to git tag if available
            try:
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return "1.0.0"  # Default fallback
    except Exception:
        return "1.0.0"

def get_build_info() -> Dict[str, Any]:
    """Get build information including git commit and build date"""
    build_info = {
        'version': get_version(),
        'build_date': None,
        'git_commit': None,
        'git_branch': None,
        'build_type': 'development',
        'is_bundled': hasattr(sys, '_MEIPASS')
    }
    
    try:
        # Get git information
        try:
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                build_info['git_commit'] = result.stdout.strip()
                build_info['build_type'] = 'release' if not result.stdout.strip().startswith('dev') else 'development'
            
            # Get branch name
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                build_info['git_branch'] = result.stdout.strip()
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Get build date (current time for development builds)
        if build_info['is_bundled']:
            # For bundled apps, try to get modification time of the executable
            try:
                exe_path = sys.executable
                if os.path.exists(exe_path):
                    build_timestamp = os.path.getmtime(exe_path)
                    build_info['build_date'] = datetime.fromtimestamp(build_timestamp).isoformat()
            except:
                pass
        
        if not build_info['build_date']:
            build_info['build_date'] = datetime.now().isoformat()
    
    except Exception:
        # If anything fails, use minimal build info
        pass
    
    return build_info

def get_system_info() -> Dict[str, str]:
    """Get system information"""
    import platform
    
    try:
        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Get platform info
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        
        # Get Flet version
        try:
            import flet
            flet_version = flet.__version__
        except (ImportError, AttributeError):
            flet_version = "Unknown"
        
        return {
            "Python": python_version,
            "Platform": f"{system} {release}",
            "Architecture": machine,
            "Flet": flet_version,
            "Bundled": "Yes" if hasattr(sys, '_MEIPASS') else "No"
        }
    except Exception as e:
        return {"Error": str(e)}

def get_app_metadata() -> Dict[str, Any]:
    """Get complete application metadata"""
    build_info = get_build_info()
    system_info = get_system_info()
    
    return {
        'app': {
            'name': APP_NAME,
            'description': APP_DESCRIPTION,
            'version': build_info['version'],
            'author': APP_AUTHOR,
            'email': APP_EMAIL,
            'url': APP_URL,
            'license': APP_LICENSE
        },
        'build': build_info,
        'system': system_info,
        'runtime': {
            'python_version': sys.version,
            'python_executable': sys.executable,
            'platform': sys.platform,
            'argv': sys.argv
        }
    }

# Version constants for easy access
VERSION = get_version()
BUILD_INFO = get_build_info()
SYSTEM_INFO = get_system_info()
APP_METADATA = get_app_metadata()

# Version string for display
VERSION_STRING = f"{APP_NAME} v{VERSION}"
if BUILD_INFO.get('git_commit'):
    VERSION_STRING += f" ({BUILD_INFO['git_commit']})"

# Copyright string
COPYRIGHT_STRING = f"© {datetime.now().year} {APP_AUTHOR}"

def print_version_info():
    """Print comprehensive version information to console"""
    metadata = get_app_metadata()
    
    print(f"{APP_NAME} Version Information")
    print("=" * 50)
    print(f"Version: {metadata['app']['version']}")
    print(f"Build Date: {metadata['build'].get('build_date', 'Unknown')}")
    print(f"Git Commit: {metadata['build'].get('git_commit', 'Unknown')}")
    print(f"Git Branch: {metadata['build'].get('git_branch', 'Unknown')}")
    print(f"Build Type: {metadata['build'].get('build_type', 'Unknown')}")
    print(f"Bundled: {'Yes' if metadata['build']['is_bundled'] else 'No'}")
    print()
    print("System Information:")
    for key, value in metadata['system'].items():
        print(f"  {key}: {value}")
    print()
    print(f"Author: {APP_AUTHOR}")
    print(f"License: {APP_LICENSE}")
    print(f"Website: {APP_URL}")

if __name__ == "__main__":
    print_version_info()