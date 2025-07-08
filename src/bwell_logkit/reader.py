"""
File reading and parsing for bWell log data.
"""

import orjson
from pathlib import Path
from typing import Any

from .exceptions import LogReadError
from .logs import LogSession
from .types import FilePath, LogRecord


def _heal_json(content: str) -> str:
    """
    Heal truncated bWell log JSON content.

    bWell logs can be truncated with:
    - Trailing comma in the data array
    - Missing closing ]} brackets

    Example: {"data": [{"key": "value"}, -> {"data": [{"key": "value"}]}
    """
    healed = content.strip()

    # Handle empty content
    if not healed:
        return healed

    # Remove trailing comma if present
    if healed.endswith(","):
        healed = healed[:-1]

    # Add missing closing brackets
    if healed.endswith("]}"):
        # Already properly closed
        pass
    elif healed.endswith("]"):
        # Missing only the closing }
        healed += "}"
    else:
        # Missing both ] and }
        healed += "]}"

    return healed


def read_records(file_path: FilePath, encoding: str = "utf-8") -> list[LogRecord]:
    """
    Read and parse a bWell log file with automatic JSON healing.

    Args:
        file_path: Path to the log file
        encoding: File encoding (default: utf-8)

    Returns:
        List of log records

    Raises:
        LogReadError: If file cannot be read or parsed
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise LogReadError(f"File not found: {file_path}", str(file_path))

    try:
        # Read raw content
        content = file_path.read_text(encoding=encoding).strip().replace("\n", "")

        if not content:
            raise LogReadError("File is empty", str(file_path))

        # Try parsing as-is first
        try:
            data = orjson.loads(content)
        except orjson.JSONDecodeError:
            # Attempt to heal the JSON
            healed_content = _heal_json(content)
            try:
                data = orjson.loads(healed_content)
            except orjson.JSONDecodeError as e:
                raise LogReadError(
                    f"Failed to parse JSON even after healing: {e}",
                    str(file_path),
                    e,
                )

        # Extract records from the data structure
        if not isinstance(data, dict):
            raise LogReadError(
                "Invalid log format: root must be an object", str(file_path)
            )

        records = data.get("data")
        if not isinstance(records, list):
            raise LogReadError(
                "Invalid log format: missing 'data' array", str(file_path)
            )

        return records

    except Exception as e:
        if isinstance(e, LogReadError):
            raise
        raise LogReadError(f"Unexpected error reading file: {e}", str(file_path), e)


def load_log(file_path: FilePath, **kwargs: Any) -> LogSession:
    """
    Load log data and return a LogSession for analysis.

    Args:
        file_path: Path to the log file
        **kwargs: Additional options passed to read_records

    Returns:
        LogSession: Session object for analysis
    """
    records = read_records(file_path, **kwargs)
    return LogSession(records, metadata={"file_path": str(file_path)})
