#!/usr/bin/env python3
"""
Cross-platform 64-bit build script for Zombie AI Simulation executable (x86_64).
Usage: python build.py
"""

import sys
import subprocess
import os
import struct

import platform

def build():
    bit_depth = struct.calcsize('P') * 8
    arch = platform.machine()
    os_name = sys.platform
    print(f"Building Zombie Simulation executable for OS: '{os_name}', Arch: '{arch}' ({bit_depth}-bit target)...")
    if bit_depth < 64:
        print("[WARNING] Python interpreter is not 64-bit! Building in 64-bit environment is recommended for full memory access.")

    # 1. Compile native Rust crate
    print("\n[1/2] Compiling Rust engine crate (crates/rust_engine)...")
    cargo_cmd = ["cargo", "build", "--release"]
    cargo_res = subprocess.run(cargo_cmd)
    if cargo_res.returncode != 0:
        print("[ERROR] Cargo build failed!")
        sys.exit(cargo_res.returncode)

    # Copy binary to rust_engine.pyd / rust_engine.so
    import shutil
    if sys.platform == "win32":
        shutil.copyfile("target/release/rust_engine.dll", "rust_engine.pyd")
    else:
        shutil.copyfile("target/release/librust_engine.so", "rust_engine.so")

    print("[2/2] Packaging with PyInstaller...")
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
