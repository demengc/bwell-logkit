"""
Tests for the logs module (LogSession and SceneView classes).
"""

import pandas as pd
import pytest

from bwell_logkit.exceptions import SceneNotFoundError
from bwell_logkit.logs import LogSession, SceneView, _clean_records
from bwell_logkit.types import SceneInfo


class TestCleanRecords:
    """Test the _clean_records utility function."""

    def test_clean_records_removes_duplicates(self):
        """Test that duplicate records are removed."""
        records = [
            {"myType": "test", "timestamp": 1.0, "value": "a"},
            {"myType": "test", "timestamp": 2.0, "value": "b"},
            {"myType": "test", "timestamp": 1.0, "value": "a"},  # Duplicate
        ]

        cleaned = _clean_records(records)
        assert len(cleaned) == 2
        assert cleaned[0]["timestamp"] == pytest.approx(1.0)
        assert cleaned[1]["timestamp"] == pytest.approx(2.0)

    def test_clean_records_sorts_by_timestamp(self):
        """Test that records are sorted by timestamp."""
        records = [
            {"myType": "test", "timestamp": 3.0},
            {"myType": "test", "timestamp": 1.0},
            {"myType": "test", "timestamp": 2.0},
        ]

        cleaned = _clean_records(records)
        assert len(cleaned) == 3
        assert cleaned[0]["timestamp"] == pytest.approx(1.0)
        assert cleaned[1]["timestamp"] == pytest.approx(2.0)
        assert cleaned[2]["timestamp"] == pytest.approx(3.0)

    def test_clean_records_handles_missing_timestamp(self):
        """Test handling of records without timestamp."""
        records = [
            {"myType": "test", "timestamp": 2.0},
            {"myType": "test"},  # No timestamp
            {"myType": "test", "timestamp": 1.0},
        ]

        cleaned = _clean_records(records)
        assert len(cleaned) == 3
        # Record without timestamp should be sorted to beginning (0)
        assert cleaned[0].get("timestamp", 0) == 0
        assert cleaned[1]["timestamp"] == pytest.approx(1.0)
        assert cleaned[2]["timestamp"] == pytest.approx(2.0)


