use pyo3::prelude::*;
use std::collections::HashMap;

pub mod container;
pub mod health;
pub mod survivor;
pub mod vehicle;
pub mod zombie;

pub use container::{RustContainerUtility, RustFoodSpoilageUtility};
pub use health::RustAnatomicalHealth;
pub use survivor::RustSurvivorEntity;
pub use vehicle::RustVehiclePhysics;
pub use zombie::RustZombieEngine;

#[derive(Clone, Debug)]
pub enum EntityType {
    Survivor,
    Zombie,
    Vehicle,
    Animal,
    Item,
}

#[derive(Clone, Debug)]
pub struct EntityComponent {
    pub id: u64,
    pub entity_type: EntityType,
    pub x: f32,
    pub y: f32,
    pub z: i32,
    pub hp: f32,
    pub active: bool,
}

/// Unified Entity Component System Manager in Rust.
#[pyclass]
pub struct RustEntityManager {
    next_id: u64,
    entities: HashMap<u64, EntityComponent>,
}

#[pymethods]
impl RustEntityManager {
    #[new]
    pub fn new() -> Self {
        RustEntityManager {
            next_id: 1,
            entities: HashMap::new(),
        }
    }

    pub fn register_entity(&mut self, entity_type_str: &str, x: f32, y: f32, z: i32, hp: f32) -> u64 {
        let etype = match entity_type_str {
            "survivor" => EntityType::Survivor,
            "zombie" => EntityType::Zombie,
            "vehicle" => EntityType::Vehicle,
            "animal" => EntityType::Animal,
            _ => EntityType::Item,
        };

        let id = self.next_id;
        self.next_id += 1;

        let comp = EntityComponent {
            id,
            entity_type: etype,
            x,
            y,
            z,
            hp,
            active: true,
        };

        self.entities.insert(id, comp);
        id
    }

    pub fn update_position(&mut self, id: u64, x: f32, y: f32, z: i32) -> bool {
        if let Some(e) = self.entities.get_mut(&id) {
            e.x = x;
            e.y = y;
            e.z = z;
            true
        } else {
            false
        }
    }

    pub fn get_entity_pos(&self, id: u64) -> Option<(f32, f32, i32)> {
        self.entities.get(&id).map(|e| (e.x, e.y, e.z))
    }

    pub fn get_active_count(&self) -> usize {
        self.entities.values().filter(|e| e.active).count()
    }
}
