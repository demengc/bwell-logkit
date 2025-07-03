"""
Tests for the scene module and SceneManager class.
"""

import pytest

from bwell_logkit.exceptions import SceneNotFoundError
from bwell_logkit.scene import SceneManager
from bwell_logkit.types import SceneInfo


class TestSceneManager:
    """Test cases for SceneManager class."""

    def test_init_basic(self, sample_records):
        """Test basic SceneManager initialization."""
        manager = SceneManager(sample_records)
        assert manager is not None

    def test_list_scenes(self, sample_records):
        """Test listing available scenes."""
        manager = SceneManager(sample_records)
        scenes = manager.list_scenes()

        assert isinstance(scenes, list)
        assert "MainMenu" in scenes
        assert "GameLevel1" in scenes

    def test_has_scene_valid(self, sample_records):
        """Test has_scene with valid scene."""
        manager = SceneManager(sample_records)

        assert manager.has_scene("MainMenu", 0) is True
        assert manager.has_scene("GameLevel1", 0) is True

    def test_has_scene_invalid(self, sample_records):
        """Test has_scene with invalid scene."""
        manager = SceneManager(sample_records)

        assert manager.has_scene("NonExistentScene", 0) is False
        assert manager.has_scene("MainMenu", 10) is False  # Invalid instance

    def test_get_scene_count(self, sample_records):
        """Test getting scene instance count."""
        manager = SceneManager(sample_records)

        main_menu_count = manager.get_scene_count("MainMenu")
        assert main_menu_count == 1

        nonexistent_count = manager.get_scene_count("NonExistentScene")
        assert nonexistent_count == 0

    def test_get_scene_info_valid(self, sample_records):
        """Test getting scene info for valid scene."""
        manager = SceneManager(sample_records)
        scene_info = manager.get_scene_info("MainMenu", 0)

        assert isinstance(scene_info, SceneInfo)
        assert scene_info.name == "MainMenu"
        assert scene_info.instance == 0
        assert scene_info.start_game_time_secs == 4.0
        assert scene_info.end_game_time_secs == 15.0
        assert scene_info.duration_secs == 11.0

    def test_get_scene_info_invalid(self, sample_records):
        """Test getting scene info for invalid scene."""
        manager = SceneManager(sample_records)

        with pytest.raises(SceneNotFoundError):
            manager.get_scene_info("NonExistentScene", 0)

        with pytest.raises(SceneNotFoundError):
            manager.get_scene_info("MainMenu", 10)

    def test_get_scene_records(self, sample_records):
        """Test getting records for a scene."""
        manager = SceneManager(sample_records)
        scene_records = manager.get_scene_records("MainMenu", 0)

        assert isinstance(scene_records, list)
        assert len(scene_records) > 0

        # All records should be within the scene time range
        scene_info = manager.get_scene_info("MainMenu", 0)
        for record in scene_records:
            timestamp = record.get("timestamp", 0)
            assert (
                scene_info.start_game_time_secs
                <= timestamp
                <= scene_info.end_game_time_secs
            )

    def test_get_all_scene_instances(self, sample_records):
        """Test getting all instances of a scene."""
        manager = SceneManager(sample_records)
        instances = manager.get_all_scene_instances("MainMenu")

        assert isinstance(instances, list)
        assert len(instances) == 1
        assert instances[0].name == "MainMenu"

    def test_get_all_scene_instances_invalid(self, sample_records):
        """Test getting instances for non-existent scene."""
        manager = SceneManager(sample_records)

        with pytest.raises(SceneNotFoundError):
            manager.get_all_scene_instances("NonExistentScene")

    def test_get_all_scene_instances_chron(self, sample_records):
        """Test getting all scenes in chronological order."""
        manager = SceneManager(sample_records)
        chron_scenes = manager.get_all_scene_instances_chron()

        assert isinstance(chron_scenes, list)
        assert len(chron_scenes) == 2  # MainMenu and GameLevel1

        # Should be sorted by start time
        assert (
            chron_scenes[0].start_game_time_secs <= chron_scenes[1].start_game_time_secs
        )

    def test_get_all_scene_instances_chron_epoch(self, sample_records):
        """Test getting all scenes in chronological order by epoch time."""
        manager = SceneManager(sample_records)
        chron_scenes = manager.get_all_scene_instances_chron(use_epoch_time=True)

        assert isinstance(chron_scenes, list)
        assert len(chron_scenes) == 2

        # Should be sorted by epoch time
        assert (
            chron_scenes[0].start_millis_since_epoch
            <= chron_scenes[1].start_millis_since_epoch
        )

    def test_get_scene_summary(self, sample_records):
        """Test getting scene summary."""
        manager = SceneManager(sample_records)
        summary = manager.get_scene_summary()

        assert isinstance(summary, dict)
        assert "MainMenu" in summary
        assert "GameLevel1" in summary

        # Check MainMenu summary structure
        main_menu_summary = summary["MainMenu"]
        assert main_menu_summary["instance_count"] == 1
        assert main_menu_summary["total_duration_secs"] > 0
        assert main_menu_summary["average_duration_secs"] > 0
        assert "instances" in main_menu_summary

        # Check instance details
        instance = main_menu_summary["instances"][0]
        assert instance["instance"] == 0
        assert "start_game_time_secs" in instance
        assert "end_game_time_secs" in instance
        assert "duration_secs" in instance


class TestSceneManagerEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_records(self):
        """Test SceneManager with empty records."""
        manager = SceneManager([])

        assert manager.list_scenes() == []
        assert manager.get_scene_count("AnyScene") == 0
        assert manager.has_scene("AnyScene", 0) is False

    def test_no_scene_records(self, movement_records):
        """Test SceneManager with no scene entry records."""
        manager = SceneManager(movement_records)

        assert manager.list_scenes() == []
        assert manager.get_scene_summary() == {}

    def test_malformed_scene_records(self, sample_records):
        """Test SceneManager with malformed scene records."""
        # Add a scene record without sceneName
        malformed_records = sample_records + [
            {
                "timestamp": 30.0,
                "msSinceEpoch": 30000,
                "myType": "SceneEntryRecord",
                # Missing sceneName field
            }
        ]

        manager = SceneManager(malformed_records)
        scenes = manager.list_scenes()

        # Should still work with valid scenes
        assert "MainMenu" in scenes
        assert "GameLevel1" in scenes


class TestSceneInfo:
    """Test SceneInfo dataclass functionality."""

    def test_scene_info_creation(self):
        """Test SceneInfo creation and properties."""
        scene_info = SceneInfo(
            name="TestScene",
            instance=1,
            start_game_time_secs=10.0,
            end_game_time_secs=25.0,
            start_millis_since_epoch=10000,
            end_millis_since_epoch=25000,
        )

        assert scene_info.name == "TestScene"
        assert scene_info.instance == 1
        assert scene_info.duration_secs == 15.0
        assert scene_info.duration_millis == 15000

    def test_scene_info_zero_duration(self):
        """Test SceneInfo with zero duration."""
        scene_info = SceneInfo(
            name="InstantScene",
            instance=0,
            start_game_time_secs=5.0,
            end_game_time_secs=5.0,
            start_millis_since_epoch=5000,
            end_millis_since_epoch=5000,
        )

        assert scene_info.duration_secs == 0.0
        assert scene_info.duration_millis == 0