class TestLogSession:
    """Test cases for LogSession class."""

    def test_init_basic(self, sample_records):
        """Test basic LogSession initialization."""
        session = LogSession(sample_records)

        assert len(session) == 9
        assert len(session.records) == 9
        assert session.metadata == {}

    def test_init_with_metadata(self, sample_records):
        """Test LogSession initialization with metadata."""
        metadata = {"file_path": "/test/path.json", "user": "test_user"}
        session = LogSession(sample_records, metadata)

        assert session.metadata["file_path"] == "/test/path.json"
        assert session.metadata["user"] == "test_user"

    def test_records_property_returns_copy(self, sample_records):
        """Test that records property returns a copy."""
        session = LogSession(sample_records)
        records_copy = session.records

        # Modify the copy
        records_copy[0]["modified"] = True

        # Original should be unchanged
        assert "modified" not in session.records[0]

    def test_metadata_property_returns_copy(self, sample_records):
        """Test that metadata property returns a copy."""
        metadata = {"test": "value"}
        session = LogSession(sample_records, metadata)
        metadata_copy = session.metadata

        # Modify the copy
        metadata_copy["modified"] = True

        # Original should be unchanged
        assert "modified" not in session.metadata

    def test_repr(self, sample_records):
        """Test string representation."""
        session = LogSession(sample_records)
        assert repr(session) == "LogSession(9 records)"

    def test_scene_manager_property(self, sample_records):
        """Test scene_manager property lazy loading."""
        session = LogSession(sample_records)

        # First access creates the manager
        manager1 = session.scene_manager
        assert manager1 is not None

        # Second access returns the same instance
        manager2 = session.scene_manager
        assert manager1 is manager2

    def test_extractor_property(self, sample_records):
        """Test extractor property lazy loading."""
        session = LogSession(sample_records)

        # First access creates the extractor
        extractor1 = session.extractor
        assert extractor1 is not None

        # Second access returns the same instance
        extractor2 = session.extractor
        assert extractor1 is extractor2

    def test_list_scenes(self, sample_records):
        """Test list_scenes method."""
        session = LogSession(sample_records)
        scenes = session.list_scenes()

        assert isinstance(scenes, list)
        assert "MainMenu" in scenes
        assert "GameLevel1" in scenes

    def test_scene_method_valid_scene(self, sample_records):
        """Test scene method with valid scene."""
        session = LogSession(sample_records)
        scene_view = session.scene("MainMenu")

        assert isinstance(scene_view, SceneView)
        assert scene_view.info.name == "MainMenu"
        assert scene_view.info.instance == 0

    def test_scene_method_invalid_scene(self, sample_records):
        """Test scene method with invalid scene."""
        session = LogSession(sample_records)

        with pytest.raises(SceneNotFoundError) as exc_info:
            session.scene("NonExistentScene")

        assert "NonExistentScene" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_filter_basic(self, sample_records):
        """Test basic filtering."""
        session = LogSession(sample_records)

        filtered = session.filter(lambda r: r.get("senderTag") == "Head")

        assert isinstance(filtered, LogSession)
        assert len(filtered) == 3  # 3 Head records in sample data
        for record in filtered.records:
            assert record["senderTag"] == "Head"

    def test_filter_type(self, sample_records):
        """Test filtering by record type."""
        session = LogSession(sample_records)

        movement_session = session.filter_type("AbsoluteActivityRecord")

        assert len(movement_session) == 6  # 6 movement records in sample data
        for record in movement_session.records:
            assert record["myType"] == "AbsoluteActivityRecord"

    def test_filter_type_multiple(self, sample_records):
        """Test filtering by multiple record types."""
        session = LogSession(sample_records)

        filtered = session.filter_type("AbsoluteActivityRecord", "SceneEntryRecord")

        assert len(filtered) == 8  # 6 movement + 2 scene records = 8

    def test_filter_time_range(self, sample_records):
        """Test filtering by time range."""
        session = LogSession(sample_records)

        # Filter for records between 1 and 15 seconds
        filtered = session.filter_time_range(1.0, 15.0)

        assert len(filtered) > 0
        for record in filtered.records:
            timestamp = record.get("timestamp", 0)
            assert 1.0 <= timestamp <= 15.0

    def test_filter_preserves_metadata(self, sample_records):
        """Test that filtering preserves metadata."""
        metadata = {"file_path": "/test/path.json"}
        session = LogSession(sample_records, metadata)

        filtered = session.filter(lambda r: True)

        assert filtered.metadata == metadata

    def test_get_stats_basic(self, sample_records):
        """Test basic statistics generation."""
        session = LogSession(sample_records)
        stats = session.get_stats()

        assert stats["total_records"] == 9
        assert "AbsoluteActivityRecord" in stats["record_types"]
        assert "SceneEntryRecord" in stats["record_types"]
        assert stats["record_types"]["AbsoluteActivityRecord"] == 6
        assert stats["record_types"]["SceneEntryRecord"] == 2

    def test_get_stats_empty_session(self):
        """Test statistics for empty session."""
        session = LogSession([])
        stats = session.get_stats()

        assert stats["total_records"] == 0
        assert stats["record_types"] == {}
        assert stats["game_time_range"] is None
        assert stats["millis_since_epoch_range"] is None

    def test_get_stats_time_ranges(self, sample_records):
        """Test time range calculation in statistics."""
        session = LogSession(sample_records)
        stats = session.get_stats()

        assert stats["game_time_range"]["start"] == pytest.approx(1.0)
        assert stats["game_time_range"]["end"] == pytest.approx(25.0)
        assert stats["millis_since_epoch_range"]["start"] == 1000
        assert stats["millis_since_epoch_range"]["end"] == 25000

    def test_to_pandas_basic(self, sample_records):
        """Test pandas DataFrame export."""
        session = LogSession(sample_records)
        df = session.to_pandas()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 9
        assert "myType" in df.columns
        assert "timestamp" in df.columns

    def test_export_csv(self, sample_records, tmp_path):
        """Test CSV export."""
        session = LogSession(sample_records)
        output_file = tmp_path / "test_output.csv"

        session.export_csv(str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestSceneView:
    """Test cases for SceneView class."""

    def test_init_basic(self, sample_records):
        """Test basic SceneView initialization."""
        session = LogSession(sample_records)
        scene_info = SceneInfo(
            name="TestScene",
            instance=0,
            start_game_time_secs=1.0,
            end_game_time_secs=10.0,
            start_millis_since_epoch=1000,
            end_millis_since_epoch=10000,
        )

        scene_view = SceneView(session, scene_info)

        assert len(scene_view) == 9
        assert scene_view.info.name == "TestScene"
        assert scene_view.info.instance == 0

    def test_records_property(self, sample_records):
        """Test records property."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        assert len(scene_view.records) == 9
        assert scene_view.records == session.records

    def test_metadata_property(self, sample_records):
        """Test metadata property."""
        metadata = {"file_path": "/test/path.json"}
        session = LogSession(sample_records, metadata)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        assert scene_view.metadata == metadata

    def test_extractor_property(self, sample_records):
        """Test extractor property lazy loading."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        extractor = scene_view.extractor
        assert extractor is not None

    def test_repr(self, sample_records):
        """Test string representation."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        expected = "SceneView(TestScene, instance=0, 9 records)"
        assert repr(scene_view) == expected

    def test_filter_returns_scene_view(self, sample_records):
        """Test that filtering returns a SceneView."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        filtered = scene_view.filter(lambda r: r.get("senderTag") == "Head")

        assert isinstance(filtered, SceneView)
        assert filtered.info.name == "Test"
        assert len(filtered) == 3

    def test_filter_type_returns_scene_view(self, sample_records):
        """Test that filter_type returns a SceneView."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        filtered = scene_view.filter_type("AbsoluteActivityRecord")

        assert isinstance(filtered, SceneView)
        assert filtered.info.name == "Test"
        assert len(filtered) == 6

    def test_filter_time_range_returns_scene_view(self, sample_records):
        """Test that filter_time_range returns a SceneView."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        filtered = scene_view.filter_time_range(1.0, 5.0)

        assert isinstance(filtered, SceneView)
        assert filtered.info.name == "Test"

    def test_get_stats_includes_scene_info(self, sample_records):
        """Test that get_stats includes scene information."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        stats = scene_view.get_stats()

        assert "scene_info" in stats
        assert stats["scene_info"]["name"] == "TestScene"
        assert stats["scene_info"]["instance"] == 0
        assert stats["scene_info"]["duration_secs"] == pytest.approx(9.0)
        assert "scenes" not in stats  # Should be removed for scene view

    def test_to_pandas_includes_scene_metadata(self, sample_records):
        """Test that to_pandas includes scene metadata by default."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 1, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        df = scene_view.to_pandas()

        assert "scene_name" in df.columns
        assert "scene_instance" in df.columns
        assert "scene_duration" in df.columns
        assert df["scene_name"].iloc[0] == "TestScene"
        assert df["scene_instance"].iloc[0] == 1
        assert df["scene_duration"].iloc[0] == pytest.approx(9.0)

    def test_to_pandas_exclude_scene_metadata(self, sample_records):
        """Test to_pandas with scene metadata excluded."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        df = scene_view.to_pandas(include_scene_info=False)

        assert "scene_name" not in df.columns
        assert "scene_instance" not in df.columns

    def test_export_csv_includes_scene_metadata(self, sample_records, tmp_path):
        """Test CSV export includes scene metadata."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("TestScene", 0, 1.0, 10.0, 1000, 10000)
        scene_view = SceneView(session, scene_info)

        output_file = tmp_path / "scene_output.csv"
        scene_view.export_csv(str(output_file))

        assert output_file.exists()
        # Read the file to verify scene columns are included
        content = output_file.read_text()
        assert "scene_name" in content
        assert "TestScene" in content


class TestChainedOperations:
    """Test chained operations and complex scenarios."""

    def test_complex_filtering_chain(self, sample_records):
        """Test chaining multiple filtering operations."""
        session = LogSession(sample_records)

        result = (
            session.filter_type("AbsoluteActivityRecord")
            .filter(lambda r: r.get("senderTag") in ["Head", "LeftHand"])
            .filter_time_range(1.0, 20.0)
        )

        assert isinstance(result, LogSession)
        assert len(result) > 0

        # Verify all filters were applied
        for record in result.records:
            assert record["myType"] == "AbsoluteActivityRecord"
            assert record["senderTag"] in ["Head", "LeftHand"]
            assert 1.0 <= record["timestamp"] <= 20.0

    def test_scene_view_filtering_chain(self, sample_records):
        """Test chaining operations on SceneView."""
        session = LogSession(sample_records)
        scene_info = SceneInfo("Test", 0, 1.0, 25.0, 1000, 25000)
        scene_view = SceneView(session, scene_info)

        result = scene_view.filter_type("AbsoluteActivityRecord").filter(
            lambda r: r.get("senderTag") == "Head"
        )

        assert isinstance(result, SceneView)
        assert result.info.name == "Test"
        assert len(result) == 3  # 3 Head records
