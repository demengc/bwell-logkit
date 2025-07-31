# bwell-logkit

A Python library for processing and analyzing log files from the National
Research Council (NRC)
Canada's [bWell](https://nrc.canada.ca/en/research-development/products-services/technical-advisory-services/bwell)
application.

## Features

- **Easy log file reading** with automatic JSON healing for truncated files
- **Parallel directory loading** for processing multiple files efficiently
- **Flexible record filtering** by type, timestamp, and custom criteria
- **Scene-based analysis** with automatic scene segmentation and metadata
- **DataFrame extraction** for data analysis with pandas integration
- **Multiple export formats** including CSV, Parquet, and pandas DataFrame

## Installation

Install `bwell-logkit` from this GitHub repository:

```bash
pip install git+https://github.com/demengc/bwell-logkit.git
```

## Quick Start

```python
from bwell_logkit import load_log, load_all_logs, RecordTypes, MovementSources

# Load a single bWell log file
session = load_log("path/to/bWellLogAll20250628112233.json")

# Or, load all log files from a directory (recursively, parallel)
sessions = load_all_logs(
    "path/to/log_directory",
    file_pattern="*.json",  # Custom file pattern
    max_workers=4,          # Limit parallel workers
    skip_errors=False        # Skip files that fail to load
)

# Basic session info
print(f"Loaded {len(session)} records")
print(f"Available scenes: {session.list_scenes()}")

# Export all data as pandas DataFrame
df = session.to_pandas()
print(f"DataFrame shape: {df.shape}")

# Filter for movement data
movement_session = session.filter_type(RecordTypes.ABSOLUTE_ACTIVITY.value)
print(f"Movement records: {len(movement_session)}")

# Filter for head tracking specifically
head_movement = movement_session.filter(
    lambda r: r.get("senderTag") == MovementSources.HEAD.value
)
print(f"Head tracking records: {len(head_movement)}")

# Export filtered data
head_movement.export_csv("head_movement_data.csv")
```

See [examples](examples/basic_usage.py) for more detailed examples.

## Core Concepts

### LogSession

The main entry point for analyzing complete log sessions. Provides filtering,
statistics, and export capabilities.

### SceneView

Scene-specific analysis with automatic scene metadata inclusion. Access via
`session.scene(name, instance)`.

### SceneManager

Manages scene segmentation and provides scene information. Access via
`session.scene_manager`.

## Development and Contributing

Want to contribute to `bwell-logkit`? Here's how to get started.

### 1. Clone the repository

```bash
git clone https://github.com/demengc/bwell-logkit.git
cd bwell-logkit
```

### 2. Set up the environment

First, install the package in editable mode along with the development
dependencies:

```bash
pip install -e .[dev]
```

This will install the package and extra tools like `pytest`, `black`, and
`mypy`.

Next, set up the pre-commit hooks, which automatically format and lint your
code on every commit:

```bash
pre-commit install
```

### 3. Run checks

You can run various checks manually to ensure your code is clean, correct, and
well-formatted.

**Formatting**

To automatically format the code with `black` and `isort`:

```bash
black src/ tests/ examples/
isort src/ tests/ examples/
```

**Linting**

To run linters with `flake8` and `mypy`:

```bash
flake8 src/ tests/
mypy src/
```

**Testing**

To run the test suite with `pytest`:

```bash
pytest
```

**Coverage**

To generate a coverage report:

```bash
pytest --cov=src/bwell_logkit --cov-report=html
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details. This project is not affiliated with or endorsed by the
National Research Council (NRC).
