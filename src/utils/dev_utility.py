#!/usr/bin/env python3
"""
Utility 2: Development & Optimization Utility Tool for Python/Rust/Lua Codebase.
Runs math benchmarks, P=NP complexity scaling analysis, and codebase health checks.
Usage: python -m src.utils.dev_utility [command]
"""

import sys
import os
import time
import numpy as np
import torch
from src.utils.p_np_math import PNPComplexityEngine, PolynomialVerifier


class DevUtility:
    def __init__(self):
        self.pnp_engine = PNPComplexityEngine(degree=3)

    def run_math_benchmarks(self):
        print("==================================================")
        print("  DEV UTILITY: High-Speed Math & GPU/CPU Benchmark")
        print("==================================================")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {device}")

        # Benchmark 1: Large Matrix Multiplication
        start = time.time()
        a = torch.randn(1000, 1000, device=device)
        b = torch.randn(1000, 1000, device=device)
        c = torch.matmul(a, b)
        if device == "cuda":
            torch.cuda.synchronize()
        matrix_time = time.time() - start
        print(f"[Benchmark] 1000x1000 Tensor MatMul Time: {matrix_time * 1000:.2f} ms")

        # Benchmark 2: P=NP Polynomial Reduction Simulation
        start = time.time()
        pnp_res = self.pnp_engine.simulate_p_equals_np_reduction(n_vars=100, n_clauses=500)
        pnp_time = time.time() - start
        print(f"[Benchmark] P=NP Reduction Simulation Time: {pnp_time * 1000:.2f} ms")
        print(f"  Poly Cost Ticks: {pnp_res['poly_cost_ticks']:.1f}")

        # Benchmark 3: 3-SAT Verifier
        clauses = [(1, 2, -3), (-1, 2, 3), (1, -2, -3)]
        assignment = {1: True, 2: False, 3: False}
        is_sat = PolynomialVerifier.verify_3sat(clauses, assignment)
        print(f"[Verifier] 3-SAT Certificate Verification Result: {is_sat}")

        return {
            "matrix_time_ms": matrix_time * 1000,
            "pnp_time_ms": pnp_time * 1000,
            "sat_verified": is_sat
        }

    def analyze_complexity(self, input_sizes=None):
        if input_sizes is None:
            input_sizes = [5, 10, 20, 30, 50]
        print("\n==================================================")
        print("  P vs NP Complexity Scaling Analysis")
        print("==================================================")
        analysis = self.pnp_engine.analyze_p_vs_np(input_sizes)
        for row in analysis:
            n = row['n']
            p_b = row['P_bound']
            np_b = row['NP_bound']
            ratio = row['NP_to_P_ratio']
            print(f"  N={n:2d} | P(N)=O(N^3): {p_b:10.0f} ticks | NP(N)=O(2^N): {np_b:15.0f} ticks | NP/P Ratio: {ratio:.1f}x")
        return analysis

    def inspect_codebase(self):
        print("\n==================================================")
        print("  Codebase Structure & Architecture Inspector")
        print("==================================================")
        dirs_to_check = ["src", "mods", "tests"]
        for d in dirs_to_check:
            if os.path.exists(d):
                files = os.listdir(d)
                print(f"Directory '{d}/': {len(files)} items -> {files[:5]}")
            else:
                print(f"Directory '{d}/': NOT FOUND")

def main():
    dev = DevUtility()
    dev.run_math_benchmarks()
    dev.analyze_complexity()
    dev.inspect_codebase()

if __name__ == "__main__":
    main()
