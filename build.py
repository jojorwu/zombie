#!/usr/bin/env python3
"""
Cross-platform build script for Zombie AI Simulation executable (Windows and Linux).
Usage: python build.py
"""

import sys
import subprocess
import os

def build():
    print(f"Building Zombie Simulation executable for {sys.platform}...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "zombie_sim.spec"
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\nBuild successful! Executable is located in the 'dist' directory.")
    else:
        print("\nBuild failed with exit code:", res.returncode)
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
