"""
Type definitions for bwell-logkit.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Union

# Core data types
LogRecord = dict[str, Any]
FilterFunction = Callable[[LogRecord], bool]
FilePath = Union[str, Path]


# Common record field names
class RecordFields:
    """Standard field names used across bWell log records."""

    RECORD_TYPE = "myType"
    GAME_TIME_SECS = "timestamp"
    MILLIS_SINCE_EPOCH = "msSinceEpoch"
    ID = "ID"

    class SceneEntry:
        """Fields specific to SceneEntryRecord."""

        SCENE_NAME = "sceneName"


# Record type constants
class RecordTypes:
    """Common bWell log record types."""

    GAME_SETTINGS = "GameSettingsRecord"
    ABSOLUTE_ACTIVITY = "AbsoluteActivityRecord"
    SCENE_ENTRY = "SceneEntryRecord"


# Sender tag constants
class MovementSources:
    """Common sender tags for activity records."""

    HEAD = "Head"
    LEFT_HAND = "LeftHand"
    RIGHT_HAND = "RightHand"


# Scene constants
class Scenes:
    """Common scene names."""

    SOLAR_SYSTEM = "Solar System Menu"
    BUTTERFLY = "Butterfly"
    LAB = "Lab"
    MOLE = "Mole"
    THEATER = "Theater"


# Scene metadata
@dataclass
class SceneInfo:
    """Information about a scene instance."""

    name: str
    instance: int
    start_game_time_secs: float
    end_game_time_secs: float
    start_millis_since_epoch: int
    end_millis_since_epoch: int

    @property
    def duration_secs(self) -> float:
        """Get scene duration in seconds."""
        return self.end_game_time_secs - self.start_game_time_secs

    @property
    def duration_millis(self) -> int:
        """Get scene duration in milliseconds."""
        return self.end_millis_since_epoch - self.start_millis_since_epoch
