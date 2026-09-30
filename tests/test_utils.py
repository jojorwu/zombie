import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from utils.p_np_math import PolynomialVerifier, PNPComplexityEngine
from utils.mod_utility import ModUtility
from utils.dev_utility import DevUtility

class TestUtilitiesAndMath(unittest.TestCase):
    def test_p_np_verifier(self):
        clauses = [(1, 2, -3), (-1, 2, 3)]
        assignment = {1: True, 2: True, 3: False}
        self.assertTrue(PolynomialVerifier.verify_3sat(clauses, assignment))

        numbers = [3, 10, 4, 21, 7]
        target = 14
        certificate = [0, 4]  # 3 + 7 = 10 != 14
        self.assertFalse(PolynomialVerifier.verify_subset_sum(numbers, target, certificate))

        certificate_correct = [1, 2]  # 10 + 4 = 14
        self.assertTrue(PolynomialVerifier.verify_subset_sum(numbers, target, certificate_correct))

    def test_pnp_complexity_engine(self):
        engine = PNPComplexityEngine(degree=3)
        p_bound = engine.polynomial_bound(10)
        np_bound = engine.exponential_bound(10)
        self.assertEqual(p_bound, 1000.0)
        self.assertEqual(np_bound, 1024.0)

        analysis = engine.analyze_p_vs_np([5, 10])
        self.assertEqual(len(analysis), 2)

    def test_mod_utility(self):
        util = ModUtility(mods_dir="mods")
        valid_cnt = util.validate_all_mods()
        self.assertGreaterEqual(valid_cnt, 1)

    def test_dev_utility(self):
        dev = DevUtility()
        bench_res = dev.run_math_benchmarks()
        self.assertIn("matrix_time_ms", bench_res)
        self.assertIn("pnp_time_ms", bench_res)

if __name__ == "__main__":
    unittest.main()
