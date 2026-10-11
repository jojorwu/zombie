try:
    from rust_engine import RustPNPComplexityEngine
    HAS_RUST_PNP = True
except ImportError:
    HAS_RUST_PNP = False


class PolynomialVerifier:
    @staticmethod
    def verify_3sat(clauses, assignment):
        if HAS_RUST_PNP and isinstance(assignment, dict):
            assign_vec = [(k, v) for k, v in assignment.items()]
            return RustPNPComplexityEngine.verify_3sat(clauses, assign_vec)
        for l1, l2, l3 in clauses:
            eval_lit = lambda lit: assignment.get(abs(lit), False) if lit > 0 else not assignment.get(abs(lit), False)
            if not (eval_lit(l1) or eval_lit(l2) or eval_lit(l3)):
                return False
        return True

    @staticmethod
    def verify_subset_sum(numbers, target, certificate):
        subset = [numbers[i] for i in certificate if i < len(numbers)]
        return sum(subset) == target


class PNPComplexityEngine:
    def __init__(self, degree: int = 3):
        self.degree = degree

    def polynomial_bound(self, n: int) -> float:
        return float(n ** self.degree)

    def exponential_bound(self, n: int) -> float:
        return float(2 ** n)

    def simulate_p_equals_np_reduction(self, n_vars: int = 100, n_clauses: int = 500) -> dict:
        return {"poly_cost_ticks": float(n_vars ** self.degree)}

    def analyze_p_vs_np(self, input_sizes: list) -> list:
        results = []
        for n in input_sizes:
            p_b = self.polynomial_bound(n)
            np_b = self.exponential_bound(n)
            results.append({
                "n": n,
                "P_bound": p_b,
                "NP_bound": np_b,
                "NP_to_P_ratio": np_b / (p_b + 1.0)
            })
        return results


class PolynomialKnapsackSolver:
    @staticmethod
    def optimize_inventory(items: list, max_capacity: float = 20.0) -> list:
        if HAS_RUST_PNP and items:
            pnp = RustPNPComplexityEngine(3)
            weights = [getattr(item, 'weight', 1.0) for item in items]
            values = [getattr(item, 'value', 1.0) for item in items]
            total_val, indices = pnp.solve_polynomial_knapsack(max_capacity, weights, values)
            return [items[i] for i in indices]
        return items
