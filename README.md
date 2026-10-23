# Zombie Simulation

Evolutionary AI survival simulation with a hybrid Python / Rust architecture:
gameplay logic and rendering live in Python (pygame), while the simulation hot
path (zombie movement, spatial hashing, line-of-sight, brain inference) runs in
a native Rust extension (`rust_engine`).  When the Rust module is not built,
the engine transparently falls back to pure-Python implementations.

See [ARCHITECTURE.md](ARCHITECTURE.md) for a deep dive into the ECS layout and
the Python↔Rust bridge.

## Requirements

- Python 3.12+
- A Rust toolchain (only needed to build the native engine): <https://rustup.rs>

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # runtime deps
pip install -r requirements-dev.txt    # + pytest, ruff (CI/dev)
```

### Building the Rust engine (recommended)

Without this step the simulation still works but runs on the slower Python
fallback for the hot path.

```bash
cargo build --release                  # produces target/release/librust_engine.so
cp target/release/librust_engine.so ./rust_engine.so
python -c "import rust_engine; print('rust engine OK')"
```

Alternatively use the packaged build script:

```bash
python build.py
```

## Running

```bash
python main.py                 # GUI mode (menu + pygame renderer)
python main.py --headless --ticks 1000   # headless benchmark run
python train.py                # evolutionary training loop
```

Simulation parameters (map size, population, `fps`, day length, …) are read
from `config.json`.

## Testing & linting

```bash
pytest tests -q                # unit + stress tests
ruff check src tests           # lint
cargo fmt --check && cargo clippy -- -D warnings   # Rust hygiene
```

## Project layout

```
main.py            entry point (GUI / headless)
train.py           evolutionary trainer
config.json        simulation configuration
crates/rust_engine Rust cdylib exposing the native hot-path engine
src/
  simulation/      engine tick pipeline, Python<->Rust bridge
  entities/        ECS entities (survivor, zombie, item, ...) + uid identity
  systems/         world systems (container, chunk, LOS, ...)
  ai/              GRU brains, batched inference, weight cache
  ui/              pygame renderer and menus
tests/             pytest suite (includes max-load stress test)
```
