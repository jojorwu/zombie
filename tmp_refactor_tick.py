import re

src = open("src/simulation/engine.py").read()

start = src.index("    def tick(self) -> None:")
# find the next top-level method after tick: "    def end_generation"
end = src.index("    def end_generation", start)
tick_body = src[start:end]

lines = tick_body.split("\n")
# strip the first line (def tick...) and trailing blank lines handled later
body_lines = lines[1:]

def find_line(pred, start_idx=0):
    for i in range(start_idx, len(body_lines)):
        if pred(body_lines[i]):
            return i
    raise ValueError("not found")

# --- locate phase boundaries by unique anchor strings ---
i_periodic = find_line(lambda l: l.strip().startswith("if self.world.current_tick % 100 == 0:"))
i_chunk_hdr = find_line(lambda l: "--- Chunk streaming" in l)
i_noise = find_line(lambda l: l.strip().startswith("active_noises: list[NoiseEvent] = []"))
i_alive = find_line(lambda l: l.strip().startswith("alive_indices: list[int]"))
i_surv_hdr = find_line(lambda l: "--- Survivor decision phase" in l)
i_scent_emit = find_line(lambda l: "if s.is_alive and not s.in_vehicle" in l) - 1
i_scent_upd = find_line(lambda l: l.strip().startswith("active_scents: list[ScentTrail] = []"))
i_zomb_hdr = find_line(lambda l: "--- Zombie AI / flocking phase" in l)
i_coll_hdr = find_line(lambda l: "Vehicle-Zombie Momentum Collision Processing" in l)
i_animals = find_line(lambda l: l.strip().startswith("for animal in self.animals:"))
i_respawn = find_line(lambda l: l.strip().startswith("self.env_manager.check_dynamic_item_respawn"))
i_final_sync = find_line(lambda l: "if (self.rust_bridge.rust_active and zombie_state_changed" in l)
i_monitor = find_line(lambda l: l.strip().startswith("self.memory_monitor.record_tick_time"))

def seg(a, b):
    """body_lines[a:b] joined, dedented-safe (all are >=8 spaces)."""
    return "\n".join(body_lines[a:b]).rstrip()

PERIODIC = seg(i_periodic, i_chunk_hdr)
CHUNK = seg(i_chunk_hdr, i_noise)
NOISE = seg(i_noise, i_alive)
SURVIVOR = seg(i_surv_hdr, i_scent_emit)
SCENT = seg(i_scent_emit, i_zomb_hdr)
ZOMBIE = seg(i_zomb_hdr, i_coll_hdr)
COLLISION = seg(i_coll_hdr, i_animals)
POST = seg(i_animals, i_final_sync)
FINALSYNC = seg(i_final_sync, i_monitor)

# --- build new methods ---
def indent(s):
    return s

new_methods = f'''    def _tick_periodic_maintenance(self) -> bool:
        """Every-100-tick housekeeping: state-manager purges + death cleanup.

        Returns ``zombie_state_changed``: True when the tick mutated zombie
        hp/roster, which forces the fused bridge pipeline to re-sync Rust.
        The original code seeded that flag from this block's schedule; we
        keep the exact same trigger condition (the every-100th tick).
        """
{indent(PERIODIC)}
        return self.world.current_tick % 100 == 0

    def _tick_chunk_streaming(self) -> tuple[bool, list[tuple[float, float]]]:
        """Freeze/rehydrate entities around the active-chunk window.

        Runs BEFORE the survivor-phase bridge crossing so the fused sync sees
        the final active roster (plan item 6: one crossing per phase).
        Returns ``(roster_changed, entity_positions)``.
        """
{indent(CHUNK)}
        return roster_changed, entity_positions

    def _tick_decay_streams(self) -> list[NoiseEvent]:
        """Age noise events and scent trails, recycling expired ones via pools."""
{indent(NOISE)}
{indent(SCENT)}
        return active_noises

    def _tick_survivor_phase(self, alive_indices: list[int]) -> None:
        """Neural-net decisions + one fused Python<->Rust crossing.

        With the native core, Rust owns ALL survivor game logic (vitals,
        looting, crafting, combat, flocking, noise) and Python only runs the
        network on the zero-copy (N, 57) observation matrix. The legacy
        pure-Python branch is the fallback for builds without rust_engine.
        """
{indent(SURVIVOR)}

    def _tick_zombie_phase(self, roster_changed: bool, zombie_state_changed: bool,
                           chunk_size: int, active_chunk_coords: set) -> bool:
        """Zombie AI/flocking through the fused bridge path (or legacy Python).

        Returns the updated ``zombie_state_changed`` flag.
        """
{indent(ZOMBIE)}
        return zombie_state_changed

    def _tick_vehicle_collisions(self, collision_zombies: list[Any], chunk_size: int,
                                 active_chunk_coords: set) -> bool:
        """Momentum collisions between occupied vehicles and active zombies.

        Python mutates zombie hp/velocity here, which forces a corrective
        push into Rust at the end of the tick. Returns the updated
        ``zombie_state_changed`` flag.
        """
{indent(COLLISION)}
        return zombie_state_changed
'''

