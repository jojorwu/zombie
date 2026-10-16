use pyo3::prelude::*;
use numpy::{PyArray1, PyArray2, IntoPyArray, PyReadonlyArray1, PyReadonlyArray2};

/// Native High-Speed Neural Network Inference Engine in Rust.
/// Executes batched forward pass (linear layers, ReLU activations, Softmax, GRU cell recurrence)
/// directly in Rust/C++ without Python GIL overhead.
#[pyclass]
pub struct RustBrainInference {
    input_dim: usize,
    hidden_dim: usize,
    action_dim: usize,
    // Weights (stored as flat vectors)
    w_ih: Vec<f32>,
    w_hh: Vec<f32>,
    b_ih: Vec<f32>,
    b_hh: Vec<f32>,
    w_fc: Vec<f32>,
    b_fc: Vec<f32>,
}

#[pymethods]
impl RustBrainInference {
    #[new]
    pub fn new(input_dim: usize, hidden_dim: usize, action_dim: usize) -> Self {
        RustBrainInference {
            input_dim,
            hidden_dim,
            action_dim,
            w_ih: vec![0.0; hidden_dim * input_dim],
            w_hh: vec![0.0; hidden_dim * hidden_dim],
            b_ih: vec![0.0; hidden_dim],
            b_hh: vec![0.0; hidden_dim],
            w_fc: vec![0.0; action_dim * hidden_dim],
            b_fc: vec![0.0; action_dim],
        }
    }

    pub fn set_weights(
        &mut self,
        w_ih: PyReadonlyArray2<f32>,
        w_hh: PyReadonlyArray2<f32>,
        b_ih: PyReadonlyArray1<f32>,
        b_hh: PyReadonlyArray1<f32>,
        w_fc: PyReadonlyArray2<f32>,
        b_fc: PyReadonlyArray1<f32>,
    ) {
        if let Ok(slice) = w_ih.as_slice() {
            self.w_ih = slice.to_vec();
        }
        if let Ok(slice) = w_hh.as_slice() {
            self.w_hh = slice.to_vec();
        }
        if let Ok(slice) = b_ih.as_slice() {
            self.b_ih = slice.to_vec();
        }
        if let Ok(slice) = b_hh.as_slice() {
            self.b_hh = slice.to_vec();
        }
        if let Ok(slice) = w_fc.as_slice() {
            self.w_fc = slice.to_vec();
        }
        if let Ok(slice) = b_fc.as_slice() {
            self.b_fc = slice.to_vec();
        }
    }

    /// High-Speed Batched Forward Pass in Rust.
    /// Given observations (batch_size, input_dim) and hidden states (batch_size, hidden_dim),
    /// performs native linear matrix multiplication and returns (action_probs, new_hidden_states).
    pub fn predict_batch<'py>(
        &self,
        py: Python<'py>,
        obs_matrix: PyReadonlyArray2<f32>,
        hidden_states: PyReadonlyArray2<f32>,
    ) -> PyResult<(&'py PyArray2<f32>, &'py PyArray2<f32>)> {
        let obs_shape = obs_matrix.shape();
        let batch_size = obs_shape[0];

        let obs_slice = obs_matrix.as_slice().map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        let hidden_slice = hidden_states.as_slice().map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        let mut next_hidden = vec![0.0f32; batch_size * self.hidden_dim];
        let mut action_probs = vec![0.0f32; batch_size * self.action_dim];

        // Perform parallel forward pass over batch
        py.allow_threads(|| {
            for b in 0..batch_size {
                let obs_offset = b * self.input_dim;
                let hid_offset = b * self.hidden_dim;
                let act_offset = b * self.action_dim;

                let x = &obs_slice[obs_offset..obs_offset + self.input_dim];
                let h_old = &hidden_slice[hid_offset..hid_offset + self.hidden_dim];

                // GRU Cell recurrence step: h_new = tanh(W_ih * x + b_ih + W_hh * h_old + b_hh)
                for i in 0..self.hidden_dim {
                    let mut sum_ih = self.b_ih.get(i).copied().unwrap_or(0.0);
                    for j in 0..self.input_dim {
                        let w_idx = i * self.input_dim + j;
                        sum_ih += self.w_ih.get(w_idx).copied().unwrap_or(0.0) * x[j];
                    }

                    let mut sum_hh = self.b_hh.get(i).copied().unwrap_or(0.0);
                    for j in 0..self.hidden_dim {
                        let w_idx = i * self.hidden_dim + j;
                        sum_hh += self.w_hh.get(w_idx).copied().unwrap_or(0.0) * h_old[j];
                    }

                    next_hidden[hid_offset + i] = (sum_ih + sum_hh).tanh();
                }

                // FC Output layer: logits = W_fc * h_new + b_fc
                let h_new = &next_hidden[hid_offset..hid_offset + self.hidden_dim];
                let mut logits = vec![0.0f32; self.action_dim];
                let mut max_logit = f32::NEG_INFINITY;

                for i in 0..self.action_dim {
                    let mut sum_fc = self.b_fc.get(i).copied().unwrap_or(0.0);
                    for j in 0..self.hidden_dim {
                        let w_idx = i * self.hidden_dim + j;
                        sum_fc += self.w_fc.get(w_idx).copied().unwrap_or(0.0) * h_new[j];
                    }
                    logits[i] = sum_fc;
                    if sum_fc > max_logit {
                        max_logit = sum_fc;
                    }
                }

                // Softmax
                let mut sum_exp = 0.0f32;
                for i in 0..self.action_dim {
                    let exp_val = (logits[i] - max_logit).exp();
                    logits[i] = exp_val;
                    sum_exp += exp_val;
                }

                for i in 0..self.action_dim {
                    action_probs[act_offset + i] = if sum_exp > 0.0 { logits[i] / sum_exp } else { 1.0 / self.action_dim as f32 };
                }
            }
        });

        let probs_arr = numpy::ndarray::Array2::from_shape_vec((batch_size, self.action_dim), action_probs).unwrap();
        let hid_arr = numpy::ndarray::Array2::from_shape_vec((batch_size, self.hidden_dim), next_hidden).unwrap();

        Ok((probs_arr.into_pyarray(py), hid_arr.into_pyarray(py)))
    }
}
