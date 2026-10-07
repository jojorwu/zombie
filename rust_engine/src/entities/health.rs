use pyo3::prelude::*;

/// Native Anatomical Health & Damage System in Rust.
#[pyclass]
pub struct RustAnatomicalHealth {
    #[pyo3(get, set)]
    pub head: f32,
    #[pyo3(get, set)]
    pub torso: f32,
    #[pyo3(get, set)]
    pub left_arm: f32,
    #[pyo3(get, set)]
    pub right_arm: f32,
    #[pyo3(get, set)]
    pub left_leg: f32,
    #[pyo3(get, set)]
    pub right_leg: f32,
    #[pyo3(get, set)]
    pub bleeding_rate: f32,
}

#[pymethods]
impl RustAnatomicalHealth {
    #[new]
    #[pyo3(signature = (head=35.0, torso=100.0, left_arm=40.0, right_arm=40.0, left_leg=45.0, right_leg=45.0))]
    pub fn new(head: f32, torso: f32, left_arm: f32, right_arm: f32, left_leg: f32, right_leg: f32) -> Self {
        RustAnatomicalHealth {
            head,
            torso,
            left_arm,
            right_arm,
            left_leg,
            right_leg,
            bleeding_rate: 0.0,
        }
    }

    pub fn apply_targeted_damage(&mut self, part: &str, raw_damage: f32, armor_reduction: f32) -> f32 {
        let actual_damage = (raw_damage * (1.0 - armor_reduction)).max(0.0);

        match part {
            "head" => {
                self.head = (self.head - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.05;
            }
            "torso" => {
                self.torso = (self.torso - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.03;
            }
            "left_arm" => self.left_arm = (self.left_arm - actual_damage).max(0.0),
            "right_arm" => self.right_arm = (self.right_arm - actual_damage).max(0.0),
            "left_leg" => {
                self.left_leg = (self.left_leg - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.02;
            }
            "right_leg" => {
                self.right_leg = (self.right_leg - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.02;
            }
            _ => {
                self.torso = (self.torso - actual_damage).max(0.0);
            }
        }

        actual_damage
    }

    pub fn tick_bleeding(&mut self) -> f32 {
        if self.bleeding_rate > 0.0 {
            let bleed_damage = self.bleeding_rate * 0.1;
            self.torso = (self.torso - bleed_damage).max(0.0);
            bleed_damage
        } else {
            0.0
        }
    }

    pub fn get_total_health(&self) -> f32 {
        let max_total = 35.0 * 0.3 + 100.0 * 0.4 + (40.0 + 40.0 + 45.0 + 45.0) * 0.075;
        let cur_total = self.head * 0.3 + self.torso * 0.4 + (self.left_arm + self.right_arm + self.left_leg + self.right_leg) * 0.075;
        ((cur_total / max_total) * 100.0).max(0.0).min(100.0)
    }

    pub fn get_speed_multiplier(&self) -> f32 {
        let min_leg = self.left_leg.min(self.right_leg);
        if min_leg < 30.0 {
            0.4
        } else if min_leg < 60.0 {
            0.7
        } else {
            1.0
        }
    }
}
