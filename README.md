# Kuristo

Kuristo is a flexible, plugin-enabled automation framework designed for scientific and HPC workflows. 
It supports sequential and parallel job execution, workflow definition via YAML, resource-aware scheduling, custom step and action definitions, and rich output with optional headless mode.

## Features

- YAML-based workflows (GitHub Actions style)
- Custom steps and actions via Python plugins
- Job dependency graph with parallel execution
- Resource-aware scheduling with core-aware limits
- Step & job timeouts
- ANSI-rich output or plain mode for CI
- Environment variable passing and output capture
- Output validation (regex, float comparisons, CSV diffing)
- Composite steps for reusable action pipelines
- Built-in log directory and run tracking
- Test coverage with `pytest`
- MPI support via configurable launcher (`mpirun`, `mpiexec`, etc.)

## Install

Kuristo is not yet on PyPI. Clone the repo and install locally:

```bash
git clone https://github.com/andrsd/kuristo.git
cd kuristo
pip install -e .
```

## Usage

Run all tests in a directory:

```bash
kuristo run -l tests/assets/
```

Run a specific test set:

```bash
kuristo run -l tests/assets/tests1
```

Check your environment:

```bash
kuristo doctor
```

Headless/CI-safe mode

```bash
kuristo run -l tests --no-ansi
```

### Workflow YAML Example

```yaml
jobs:
  test-matrix:
    strategy:
      matrix:
        include:
          - os: ubuntu
            version: 20.04
          - os: ubuntu
            version: 22.04

    steps:
      - name: Run simulation
        id: simulation
        run: ./simulate --config=${{ matrix.version }}

      - name: Check output
        uses: checks/regex
        with:
          input: ${{ steps.simulation.output }}
          pattern: "SUCCESS"
```

### Writing Custom Actions

Create a plugin in `.kuristo/steps.py`:

```python
import kuristo

@kuristo.action("my/special-step")
class MyStep(kuristo.ProcessStep):
    def __init__(self, name, context: kuristo.Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self.input = kwargs["input"]

    def create_command(self):
        return f"echo Hello {self.input}"
```

Then, use in the workflow as:

```yaml
jobs:
  test:
    steps:
      - name: My special test
        uses: my/special-step
        with:
          input: "world"

```

Kuristo will auto-discover `.py` files in `.kuristo/`.

### Logging & Output

All logs and run data are saved in:

```bash
.kuristo-out/
├── runs/
│   ├── latest → 20250620_101500/
│   └── 20250620_101500/
```

Set logging retention and cleanup in `config.yaml`:

```yaml
log:
  dir_name: .kuristo-out
  history: 5
  cleanup: on_success
```

## Job Timing Report

To output a CSV of job timings:

```bash
kuristo run -l tests --report timing.csv
```

## Configuration

You can define a global config at `.kuristo/config.yaml`:

```yaml
resources:
  num_cores: 8

runner:
  mpi_launcher: mpiexec
```

Or override via environment variable:

```bash
KURISTO_MPI_LAUNCHER=mpiexec2 kuristo run -l tests/
```

## Testing & Coverage

Run tests:

```bash
pytest -v
```

With coverage:

```bash
pytest --cov=kuristo --cov-report=term-missing
```


## Philosophy

Kuristo is inspired by the structure of GitHub Actions but tailored for local and HPC workflows. 
It aims to be lightweight, extensible, and scriptable — with strong support for reproducibility and numerical simulation validation.

## License

MIT

## Fun Fact

"Kuristo" means "runner" in Esperanto. Because that’s what it does — it runs your stuff.
