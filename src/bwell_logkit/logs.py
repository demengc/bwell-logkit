"""
Core LogSession and SceneView classes for bWell log analysis.
"""

import copy
import json
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from .exceptions import SceneNotFoundError
from .extractor import LogSessionExtractor, SceneViewExtractor
from .scene import SceneManager
from .types import FilterFunction, LogRecord, RecordFields, SceneInfo

if TYPE_CHECKING:
    import pandas as pd


def _clean_records(records: list[LogRecord]) -> list[LogRecord]:
    """Clean and deduplicate records."""
    # Create deduplication key based on hash of entire record
    seen = set()
    cleaned = []

    for record in records:
        record_json = json.dumps(record, sort_keys=True, default=str)
        record_hash = hash(record_json)

        if record_hash not in seen:
            seen.add(record_hash)
            cleaned.append(record)

    # Sort by timestamp
    cleaned.sort(key=lambda r: r.get(RecordFields.GAME_TIME_SECS, 0))
    return cleaned


class LogSession:
    """
    Main session object for analyzing bWell log data.

    Represents a complete log session with filtering and analysis capabilities.
    For scene-specific analysis, use session.scene() to get a SceneView.
    """

    def __init__(
        self,
        records: list[LogRecord],
        metadata: dict[str, Any] | None = None,
        *,
        initialize_scene_manager: bool = False,
        _scene_manager: "SceneManager | None" = None,
    ):
        """
        Initialize a log session.

        Args:
            records: List of log records
            metadata: Optional metadata about the session
            initialize_scene_manager: Whether to initialize scene manager immediately
            _scene_manager: Optional pre-existing scene manager (from parent session)
        """
        # Sort records by timestamp and remove duplicates
        self._records = _clean_records(records)
        self._metadata = metadata or {}

        # Lazy-loaded components (unless eagerly initialized)
        # _scene_manager can either be provided by a parent session or lazily/eagerly
        # created here depending on `initialize_scene_manager`.
        self._scene_manager: SceneManager | None = _scene_manager
        if initialize_scene_manager and self._scene_manager is None:
            self._scene_manager = SceneManager(self._records)

        self._extractor: LogSessionExtractor | None = None

    @property
    def records(self) -> list[LogRecord]:
        """Get all records in the session."""
        return copy.deepcopy(self._records)

    @property
    def metadata(self) -> dict[str, Any]:
        """Get session metadata."""
        return self._metadata.copy()

    def __len__(self) -> int:
        """Return number of records."""
        return len(self._records)

    def __repr__(self) -> str:
        return f"LogSession({len(self._records)} records)"

    @property
    def scene_manager(self) -> SceneManager:
        """
        Get the scene manager for this session.

        Returns:
            SceneManager: Manager for scene-based operations
        """
        if self._scene_manager is None:
            self._scene_manager = SceneManager(self._records)
        return self._scene_manager

    def list_scenes(self) -> list[str]:
        """
        List all available scene names.

        Returns:
            List of scene names
        """
        return self.scene_manager.list_scenes()

    @property
    def extractor(self) -> LogSessionExtractor:
        """
        Get the data extractor for this session.

        Returns:
            LogSessionExtractor: Extractor for data export operations
        """
        if self._extractor is None:
            self._extractor = LogSessionExtractor(self._records, self._metadata)
        return self._extractor

    def scene(self, name: str, instance: int = 0) -> "SceneView":
        """
        Get a specific scene instance for scene-focused analysis.

        Args:
            name: Scene name
            instance: Scene instance (0-based, default: 0)

        Returns:
            SceneView: Scene-specific view with scene analysis capabilities

        Raises:
            SceneNotFoundError: If scene is not found
        """
        if not self.scene_manager.has_scene(name, instance):
            available = self.scene_manager.list_scenes()
            raise SceneNotFoundError(name, instance, available)

        scene_info = self.scene_manager.get_scene_info(name, instance)
        scene_records = self.scene_manager.get_scene_records(name, instance)

        return SceneView(LogSession(scene_records, self._metadata), scene_info)

    def filter(self, condition: FilterFunction) -> "LogSession":
        """
        Filter records and return a new session.

        Args:
            condition: Function that takes a record and returns bool

        Returns:
            LogSession: New session with filtered records
        """
        filtered_records = [r for r in self._records if condition(r)]
        return LogSession(
            filtered_records,
            self._metadata,
            _scene_manager=self._scene_manager,
        )

    def filter_type(self, *record_types: str) -> "LogSession":
        """
        Filter by record type(s).

        Args:
            *record_types: One or more record types to include

        Returns:
            LogSession: New session with filtered records
        """
        return self.filter(lambda r: r.get(RecordFields.RECORD_TYPE) in record_types)

    def filter_time_range(self, start: float, end: float) -> "LogSession":
        """
        Filter by game time range.

        Args:
            start: Start time in seconds
            end: End time in seconds

        Returns:
            LogSession: New session with filtered records
        """
        return self.filter(
            lambda r: start <= r.get(RecordFields.GAME_TIME_SECS, 0) <= end
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the session.

        Returns:
            Dictionary with session statistics
        """
        if not self._records:
            return {
                "total_records": 0,
                "record_types": {},
                "game_time_range": None,
                "millis_since_epoch_range": None,
                "scenes": [],
                "metadata": self._metadata,
            }

        # Count record types
        type_counts: dict[str, int] = defaultdict(int)
        for record in self._records:
            record_type = record.get(RecordFields.RECORD_TYPE, "unknown")
            type_counts[record_type] += 1

        # Get game time range
        game_time_stamps = [
            r.get(RecordFields.GAME_TIME_SECS)
            for r in self._records
            if r.get(RecordFields.GAME_TIME_SECS) is not None
        ]
        game_time_range = None
        if game_time_stamps:
            # Filter out None values for min/max
            valid_game_times = [t for t in game_time_stamps if t is not None]
            if valid_game_times:
                game_time_range = {
                    "start": min(valid_game_times),
                    "end": max(valid_game_times),
                }

        # Get millis since epoch range
        epoch_stamps = [
            r.get(RecordFields.MILLIS_SINCE_EPOCH)
            for r in self._records
            if r.get(RecordFields.MILLIS_SINCE_EPOCH) is not None
        ]
        millis_since_epoch_range = None
        if epoch_stamps:
            # Filter out None values for min/max
            valid_epoch_times = [t for t in epoch_stamps if t is not None]
            if valid_epoch_times:
                millis_since_epoch_range = {
                    "start": min(valid_epoch_times),
                    "end": max(valid_epoch_times),
                }

        # Get scene info
        scenes = []
        try:
            for scene_name in self.scene_manager.list_scenes():
                scene_count = self.scene_manager.get_scene_count(scene_name)
                scenes.append({"name": scene_name, "instances": scene_count})
        except (AttributeError, TypeError, KeyError):
            # If scene analysis fails for any reason, continue without it
            pass

        return {
            "total_records": len(self._records),
            "record_types": dict(type_counts),
            "game_time_range": game_time_range,
            "millis_since_epoch_range": millis_since_epoch_range,
            "scenes": scenes,
            "metadata": self._metadata,
        }

    def to_pandas(
        self, flatten: bool = True, include_metadata: bool = False
    ) -> "pd.DataFrame":
        """
        Export session data to a pandas DataFrame.

        Args:
            flatten: Whether to flatten dicts into separate columns
            include_metadata: Whether to include session metadata as columns

        Returns:
            pd.DataFrame: DataFrame containing all log records
        """
        return self.extractor.to_pandas(
            flatten=flatten, include_metadata=include_metadata
        )

    def export_csv(self, file_path: str, **kwargs: Any) -> None:
        """
        Export session data to CSV file.

        Args:
            file_path: Path for the output CSV file
            **kwargs: Additional arguments passed to pandas.to_csv()
        """
        self.extractor.export_csv(file_path, **kwargs)

    def export_parquet(self, file_path: str, **kwargs: Any) -> None:
        """
        Export session data to Parquet file.

        Args:
            file_path: Path for the output Parquet file
            **kwargs: Additional arguments passed to pandas.to_parquet()
        """
        self.extractor.export_parquet(file_path, **kwargs)


class SceneView:
    """
    A domain-specific view for analyzing a particular scene instance.

    Provides scene-focused analysis capabilities with automatic scene metadata
    inclusion and scene-specific operations. Implements LogSession operations
    via composition to avoid duplication.
    """

    def __init__(self, session: LogSession, scene_info: SceneInfo):
        """
        Initialize scene view.

        Args:
            session: LogSession containing the scene records
            scene_info: Information about the scene
        """
        self._session = session
        self._scene_info = scene_info
        self._extractor: SceneViewExtractor | None = None

    @property
    def records(self) -> list[LogRecord]:
        """Get records in this scene."""
        return self._session.records

    @property
    def info(self) -> SceneInfo:
        """Get scene information."""
        return self._scene_info

    @property
    def metadata(self) -> dict[str, Any]:
        """Get session metadata."""
        return self._session.metadata

    @property
    def extractor(self) -> SceneViewExtractor:
        """
        Get the data extractor for this scene view.

        Returns:
            SceneViewExtractor: Extractor for scene data export operations
        """
        if self._extractor is None:
            self._extractor = SceneViewExtractor(self._session, self._scene_info)
        return self._extractor

    def __len__(self) -> int:
        """Return number of records in scene."""
        return len(self._session)

    def __repr__(self) -> str:
        return (
            f"SceneView({self._scene_info.name}, instance="
            f"{self._scene_info.instance}, {len(self._session)} records)"
        )

    # Delegate filtering operations to wrapped session
    def filter(self, condition: FilterFunction) -> "SceneView":
        """
        Filter scene records and return a new scene view.

        Args:
            condition: Function that takes a record and returns bool

        Returns:
            SceneView: New scene view with filtered records
        """
        filtered_session = self._session.filter(condition)
        return SceneView(filtered_session, self._scene_info)

    def filter_type(self, *record_types: str) -> "SceneView":
        """
        Filter by record type(s) within the scene.

        Args:
            *record_types: One or more record types to include

        Returns:
            SceneView: New scene view with filtered records
        """
        filtered_session = self._session.filter_type(*record_types)
        return SceneView(filtered_session, self._scene_info)

    def filter_time_range(self, start: float, end: float) -> "SceneView":
        """
        Filter by game time range within the scene.

        Args:
            start: Start time in seconds (relative to scene)
            end: End time in seconds (relative to scene)

        Returns:
            SceneView: New scene view with filtered records
        """
        filtered_session = self._session.filter_time_range(start, end)
        return SceneView(filtered_session, self._scene_info)

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the scene.

        Returns:
            Dictionary with scene-specific statistics
        """
        base_stats = self._session.get_stats()

        # Add scene-specific information
        base_stats["scene_info"] = {
            "name": self._scene_info.name,
            "instance": self._scene_info.instance,
            "duration_secs": self._scene_info.duration_secs,
            "start_game_time_secs": self._scene_info.start_game_time_secs,
            "end_game_time_secs": self._scene_info.end_game_time_secs,
            "start_millis_since_epoch": self._scene_info.start_millis_since_epoch,
            "end_millis_since_epoch": self._scene_info.end_millis_since_epoch,
        }

        # Remove session-level scene list (not relevant for single scene)
        if "scenes" in base_stats:
            del base_stats["scenes"]

        return base_stats

    def to_pandas(
        self,
        flatten: bool = True,
        include_metadata: bool = False,
        include_scene_info: bool = True,
    ) -> "pd.DataFrame":
        """
        Export scene data to a pandas DataFrame.

        Args:
            flatten: Whether to flatten dicts into separate columns
            include_metadata: Whether to include session metadata as columns
            include_scene_info: Whether to include scene metadata

        Returns:
            pd.DataFrame: DF containing scene records with scene metadata
        """
        return self.extractor.to_pandas(
            flatten=flatten,
            include_metadata=include_metadata,
            include_scene_info=include_scene_info,
        )

    def export_csv(self, file_path: str, **kwargs: Any) -> None:
        """Export scene data to CSV file with scene metadata."""
        self.extractor.export_csv(file_path, **kwargs)

    def export_parquet(self, file_path: str, **kwargs: Any) -> None:
        """Export scene data to Parquet file with scene metadata."""
        self.extractor.export_parquet(file_path, **kwargs)
