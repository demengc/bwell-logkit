"""
Data extraction and export functionality for bWell log analysis.
"""

from typing import TYPE_CHECKING, Any

import pandas as pd

from .exceptions import ExtractionError
from .types import LogRecord, SceneInfo

if TYPE_CHECKING:
    from .logs import LogSession


def _flatten_dataframe(df: "pd.DataFrame") -> "pd.DataFrame":
    """Flatten nested dictionaries in DataFrame columns."""

    flattened_data = []

    for _, row in df.iterrows():
        flattened_row = {}
        for col, value in row.items():
            # Ensure col is treated as str for dict indexing
            col_str = str(col)
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    flattened_row[f"{col_str}_{nested_key}"] = nested_value
            else:
                flattened_row[col_str] = value
        flattened_data.append(flattened_row)

    return pd.DataFrame(flattened_data)


class LogSessionExtractor:
    """Handles data extraction and export for LogSession objects."""

    def __init__(self, records: list[LogRecord], metadata: dict[str, Any]):
        """
        Initialize the extractor.

        Args:
            records: List of log records
            metadata: Session metadata
        """
        self._records = records
        self._metadata = metadata

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

        Raises:
            ExtractionError: If pandas is not available or export fails
        """

        if not self._records:
            return pd.DataFrame()

        try:
            df = pd.DataFrame(self._records)

            if flatten:
                df = _flatten_dataframe(df)

            if include_metadata:
                for key, value in self._metadata.items():
                    df[f"session_{key}"] = value

            return df

        except Exception as e:
            raise ExtractionError(
                f"Failed to create DataFrame: {e}", "to_pandas"
            ) from e

    def export_csv(self, file_path: str, **kwargs: Any) -> None:
        """
        Export session data to CSV file.

        Args:
            file_path: Path for the output CSV file
            **kwargs: Additional arguments passed to pandas.to_csv()
        """
        df = self.to_pandas()
        df.to_csv(file_path, index=False, **kwargs)

    def export_parquet(self, file_path: str, **kwargs: Any) -> None:
        """
        Export session data to Parquet file.

        Args:
            file_path: Path for the output Parquet file
            **kwargs: Additional arguments passed to pandas.to_parquet()
        """
        df = self.to_pandas()
        df.to_parquet(file_path, index=False, **kwargs)


class SceneViewExtractor:
    """Handles data extraction and export for SceneView objects via
    composition."""

    def __init__(self, session: "LogSession", scene_info: SceneInfo):
        """
        Initialize the extractor using composition.

        Args:
            session: LogSession containing the scene records
            scene_info: Information about the scene
        """
        self._session = session
        self._scene_info = scene_info

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
            include_scene_info: Whether to include scene metadata (default:
            True)

        Returns:
            pd.DataFrame: DataFrame containing scene records with scene
            metadata

        Raises:
            ExtractionError: If pandas is not available or export fails
        """
        try:
            # Get base DataFrame from session
            df = self._session.to_pandas(flatten, include_metadata)

            # Add scene-specific columns if requested
            if include_scene_info:
                if df.empty:
                    # For empty DFs, create the columns with appropriate types
                    scene_columns = {
                        "scene_name": pd.Series([], dtype="object"),
                        "scene_instance": pd.Series([], dtype="int64"),
                        "scene_start_game_time_secs": pd.Series([], dtype="float64"),
                        "scene_end_game_time_secs": pd.Series([], dtype="float64"),
                        "scene_start_millis_since_epoch": pd.Series([], dtype="int64"),
                        "scene_end_millis_since_epoch": pd.Series([], dtype="int64"),
                        "scene_duration": pd.Series([], dtype="float64"),
                    }
                    for col_name, col_series in scene_columns.items():
                        df[col_name] = col_series
                else:
                    df["scene_name"] = self._scene_info.name
                    df["scene_instance"] = self._scene_info.instance
                    df["scene_start_game_time_secs"] = (
                        self._scene_info.start_game_time_secs
                    )
                    df["scene_end_game_time_secs"] = self._scene_info.end_game_time_secs
                    df["scene_start_millis_since_epoch"] = (
                        self._scene_info.start_millis_since_epoch
                    )
                    df["scene_end_millis_since_epoch"] = (
                        self._scene_info.end_millis_since_epoch
                    )
                    df["scene_duration"] = self._scene_info.duration_secs

            return df

        except Exception as e:
            raise ExtractionError(
                f"Failed to create scene DataFrame: {e}", "scene_to_pandas"
            ) from e

    def export_csv(self, file_path: str, **kwargs: Any) -> None:
        """Export scene data to CSV file with scene metadata."""
        df = self.to_pandas()
        df.to_csv(file_path, index=False, **kwargs)

    def export_parquet(self, file_path: str, **kwargs: Any) -> None:
        """Export scene data to Parquet file with scene metadata."""
        df = self.to_pandas()
        df.to_parquet(file_path, index=False, **kwargs)
