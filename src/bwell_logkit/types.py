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

    class MoleHit:
        """Fields specific to MoleHitRecord."""

        RESULT = "result"
        MOLE_LIFE_TIME = "moleLifeTime"
        WAS_TRICKY = "wasTricky"


# Record type constants
class RecordTypes:
    """Common bWell log record types."""

    GAME_SETTINGS = "GameSettingsRecord"
    ABSOLUTE_ACTIVITY = "AbsoluteActivityRecord"
    SCENE_ENTRY = "SceneEntryRecord"
    MOLE_HIT = "MoleHitRecord"


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


# Mole result constants
class MoleResults:
    """Constants for mole result types."""

    # Mole hit by correct colored hammer
    SUCCESS_CORRECT_COLOR = 0
    # Tricky mole ignored
    IGNORED_TRICKY = 1
    # Mole hit by wrong colored hammer
    ERROR_GENERIC_WRONG_COLOR = 2
    # Mole hit by hammer that used to be the correct color
    ERROR_PREVIOUS_HAND_COLOR = 3
    # Mole hit by hammer of wrong color; other hand had correct color
    ERROR_WRONG_HAND = 4
    # Mole timed out and disappeared, had matching color period
    MISSED = 5
    # Tricky mole hit before the stop signal
    EARLY_RESPONSE_ON_TRICKY = 6
    # Mole timed out, never had matching color
    IGNORED_INVALID = 7
    # Mole table cleared of remaining moles in play
    TABLE_CLEARING = 8


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
