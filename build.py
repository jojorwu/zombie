#!/usr/bin/env python3
"""
Cross-platform 64-bit build script for Zombie AI Simulation executable (x86_64).
Usage: python build.py
"""

import sys
import subprocess
import os
import struct

def build():
    bit_depth = struct.calcsize('P') * 8
    print(f"Building Zombie Simulation 64-bit executable for {sys.platform} ({bit_depth}-bit target)...")
    if bit_depth < 64:
        print("[WARNING] Python interpreter is not 64-bit! Building in 64-bit environment is recommended for full memory access.")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "zombie_sim.spec"
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n64-bit Build successful! Executable is located in the 'dist' directory.")
    else:
        print("\nBuild failed with exit code:", res.returncode)
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
