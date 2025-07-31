"""
Type definitions for bwell-logkit.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

# Core data types
LogRecord = dict[str, Any]
FilterFunction = Callable[[LogRecord], bool]
FilePath = Union[str, Path]

# Type variable for enum types
T = TypeVar("T", bound="BWellEnum")


class BWellEnum(Enum):
    """Base enum class with bidirectional lookup methods."""

    @classmethod
    def from_value(cls: type[T], value: Any) -> T:
        """Get enum member from its raw value. Raises ValueError if not found."""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No {cls.__name__} member with value {value!r}")

    @classmethod
    def try_from_value(
        cls: type[T], value: Any, default: Optional[Any] = None
    ) -> Optional[T]:
        """Get enum member from its raw value, returning default if not found."""
        try:
            return cls.from_value(value)
        except ValueError:
            return default

    @classmethod
    def get_value_mapping(cls) -> dict:
        """Get a mapping of all raw values to their descriptive names."""
        return {member.value: member.name for member in cls}

    @classmethod
    def get_description_mapping(cls) -> dict:
        """Get a mapping of all raw values to their descriptions (docstrings)."""
        return {member.value: member.__doc__ or member.name for member in cls}


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


class RecordTypes(BWellEnum):
    """Common bWell log record types."""

    GAME_SETTINGS = "GameSettingsRecord"
    ABSOLUTE_ACTIVITY = "AbsoluteActivityRecord"
    SCENE_ENTRY = "SceneEntryRecord"
    MOLE_HIT = "MoleHitRecord"


class MovementSources(BWellEnum):
    """Common sender tags for activity records."""

    HEAD = "Head"
    LEFT_HAND = "LeftHand"
    RIGHT_HAND = "RightHand"


class Scenes(BWellEnum):
    """Common scene names."""

    SOLAR_SYSTEM = "Solar System Menu"
    BUTTERFLY = "Butterfly"
    LAB = "Lab"
    MOLE = "Mole"
    THEATER = "Theater"


class MoleResults(BWellEnum):
    """Constants for mole result types with bidirectional lookup."""

    SUCCESS_CORRECT_COLOR = 0
    IGNORED_TRICKY = 1
    ERROR_GENERIC_WRONG_COLOR = 2
    ERROR_PREVIOUS_HAND_COLOR = 3
    ERROR_WRONG_HAND = 4
    MISSED = 5
    EARLY_RESPONSE_ON_TRICKY = 6
    IGNORED_INVALID = 7
    TABLE_CLEARING = 8

    @classmethod
    def get_description_mapping(cls) -> dict:
        """Get a mapping of all raw values to their descriptions."""
        descriptions = {
            0: "Mole hit by correct colored hammer",
            1: "Tricky mole ignored",
            2: "Mole hit by wrong colored hammer",
            3: "Mole hit by hammer that used to be the correct color",
            4: "Mole hit by hammer of wrong color; other hand had correct color",
            5: "Mole timed out and disappeared, had matching color period",
            6: "Tricky mole hit before the stop signal",
            7: "Mole timed out, never had matching color",
            8: "Mole table cleared of remaining moles in play",
        }
        return descriptions


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
