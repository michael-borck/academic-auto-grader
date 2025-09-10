@echo off
REM Academic Auto Grader - Build Script for Windows
REM Wrapper script for the Python build script

setlocal enabledelayedexpansion

echo.
echo ============================================
echo  Academic Auto Grader - Build Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and ensure it's in your PATH
    pause
    exit /b 1
)

REM Check if build.py exists
if not exist "build.py" (
    echo ❌ build.py not found in current directory
    pause
    exit /b 1
)

REM Run the Python build script with all arguments
echo ✅ Running Python build script...
python build.py %*

if errorlevel 1 (
    echo.
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo ✅ Build script completed!
pause