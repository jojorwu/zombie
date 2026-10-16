use pyo3::prelude::*;
use mlua::{Lua, Result as LuaResult};

/// Native Lua Mod Manager in Rust powered by `mlua`.
#[pyclass(unsendable)]
pub struct RustLuaModManager {
    lua: Lua,
}

#[pymethods]
impl RustLuaModManager {
    #[new]
    pub fn new() -> Self {
        let lua = Lua::new();
        RustLuaModManager { lua }
    }

    pub fn load_mod_script(&self, script: &str) -> PyResult<bool> {
        let res: LuaResult<()> = self.lua.load(script).exec();
        Ok(res.is_ok())
    }

    pub fn trigger_event(&self, event_name: &str, arg: u64) -> PyResult<bool> {
        let globals = self.lua.globals();
        if let Ok(func) = globals.get::<_, mlua::Function>(event_name) {
            let _: LuaResult<()> = func.call(arg);
            Ok(true)
        } else {
            Ok(false)
        }
    }
}
