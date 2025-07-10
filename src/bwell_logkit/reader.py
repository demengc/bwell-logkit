"""
File reading and parsing for bWell log data.
"""

import concurrent.futures
from pathlib import Path
from typing import Any

import orjson

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


def load_all_logs(
    folder_path: FilePath,
    *,
    file_pattern: str = "*.json",
    max_workers: int | None = None,
    skip_errors: bool = True,
    **kwargs: Any,
) -> dict[str, LogSession]:
    """
    Load all log files from a folder recursively in parallel.

    Args:
        folder_path: Path to the folder containing log files
        file_pattern: Glob pattern for log files (default: "*.json")
        max_workers: Maximum # of workers (default: None / TPE default)
        skip_errors: If True, skip failed files; if False, raise on 1st error
        **kwargs: Additional options passed to read_records

    Returns:
        dict[str, LogSession]: Dict mapping relative file paths to LogSessions

    Raises:
        LogReadError: If folder doesn't exist / if skip_errors=False and any
        file fails to load
    """
    folder_path = Path(folder_path)

    if not folder_path.exists():
        raise LogReadError(f"Folder not found: {folder_path}", str(folder_path))

    if not folder_path.is_dir():
        raise LogReadError(f"Path is not a directory: {folder_path}", str(folder_path))

    # Find all log files recursively
    log_files = list(folder_path.rglob(file_pattern))

    if not log_files:
        return {}

    def load_single_log(file_path: Path) -> tuple[str, LogSession | Exception]:
        """Load a single log file and return (relative_path, result)."""
        try:
            relative_path = file_path.relative_to(folder_path).as_posix()
            session = load_log(file_path, **kwargs)
            # Update metadata to include relative path
            session.set_metadata("relative_path", relative_path)
            return (relative_path, session)
        except Exception as e:
            relative_path = file_path.relative_to(folder_path).as_posix()
            return (relative_path, e)

    results: dict[str, LogSession] = {}
    errors: list[tuple[str, Exception]] = []

    # Use ThreadPoolExecutor for parallel loading
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(load_single_log, file_path): file_path
            for file_path in log_files
        }

        # Collect results
        for future in concurrent.futures.as_completed(future_to_file):
            relative_path, result = future.result()

            if isinstance(result, Exception):
                errors.append((relative_path, result))
                if not skip_errors:
                    raise LogReadError(
                        f"Failed to load log file '{relative_path}': {result}",
                        relative_path,
                        result,
                    )
            else:
                results[relative_path] = result

    # Log errors if skip_errors=True but there were some failures
    if errors and skip_errors:
        failed_files = [path for path, _ in errors]
        print(
            f"Warning: Failed to load {len(failed_files)} file(s): " f"{failed_files}"
        )

    return results
