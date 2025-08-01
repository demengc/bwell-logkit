"""
Type definitions for bwell-logkit.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum, unique
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, TypeVar

# Core data types
LogRecord = dict[str, Any]
FilterFunction = Callable[[LogRecord], bool]
FilePath = str | Path

# Type variable for enum types
T = TypeVar("T", bound="BWellEnum")


class BWellEnum(Enum):
    """Base enum class with bidirectional lookup methods."""

    @classmethod
    def from_value(cls: type[T], value: Any) -> T:
        """Get enum member from its raw value. Raises ValueError if not found."""
        return cls(value)

    @classmethod
    def try_from_value(
        cls: type[T], value: Any, /, default: Optional[T] = None
    ) -> Optional[T]:
        """Get enum member from its raw value, returning default if not found."""
        try:
            return cls.from_value(value)
        except ValueError:
            return default

    @classmethod
    def get_value_mapping(cls) -> Mapping[Any, str]:
        """Get a mapping of all raw values to their descriptive names."""
        return {member.value: member.name for member in cls}

    @classmethod
    def get_description_mapping(cls) -> Mapping[Any, str]:
        """Get a mapping of all raw values to their descriptions (docstrings)."""
        return {member.value: member.__doc__ or member.name for member in cls}


# Common record field names
@unique
class RecordFields(StrEnum):
    """Standard field names used across bWell log records."""

    RECORD_TYPE = "myType"
    GAME_TIME_SECS = "timestamp"
    MILLIS_SINCE_EPOCH = "msSinceEpoch"
    ID = "ID"


@unique
class SceneEntryRecordFields(StrEnum):
    """Fields specific to SceneEntryRecord."""

    SCENE_NAME = "sceneName"


@unique
class MoleHitRecordFields(StrEnum):
    """Fields specific to MoleHitRecord."""

    RESULT = "result"
    MOLE_LIFE_TIME = "moleLifeTime"
    WAS_TRICKY = "wasTricky"


@unique
class RecordTypes(StrEnum):
    """Common bWell log record types."""

    GAME_SETTINGS = "GameSettingsRecord"
    ABSOLUTE_ACTIVITY = "AbsoluteActivityRecord"
    SCENE_ENTRY = "SceneEntryRecord"
    MOLE_HIT = "MoleHitRecord"


@unique
class MovementSources(StrEnum):
    """Common sender tags for activity records."""

    HEAD = "Head"
    LEFT_HAND = "LeftHand"
    RIGHT_HAND = "RightHand"


@unique
class Scenes(StrEnum):
    """Common scene names."""

    SOLAR_SYSTEM = "Solar System Menu"
    BUTTERFLY = "Butterfly"
    LAB = "Lab"
    MOLE = "Mole"
    THEATER = "Theater"


@unique
class MoleResults(IntEnum):
    """Constants for mole result types with bidirectional lookup."""

    SUCCESS_CORRECT_COLOR = 0  # Mole hit by correct colored hammer
    IGNORED_TRICKY = 1  # Tricky mole ignored
    ERROR_GENERIC_WRONG_COLOR = 2  # Mole hit by wrong colored hammer
    ERROR_PREVIOUS_HAND_COLOR = (
        3  # Mole hit by hammer that used to be the correct color
    )
    ERROR_WRONG_HAND = (
        4  # Mole hit by hammer of wrong color; other hand had correct color
    )
    MISSED = 5  # Mole timed out and disappeared, had matching color period
    EARLY_RESPONSE_ON_TRICKY = 6  # Tricky mole hit before the stop signal
    IGNORED_INVALID = 7  # Mole timed out, never had matching color
    TABLE_CLEARING = 8  # Mole table cleared of remaining moles in play


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
