use pyo3::prelude::*;

#[pyclass]
pub struct RustPNPComplexityEngine {
    #[pyo3(get, set)]
    pub degree: u32,
}

#[pymethods]
impl RustPNPComplexityEngine {
    #[new]
    pub fn new(degree: u32) -> Self {
        RustPNPComplexityEngine { degree }
    }

    pub fn solve_polynomial_knapsack(&self, capacity: f32, weights: Vec<f32>, values: Vec<f32>) -> (f32, Vec<usize>) {
        let n = weights.len();
        if n == 0 || capacity <= 0.0 {
            return (0.0, vec![]);
        }

        // Greedy Value-to-Weight Ratio heuristic
        let mut items: Vec<(usize, f32, f32, f32)> = (0..n)
            .map(|i| {
                let ratio = if weights[i] > 0.0 { values[i] / weights[i] } else { 0.0 };
                (i, weights[i], values[i], ratio)
            })
            .collect();

        items.sort_by(|a, b| b.3.partial_cmp(&a.3).unwrap_or(std::cmp::Ordering::Equal));

        let mut current_weight = 0.0;
        let mut total_value = 0.0;
        let mut selected_indices = Vec::new();

        for (idx, w, v, _) in items {
            if current_weight + w <= capacity {
                current_weight += w;
                total_value += v;
                selected_indices.push(idx);
            }
        }

        (total_value, selected_indices)
    }

    #[staticmethod]
    pub fn verify_3sat(clauses: Vec<(i32, i32, i32)>, assignment: Vec<(i32, bool)>) -> bool {
        let assign_map: std::collections::HashMap<i32, bool> = assignment.into_iter().collect();

        for (l1, l2, l3) in clauses {
            let eval_lit = |lit: i32| -> bool {
                let var = lit.abs();
                let val = *assign_map.get(&var).unwrap_or(&false);
                if lit > 0 { val } else { !val }
            };

            let clause_sat = eval_lit(l1) || eval_lit(l2) || eval_lit(l3);
            if !clause_sat {
                return false;
            }
        }

        true
    }
}