# --- assemble new tick() ---
new_tick = '''    def tick(self) -> None:
        """One ECS-style simulation step, split into testable phases.

        Pipeline order matters: periodic maintenance -> chunk streaming ->
        noise decay -> survivor decision phase (fused bridge crossing) ->
        scent emission/decay -> zombie flocking phase -> vehicle collisions
        -> animals/respawn/snapshot -> corrective Rust sync -> telemetry.
        Each phase is a private ``_tick_*`` method so it can be unit-tested
        in isolation (plan item 11: tick() was a 234-line monolith).
        """
        t0: float = time.time()

        self.env_manager.tick_environment()
        self.mod_manager.trigger_event("on_tick", self.world.current_tick)
        self.event_bus.process_events()

        zombie_state_changed: bool = self._tick_periodic_maintenance()
        roster_changed, _ = self._tick_chunk_streaming()
        self.noise_events = self._tick_decay_streams()

        alive_indices: list[int] = [i for i, s in enumerate(self.survivors) if s.is_alive]
        alive_count: int = len(alive_indices)
        self._tick_survivor_phase(alive_indices)

        chunk_size: int = self.world.chunk_manager.chunk_size
        active_chunk_coords: set[tuple[int, int]] = self.world.chunk_manager.active_chunks
        zombie_state_changed = self._tick_zombie_phase(
            roster_changed, zombie_state_changed, chunk_size, active_chunk_coords
        )

        collision_zombies: list[Any] = [
            z for z in self.zombies
            if z.is_alive and (int(z.x) // chunk_size, int(z.y) // chunk_size) in active_chunk_coords
        ]
        zombie_state_changed = self._tick_vehicle_collisions(
            collision_zombies, chunk_size, active_chunk_coords
        )

        self._tick_world_extras()
        self._tick_final_rust_sync(zombie_state_changed)

        self.memory_monitor.record_tick_time(time.time() - t0)

        # Max simulation length = 1 month (108,000 ticks)
        max_ticks: int = self.sim_cfg.get("max_ticks_per_gen", 108000)
        if alive_count == 0 or self.world.current_tick >= max_ticks:
            self.end_generation()

'''

extras = '''    def _tick_world_extras(self) -> None:
        """Animal updates, dynamic item respawn and snapshot capture."""
''' + POST + '''

'''

finalsync = '''    def _tick_final_rust_sync(self, zombie_state_changed: bool) -> None:
        """Push Python-side zombie mutations back into the authoritative Rust roster."""
''' + FINALSYNC

# For chunk streaming we need roster_changed/entity_positions defined inside method; CHUNK already defines them.
# NOISE segment defines active_noises; SCENT defines active_scents and uses self.noise_events? check scent emit uses self.scent_trails. ok.
# _tick_decay_streams signature takes noises param but body uses self.noise_events — simplify: no param.
new_methods = new_methods.replace(
    "def _tick_decay_streams(self, noises: list[NoiseEvent]) -> list[NoiseEvent]:",
    "def _tick_decay_streams(self) -> list[NoiseEvent]:"
)
new_tick = new_tick.replace("self.noise_events = self._tick_decay_streams(self.noise_events)",
                            "self.noise_events = self._tick_decay_streams()")

replacement = new_tick + extras + finalsync + "\n\n" + new_methods.rstrip() + "\n\n"

src_new = src[:start] + replacement + src[end:]
open("src/simulation/engine.py", "w").write(src_new)
print("rewritten")
