"""
Tests for the extractor module.
"""

import pandas as pd
import pytest

from bwell_logkit.exceptions import ExtractionError
from bwell_logkit.extractor import (
    LogSessionExtractor,
    SceneViewExtractor,
    _flatten_dataframe,
)
from bwell_logkit.logs import LogSession
from bwell_logkit.types import SceneInfo


class TestFlattenDataframe:
    """Test the _flatten_dataframe utility function."""

    def test_flatten_basic(self):
        """Test basic DataFrame flattening."""
        df = pd.DataFrame(
            [
                {
                    "simple": "value",
                    "nested": {"x": 1, "y": 2},
                    "another": {"a": "test", "b": 5},
                }
            ]
        )

        flattened = _flatten_dataframe(df)

        assert "simple" in flattened.columns
        assert "nested_x" in flattened.columns
        assert "nested_y" in flattened.columns
        assert "another_a" in flattened.columns
        assert "another_b" in flattened.columns
        assert "nested" not in flattened.columns  # Original nested column removed

        assert flattened.iloc[0]["simple"] == "value"
        assert flattened.iloc[0]["nested_x"] == 1
        assert flattened.iloc[0]["nested_y"] == 2
        assert flattened.iloc[0]["another_a"] == "test"
        assert flattened.iloc[0]["another_b"] == 5

    def test_flatten_no_nested_data(self):
        """Test flattening DataFrame with no nested data."""
        df = pd.DataFrame([{"a": 1, "b": 2, "c": "test"}])

        flattened = _flatten_dataframe(df)

        # Should be unchanged
        assert list(flattened.columns) == ["a", "b", "c"]
        assert flattened.iloc[0]["a"] == 1
        assert flattened.iloc[0]["b"] == 2
        assert flattened.iloc[0]["c"] == "test"

    def test_flatten_empty_dataframe(self):
        """Test flattening empty DataFrame."""
        df = pd.DataFrame()
        flattened = _flatten_dataframe(df)
        assert len(flattened) == 0


