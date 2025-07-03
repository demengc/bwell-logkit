"""
Pytest configuration and shared fixtures for bwell-logkit tests.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


@pytest.fixture
def sample_log_data() -> Dict[str, Any]:
    """Sample bWell log data structure with comprehensive test data."""
    return {
        "data": [
            {
                "timestamp": 1.0,
                "msSinceEpoch": 1000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "Head",
                "absolutePosition": {"x": 1.5, "y": 2.0, "z": 0.5},
                "absoluteRotation": {
                    "x": 0.0,
                    "y": 0.707,
                    "z": 0.0,
                    "w": 0.707,
                },
            },
            {
                "timestamp": 2.0,
                "msSinceEpoch": 2000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "LeftHand",
                "absolutePosition": {"x": -0.5, "y": 1.0, "z": 0.3},
                "absoluteRotation": {"x": 0.1, "y": 0.2, "z": 0.3, "w": 0.9},
            },
            {
                "timestamp": 3.0,
                "msSinceEpoch": 3000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "RightHand",
                "absolutePosition": {"x": 0.8, "y": 1.2, "z": 0.4},
                "absoluteRotation": {"x": 0.2, "y": 0.3, "z": 0.4, "w": 0.8},
            },
            {
                "timestamp": 4.0,
                "msSinceEpoch": 4000,
                "myType": "SceneEntryRecord",
                "sceneName": "MainMenu",
            },
            {
                "timestamp": 10.0,
                "msSinceEpoch": 10000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "Head",
                "absolutePosition": {"x": 2.0, "y": 2.5, "z": 1.0},
                "absoluteRotation": {"x": 0.1, "y": 0.8, "z": 0.1, "w": 0.6},
            },
            {
                "timestamp": 15.0,
                "msSinceEpoch": 15000,
                "myType": "SceneEntryRecord",
                "sceneName": "GameLevel1",
            },
            {
                "timestamp": 20.0,
                "msSinceEpoch": 20000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "Head",
                "absolutePosition": {"x": 3.0, "y": 3.0, "z": 1.5},
                "absoluteRotation": {"x": 0.2, "y": 0.9, "z": 0.2, "w": 0.5},
            },
            {
                "timestamp": 22.0,
                "msSinceEpoch": 22000,
                "myType": "AbsoluteActivityRecord",
                "senderTag": "LeftHand",
                "absolutePosition": {"x": 0.0, "y": 1.5, "z": 0.8},
                "absoluteRotation": {"x": 0.3, "y": 0.4, "z": 0.5, "w": 0.7},
            },
            {
                "timestamp": 25.0,
                "msSinceEpoch": 25000,
                "myType": "GameSettingsRecord",
                "setting": "volume",
                "value": 0.8,
            },
        ]
    }


@pytest.fixture
def truncated_log_data() -> str:
    """Sample truncated log content with trailing comma and missing ]}."""
    return (
        '{"data": [{"timestamp": 1.0, '
        '"myType": "AbsoluteActivityRecord", '
        '"senderTag": "Head"},'
    )


@pytest.fixture
def empty_log_data() -> Dict[str, Any]:
    """Empty log data structure."""
    return {"data": []}


@pytest.fixture
def malformed_log_data() -> str:
    """Malformed bWell log missing closing ]}."""
    return '{"data": [{"timestamp": 1.0, "myType": "AbsoluteActivityRecord"}'


@pytest.fixture
def sample_log_file(sample_log_data, tmp_path) -> Path:
    """Create a temporary log file with sample data."""
    log_file = tmp_path / "test_log.json"
    log_file.write_text(json.dumps(sample_log_data))
    return log_file


@pytest.fixture
def truncated_log_file(truncated_log_data, tmp_path) -> Path:
    """Create a temporary truncated log file."""
    log_file = tmp_path / "truncated_log.json"
    log_file.write_text(truncated_log_data)
    return log_file


@pytest.fixture
def empty_log_file(empty_log_data, tmp_path) -> Path:
    """Create a temporary empty log file."""
    log_file = tmp_path / "empty_log.json"
    log_file.write_text(json.dumps(empty_log_data))
    return log_file


@pytest.fixture
def malformed_log_file(malformed_log_data, tmp_path) -> Path:
    """Create a temporary malformed log file."""
    log_file = tmp_path / "malformed_log.json"
    log_file.write_text(malformed_log_data)
    return log_file


@pytest.fixture
def sample_records(sample_log_data) -> List[Dict[str, Any]]:
    """Extract records from sample log data."""
    return sample_log_data["data"]


@pytest.fixture
def movement_records(sample_records) -> List[Dict[str, Any]]:
    """Filter sample records to only movement records."""
    return [r for r in sample_records if r.get("myType") == "AbsoluteActivityRecord"]


@pytest.fixture
def scene_records(sample_records) -> List[Dict[str, Any]]:
    """Filter sample records to only scene records."""
    return [r for r in sample_records if r.get("myType") == "SceneEntryRecord"]


@pytest.fixture
def log_directory(tmp_path, sample_log_data) -> Path:
    """Create a directory with multiple log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Create multiple log files with variations
    for i in range(3):
        log_file = log_dir / f"log_{i}.json"
        # Modify timestamps to make files unique
        data = sample_log_data.copy()
        for record in data["data"]:
            record["timestamp"] = record["timestamp"] + (i * 100)
            record["msSinceEpoch"] = record["msSinceEpoch"] + (i * 100000)
        log_file.write_text(json.dumps(data))

    return log_dir


@pytest.fixture
def invalid_json_file(tmp_path) -> Path:
    """Create a file with completely invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("this is not json at all { invalid }")
    return invalid_file


@pytest.fixture
def no_data_field_file(tmp_path) -> Path:
    """Create a JSON file without the required 'data' field."""
    no_data_file = tmp_path / "no_data.json"
    no_data_file.write_text('{"other_field": "value", "records": []}')
    return no_data_file
