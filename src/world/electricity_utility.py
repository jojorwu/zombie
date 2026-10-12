try:
    from rust_engine import RustElectricityUtility
    RUST_ELEC_AVAILABLE = True
except ImportError:
    RUST_ELEC_AVAILABLE = False


class ElectricityUtility:
    def __init__(self, cutoff_day: int = 7, grid_enabled: bool = True):
        self.cutoff_day = cutoff_day
        self.grid_enabled = grid_enabled

    def is_power_active(self, current_day: int) -> bool:
        if not self.grid_enabled:
            return False
        return current_day < self.cutoff_day

    def update_generators(self):
        pass
