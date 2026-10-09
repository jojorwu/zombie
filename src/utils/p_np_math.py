import math
import numpy as np
from src.entities.item import ResourceItem
from src.utils.container_utility import ContainerUtility


try:
    from rust_engine import RustPNPComplexityEngine
    RUST_PNP_AVAILABLE = True
except ImportError:
    RUST_PNP_AVAILABLE = False


class PolynomialVerifier:
    """
    Polynomial-time verifier for NP problem certificates.
    An NP problem is in P if there exists a polynomial-time algorithm to solve it directly.
    """
    @staticmethod
    def verify_3sat(clauses, assignment):
        if RUST_PNP_AVAILABLE:
            assign_vec = [(k, v) for k, v in assignment.items()]
            clauses_vec = [tuple(c) for c in clauses]
            return RustPNPComplexityEngine.verify_3sat(clauses_vec, assign_vec)

        for c in clauses:
            clause_satisfied = False
            for lit in c:
                var = abs(lit)
                val = assignment.get(var, False)
                if lit < 0:
                    val = not val
                if val:
                    clause_satisfied = True
                    break
            if not clause_satisfied:
                return False
        return True

    @staticmethod
    def verify_subset_sum(numbers, target, certificate):
        subset = [numbers[i] for i in certificate if 0 <= i < len(numbers)]
        return sum(subset) == target

    @staticmethod
    def verify_spatial_partitioning(coords, cell_size=16.0):
        if coords is None or len(coords) == 0:
            return True
        grid = {}
        for x, y in coords:
            cell = (int(x // cell_size), int(y // cell_size))
            grid.setdefault(cell, 0)
            grid[cell] += 1
        return len(grid) > 0


class PolynomialKnapsackSolver:
    """
    Polynomial / Pseudo-Polynomial O(N * W) Dynamic Programming solver for NP-Hard 0/1 Knapsack.
    Used by survivors to optimize inventory item selection based on item weight (kg) vs survival utility value.
    """
    ITEM_VALUES = {
        ResourceItem.MEDKIT: 100.0,
        ResourceItem.PISTOL: 80.0,
        ResourceItem.RIFLE: 90.0,
        ResourceItem.SHOTGUN: 85.0,
        ResourceItem.PISTOL_AMMO: 60.0,
        ResourceItem.RIFLE_AMMO: 70.0,
        ResourceItem.SHOTGUN_SHELLS: 65.0,
        ResourceItem.CANNED_FOOD: 50.0,
        ResourceItem.MRE: 75.0,
        ResourceItem.WATER_BOTTLE: 55.0,
        ResourceItem.AXE: 40.0,
        ResourceItem.CROWBAR: 35.0,
        ResourceItem.KNIFE: 30.0,
        ResourceItem.CHEF_KNIFE: 25.0,
        ResourceItem.BREAD: 20.0,
        ResourceItem.APPLE: 15.0,
        ResourceItem.WOOD: 10.0,
        ResourceItem.METAL: 10.0,
        ResourceItem.FUEL: 45.0,
        ResourceItem.FOOD: 25.0,
        ResourceItem.WATER: 25.0,
        ResourceItem.WEAPON: 30.0,
    }

    @classmethod
    def optimize_inventory(cls, item_list, max_capacity=20):
        if not item_list:
            return []

        formatted_items = []
        for item in item_list:
            itype = item.item_type if hasattr(item, 'item_type') else item
            val = cls.ITEM_VALUES.get(itype, 10.0)
            weight = max(1, int(round(ContainerUtility.get_item_weight(itype) * 2.0)))
            formatted_items.append((itype, weight, val, item))

        n = len(formatted_items)
        w_max = int(round(max_capacity * 2.0))

        dp = np.zeros((n + 1, w_max + 1), dtype=np.float32)

        for i in range(1, n + 1):
            itype, weight, val, _obj = formatted_items[i - 1]
            for w in range(w_max + 1):
                if weight <= w:
                    dp[i, w] = max(dp[i - 1, w], dp[i - 1, w - weight] + val)
                else:
                    dp[i, w] = dp[i - 1, w]

        selected_items = []
        w = w_max
        for i in range(n, 0, -1):
            if not math.isclose(float(dp[i, w]), float(dp[i - 1, w]), abs_tol=1e-4):
                selected_items.append(formatted_items[i - 1][3])
                w -= formatted_items[i - 1][1]

        return selected_items


class PolynomialTSPSolver:
    """
    Polynomial-time O(N^2) 2-Opt Heuristic Solver for Traveling Salesperson Problem (TSP).
    Used by survivors to plan optimal multi-destination looting routes between buildings.
    """
    @staticmethod
    def compute_optimal_route(waypoints):
        if not waypoints or len(waypoints) <= 2:
            return list(waypoints)

        unvisited = list(waypoints[1:])
        route = [waypoints[0]]

        while unvisited:
            curr = route[-1]
            best_idx = 0
            min_dist = float('inf')
            for i, p in enumerate(unvisited):
                d = math.hypot(p[0] - curr[0], p[1] - curr[1]) + abs(p[2] - curr[2]) * 3.0
                if d < min_dist:
                    min_dist = d
                    best_idx = i
            route.append(unvisited.pop(best_idx))

        num_pts = len(route)
        improved = True
        passes = 0
        while improved and passes < 5:
            improved = False
            passes += 1
            for i in range(1, num_pts - 2):
                for j in range(i + 1, num_pts - 1):
                    p1, p2 = route[i - 1], route[i]
                    p3, p4 = route[j], route[j + 1]

                    d1 = (math.hypot(p1[0] - p2[0], p1[1] - p2[1]) + abs(p1[2] - p2[2]) * 3.0 +
                          math.hypot(p3[0] - p4[0], p3[1] - p4[1]) + abs(p3[2] - p4[2]) * 3.0)
                    d2 = (math.hypot(p1[0] - p3[0], p1[1] - p3[1]) + abs(p1[2] - p3[2]) * 3.0 +
                          math.hypot(p2[0] - p4[0], p2[1] - p4[1]) + abs(p2[2] - p4[2]) * 3.0)

                    if d2 < d1:
                        route[i:j + 1] = reversed(route[i:j + 1])
                        improved = True

        return route


class PNPComplexityEngine:
    """
    Mathematical engine analyzing P vs NP complexity scaling and polynomial reduction bounds.
    Formula: P = NP iff Boolean Satisfiability (3-SAT) is solvable in polynomial time O(N^k).
    """
    def __init__(self, degree=3):
        self.degree = degree

    def polynomial_bound(self, n):
        return float(n ** self.degree)

    def exponential_bound(self, n):
        return float(2 ** n) if n < 100 else float('inf')

    def analyze_p_vs_np(self, input_sizes):
        results = []
        for n in input_sizes:
            p_time = self.polynomial_bound(n)
            np_time = self.exponential_bound(n)
            ratio = np_time / p_time if p_time > 0 else 0.0
            results.append({
                "n": n,
                "P_bound": p_time,
                "NP_bound": np_time,
                "NP_to_P_ratio": ratio
            })
        return results

    def simulate_p_equals_np_reduction(self, n_vars, n_clauses):
        matrix = np.random.randn(n_vars, n_vars)
        eigenvalues = np.linalg.eigvals(matrix)
        poly_cost = (n_vars ** 2.5) + (n_clauses ** 1.5)
        return {
            "n_vars": n_vars,
            "n_clauses": n_clauses,
            "poly_cost_ticks": float(poly_cost),
            "max_eigenvalue": float(np.max(np.abs(eigenvalues)))
        }