class TestLogSessionExtractor:
    """Test cases for LogSessionExtractor class."""

    def test_init_basic(self, sample_records):
        """Test basic LogSessionExtractor initialization."""
        metadata = {"file_path": "/test/path.json"}
        extractor = LogSessionExtractor(sample_records, metadata)

        assert extractor._records == sample_records
        assert extractor._metadata == metadata

    def test_to_pandas_basic(self, sample_records):
        """Test basic pandas DataFrame export."""
        extractor = LogSessionExtractor(sample_records, {})
        df = extractor.to_pandas()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 9
        assert "myType" in df.columns
        assert "timestamp" in df.columns

    def test_to_pandas_with_flattening(self, sample_records):
        """Test pandas export with flattening enabled."""
        extractor = LogSessionExtractor(sample_records, {})
        df = extractor.to_pandas(flatten=True)

        # Should have flattened columns
        assert "absolutePosition_x" in df.columns
        assert "absolutePosition_y" in df.columns
        assert "absolutePosition_z" in df.columns
        assert "absoluteRotation_x" in df.columns

    def test_to_pandas_without_flattening(self, sample_records):
        """Test pandas export with flattening disabled."""
        extractor = LogSessionExtractor(sample_records, {})
        df = extractor.to_pandas(flatten=False)

        # Should keep nested structure
        assert "absolutePosition" in df.columns
        assert "absoluteRotation" in df.columns
        # Shouldn't have flattened columns
        assert "absolutePosition_x" not in df.columns

    def test_to_pandas_with_metadata(self, sample_records):
        """Test pandas export with metadata included."""
        metadata = {"file_path": "/test/path.json", "user": "test_user"}
        extractor = LogSessionExtractor(sample_records, metadata)
        df = extractor.to_pandas(include_metadata=True)

        assert "session_file_path" in df.columns
        assert "session_user" in df.columns
        assert df.iloc[0]["session_file_path"] == "/test/path.json"
        assert df.iloc[0]["session_user"] == "test_user"

    def test_to_pandas_empty_records(self):
        """Test pandas export with empty records."""
        extractor = LogSessionExtractor([], {})
        df = extractor.to_pandas()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_export_csv(self, sample_records, tmp_path):
        """Test CSV export functionality."""
        extractor = LogSessionExtractor(sample_records, {})
        output_file = tmp_path / "test.csv"

        extractor.export_csv(str(output_file))
        assert output_file.exists()

    def test_export_csv_with_kwargs(self, sample_records, tmp_path):
        """Test CSV export with custom kwargs."""
        extractor = LogSessionExtractor(sample_records, {})
        output_file = tmp_path / "test_output.csv"

        extractor.export_csv(str(output_file), sep=";", na_rep="NULL")

        assert output_file.exists()
        content = output_file.read_text()
        assert ";" in content  # Custom separator

    def test_export_parquet_basic(self, sample_records, tmp_path):
        """Test Parquet export functionality."""
        extractor = LogSessionExtractor(sample_records, {})
        output_file = tmp_path / "test_output.parquet"

        extractor.export_parquet(str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify by reading back
        df_read = pd.read_parquet(output_file)
        assert len(df_read) == 9
        assert "myType" in df_read.columns


class TestSceneViewExtractor:
    """Test cases for SceneViewExtractor class."""

    def test_init_basic(self, sample_records):
        """Test basic SceneViewExtractor initialization."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        assert extractor._session == session
        assert extractor._scene_info == scene_info

    def test_to_pandas_with_scene_info(self, sample_records):
        """Test pandas export with scene info included."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 1, 5.0, 15.0, 5000, 15000)
        extractor = SceneViewExtractor(session, scene_info)

        df = extractor.to_pandas(include_scene_info=True)

        assert "scene_name" in df.columns
        assert "scene_instance" in df.columns
        assert "scene_duration" in df.columns
        assert "scene_start_game_time_secs" in df.columns
        assert "scene_end_game_time_secs" in df.columns

        assert df.iloc[0]["scene_name"] == "TestScene"
        assert df.iloc[0]["scene_instance"] == 1
        assert df.iloc[0]["scene_duration"] == 10.0
        assert df.iloc[0]["scene_start_game_time_secs"] == 5.0
        assert df.iloc[0]["scene_end_game_time_secs"] == 15.0

    def test_to_pandas_without_scene_info(self, sample_records):
        """Test pandas export without scene info."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        df = extractor.to_pandas(include_scene_info=False)

        assert "scene_name" not in df.columns
        assert "scene_instance" not in df.columns
        assert "scene_duration" not in df.columns

    def test_to_pandas_empty_session(self):
        """Test pandas export with empty session."""
        session = LogSession([])
        scene_info = SceneInfo("EmptyScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        df = extractor.to_pandas(include_scene_info=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        # Scene info columns should still be present but empty
        assert "scene_name" in df.columns

    def test_to_pandas_with_metadata_and_scene_info(self, sample_records):
        """Test pandas export with both metadata and scene info."""
        metadata = {"file_path": "/test/path.json"}
        session = LogSession(sample_records, metadata)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        df = extractor.to_pandas(include_metadata=True, include_scene_info=True)

        assert "session_file_path" in df.columns
        assert "scene_name" in df.columns
        assert df.iloc[0]["session_file_path"] == "/test/path.json"
        assert df.iloc[0]["scene_name"] == "TestScene"

    def test_export_csv_with_scene_metadata(self, sample_records, tmp_path):
        """Test CSV export includes scene metadata."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        output_file = tmp_path / "scene_output.csv"
        extractor.export_csv(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "scene_name" in content
        assert "TestScene" in content
        assert "scene_duration" in content

    def test_export_parquet_with_scene_metadata(self, sample_records, tmp_path):
        """Test Parquet export includes scene metadata."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        output_file = tmp_path / "scene_output.parquet"
        extractor.export_parquet(str(output_file))

        assert output_file.exists()
        df_read = pd.read_parquet(output_file)
        assert "scene_name" in df_read.columns
        assert df_read.iloc[0]["scene_name"] == "TestScene"


class TestExtractorErrorHandling:
    """Test error handling in extractors."""

    def test_extraction_error_propagation(self, sample_records, monkeypatch):
        """Test that extraction errors are properly wrapped."""
        extractor = LogSessionExtractor(sample_records, {})

        # Mock pandas.DataFrame to raise an exception
        def mock_dataframe(*args, **kwargs):
            raise ValueError("Mock pandas error")

        monkeypatch.setattr("pandas.DataFrame", mock_dataframe)

        with pytest.raises(ExtractionError) as exc_info:
            extractor.to_pandas()

        assert "Failed to create DataFrame" in str(exc_info.value)
        assert exc_info.value.extractor_type == "to_pandas"

    def test_scene_extraction_error_propagation(self, sample_records, monkeypatch):
        """Test scene extractor error handling."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        extractor = SceneViewExtractor(session, scene_info)

        # Mock the session's to_pandas method to raise an error
        def mock_to_pandas(*args, **kwargs):
            raise ValueError("Mock session error")

        monkeypatch.setattr(session, "to_pandas", mock_to_pandas)

        with pytest.raises(ExtractionError) as exc_info:
            extractor.to_pandas()

        assert "Failed to create scene DataFrame" in str(exc_info.value)
        assert exc_info.value.extractor_type == "scene_to_pandas"


class TestExtractorIntegration:
    """Integration tests for extractors."""

    def test_session_to_extractor_integration(self, sample_records):
        """Test integration between LogSession and its extractor."""
        session = LogSession(sample_records)

        # Test that session delegates properly to extractor
        df_from_session = session.to_pandas()
        df_from_extractor = session.extractor.to_pandas()

        # Should be identical
        pd.testing.assert_frame_equal(df_from_session, df_from_extractor)

    def test_scene_view_to_extractor_integration(self, sample_records):
        """Test integration between SceneView and its extractor."""
        from bwell_logkit.logs import SceneView

        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        # Test that scene view delegates properly to extractor
        df_from_scene = scene_view.to_pandas()
        df_from_extractor = scene_view.extractor.to_pandas()

        # Should be identical
        pd.testing.assert_frame_equal(df_from_scene, df_from_extractor)
