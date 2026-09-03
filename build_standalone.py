"""
Standalone Executable Builder.

Packages the Python CLI Alarm Clock into a standalone single-file binary
(e.g., 'alarm.exe' on Windows, 'alarm' on macOS/Linux) that runs on any
machine WITHOUT Python installed.

Usage:
  python build_standalone.py
"""

import os
import platform
import subprocess
import sys


def build_executable():
    print("==================================================")
    print("     Python CLI Alarm - Standalone Binary Build   ")
    print("==================================================")

    # Check if pyinstaller is available
    try:
        import PyInstaller
        print(f"✓ PyInstaller found (v{PyInstaller.__version__})")
    except ImportError:
        print("[!] PyInstaller is not installed in the current environment.")
        print("    To generate a standalone .exe, install PyInstaller:")
        print("    pip install pyinstaller")
        print("    Then re-run: python build_standalone.py")
        return 1

    entry_script = os.path.abspath("main.py")
    binary_name = "alarm"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        binary_name,
        "--clean",
        entry_script,
    ]

    print(f"Building standalone binary for {platform.system()}...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe_ext = ".exe" if platform.system() == "Windows" else ""
        dist_path = os.path.join(os.path.abspath("dist"), f"{binary_name}{exe_ext}")
        print()
        print("==================================================")
        print("           BUILD SUCCESSFUL!                      ")
        print("==================================================")
        print(f"Standalone executable generated at:")
        print(f"  {dist_path}")
        print("This file can be distributed and run on any machine")
        print("WITHOUT needing Python installed!")
        print("==================================================")
        return 0
    else:
        print(f"[Error] Build failed with exit code {result.returncode}")
        return result.returncode


if __name__ == "__main__":
    sys.exit(build_executable())
