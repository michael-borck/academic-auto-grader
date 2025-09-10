#!/bin/bash
# Academic Auto Grader - Build Script for Unix-like systems
# Wrapper script for the Python build script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "Academic Auto Grader - Build Script"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if build.py exists
if [ ! -f "build.py" ]; then
    print_error "build.py not found in current directory"
    exit 1
fi

# Make build.py executable if it isn't
chmod +x build.py

# Run the Python build script with all arguments
print_success "Running Python build script..."
python3 build.py "$@"

print_success "Build script completed!"