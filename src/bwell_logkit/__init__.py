"""
bwell-logkit: A Python library for processing and analyzing log files from
the National Research Council (NRC) Canada's bWell application.
"""

from .exceptions import (
    BwellLogKitError,
    ExtractionError,
    LogReadError,
    SceneNotFoundError,
)
from .logs import LogSession, SceneView
from .reader import load_log, read_records
from .scene import SceneManager
from .types import (
    FilePath,
    FilterFunction,
    LogRecord,
    MovementSources,
    RecordFields,
    RecordTypes,
    SceneInfo,
    Scenes,
)

__version__ = "1.0.0"
__author__ = "Demeng Chen"
__email__ = "contact@demeng.dev"

__all__ = [
    # Main entry points
    "load_log",
    "read_records",
    # Core classes
    "LogSession",
    "SceneView",
    "SceneManager",
    # Exceptions
    "BwellLogKitError",
    "LogReadError",
    "SceneNotFoundError",
    "ExtractionError",
    # Types and constants
    "LogRecord",
    "FilterFunction",
    "FilePath",
    "SceneInfo",
    "RecordFields",
    "RecordTypes",
    "MovementSources",
    "Scenes",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
