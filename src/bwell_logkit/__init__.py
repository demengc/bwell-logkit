"""
bwell-logkit: A Python library for processing and analyzing log files from
the National Research Council (NRC) Canada's bWell application.
"""

# Version and author information
__version__ = "1.1.1"
__author__ = "Demeng Chen"
__email__ = "contact@demeng.dev"

# Exception imports
from .exceptions import (
    BwellLogKitError,
    ExtractionError,
    LogReadError,
    SceneNotFoundError,
)
from .logs import LogSession, SceneView

# Core functionality imports
from .reader import load_all_logs, load_log, read_records
from .scene import SceneManager

# Type and constant imports
from .types import (
    FilePath,
    FilterFunction,
    LogRecord,
    MoleHitRecordFields,
    MovementSources,
    RecordFields,
    RecordTypes,
    SceneEntryRecordFields,
    SceneInfo,
    Scenes,
)

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__email__",
    # Main entry points
    "load_log",
    "load_all_logs",
    "read_records",
    # Core classes
    "LogSession",
    "SceneView",
    "SceneManager",
    # Exceptions
    "BwellLogKitError",
    "ExtractionError",
    "LogReadError",
    "SceneNotFoundError",
    # Types and constants
    "FilePath",
    "FilterFunction",
    "LogRecord",
    "MoleHitRecordFields",
    "MovementSources",
    "RecordFields",
    "RecordTypes",
    "SceneEntryRecordFields",
    "SceneInfo",
    "Scenes",
]
