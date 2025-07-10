"""
Tests for the reader module.
"""

from pathlib import Path

import orjson
import pytest

from bwell_logkit.exceptions import LogReadError
from bwell_logkit.logs import LogSession
from bwell_logkit.reader import _heal_json, load_all_logs, load_log, read_records


class TestReadRecords:
    """Test cases for read_records function."""

    def test_read_valid_log_file(self, sample_log_file, sample_log_data):
        """Test reading a valid log file."""
        records = read_records(sample_log_file)

        assert len(records) == 9
        assert records[0]["myType"] == "AbsoluteActivityRecord"
        assert records[0]["senderTag"] == "Head"
        assert records[3]["myType"] == "SceneEntryRecord"
        assert records[3]["sceneName"] == "MainMenu"

    def test_read_empty_log_file(self, empty_log_file):
        """Test reading an empty log file."""
        records = read_records(empty_log_file)
        assert records == []

    def test_read_truncated_log_file(self, truncated_log_file):
        """Test reading and healing a truncated log file."""
        records = read_records(truncated_log_file)

        # Should successfully heal and read at least one record
        assert len(records) >= 1
        assert records[0]["myType"] == "AbsoluteActivityRecord"

    def test_read_malformed_log_file(self, malformed_log_file):
        """Test reading a malformed but healable log file."""
        records = read_records(malformed_log_file)

        assert len(records) == 1
        assert records[0]["myType"] == "AbsoluteActivityRecord"

    def test_file_not_found(self, tmp_path):
        """Test error handling when file doesn't exist."""
        non_existent_file = tmp_path / "does_not_exist.json"

        with pytest.raises(LogReadError) as exc_info:
            read_records(non_existent_file)

        assert "File not found" in str(exc_info.value)
        assert str(non_existent_file) in str(exc_info.value)

    def test_invalid_json(self, invalid_json_file):
        """Test error handling for completely invalid JSON."""
        with pytest.raises(LogReadError) as exc_info:
            read_records(invalid_json_file)

        assert "Failed to parse JSON" in str(exc_info.value)

    def test_missing_data_field(self, no_data_field_file):
        """Test error handling when 'data' field is missing."""
        with pytest.raises(LogReadError) as exc_info:
            read_records(no_data_field_file)

        assert "missing 'data' array" in str(exc_info.value)

    def test_string_path_input(self, sample_log_file):
        """Test that string paths work as well as Path objects."""
        records = read_records(str(sample_log_file))
        assert len(records) == 9

    def test_encoding_parameter(self, sample_log_file):
        """Test custom encoding parameter."""
        records = read_records(sample_log_file, encoding="utf-8")
        assert len(records) == 9


class TestLoadLog:
    """Test cases for load_log function."""

    def test_load_log_basic(self, sample_log_file):
        """Test basic log loading."""
        session = load_log(sample_log_file)

        assert isinstance(session, LogSession)
        assert len(session) == 9
        assert len(session.records) == 9

    def test_load_log_metadata(self, sample_log_file):
        """Test metadata is properly set."""
        session = load_log(sample_log_file)

        assert "file_path" in session.metadata
        assert session.metadata["file_path"] == str(sample_log_file)

    def test_load_log_with_kwargs(self, sample_log_file):
        """Test load_log passes kwargs to read_records."""
        session = load_log(sample_log_file, encoding="utf-8")
        assert len(session) == 9

    def test_load_log_error_propagation(self, tmp_path):
        """Test that errors from read_records are propagated."""
        non_existent_file = tmp_path / "does_not_exist.json"

        with pytest.raises(LogReadError):
            load_log(non_existent_file)


class TestJsonHealing:
    """Test cases for bWell JSON healing functionality."""

    def test_heal_json_trailing_comma_missing_brackets(self):
        """Test healing bWell log with trailing comma and missing ]}."""
        malformed = '{"data": [{"test": "value"},'
        healed = _heal_json(malformed)

        result = orjson.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_missing_closing_bracket_only(self):
        """Test healing bWell log with missing } only."""
        malformed = '{"data": [{"test": "value"}]'
        healed = _heal_json(malformed)

        result = orjson.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_already_valid(self):
        """Test healing already valid JSON doesn't break it."""
        valid = '{"data": [{"test": "value"}]}'
        healed = _heal_json(valid)

        result = orjson.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_strip_whitespace(self):
        """Test that healing strips whitespace."""
        malformed = '  {"data": [{"test": "value"}]  '
        healed = _heal_json(malformed)

        result = orjson.loads(healed)
        assert result["data"][0]["test"] == "value"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_file_content(self, tmp_path):
        """Test handling of completely empty file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        with pytest.raises(LogReadError) as exc_info:
            read_records(empty_file)

        assert "File is empty" in str(exc_info.value)

    def test_data_field_not_list(self, tmp_path):
        """Test error when 'data' field is not a list."""
        bad_data_file = tmp_path / "bad_data.json"
        bad_data_file.write_text('{"data": "not a list"}')

        with pytest.raises(LogReadError) as exc_info:
            read_records(bad_data_file)

        assert "missing 'data' array" in str(exc_info.value)

    def test_root_not_object(self, tmp_path):
        """Test error when root is not an object."""
        bad_root_file = tmp_path / "bad_root.json"
        bad_root_file.write_text('["this", "is", "a", "list"]')

        with pytest.raises(LogReadError) as exc_info:
            read_records(bad_root_file)

        assert "root must be an object" in str(exc_info.value)


class TestLoadAllLogs:
    """Test cases for load_all_logs function."""

    def test_load_all_logs_basic(self, log_directory):
        """Test basic functionality of loading all logs from a directory."""
        sessions = load_all_logs(log_directory)

        # Should have 3 log files from the fixture
        assert len(sessions) == 3
        assert all(isinstance(session, LogSession) for session in sessions.values())

        # Check relative paths are correct
        expected_paths = {"log_0.json", "log_1.json", "log_2.json"}
        assert set(sessions.keys()) == expected_paths

        # Check each session has records
        for path, session in sessions.items():
            assert len(session) == 9  # Each log has 9 records from fixture
            assert session.metadata["relative_path"] == path
            assert "file_path" in session.metadata

    def test_load_all_logs_recursive(self, tmp_path, sample_log_data):
        """Test recursive directory search."""
        # Create nested directory structure
        base_dir = tmp_path / "logs"
        base_dir.mkdir()

        # Create subdirectories
        adhd_dir = base_dir / "ADHD"
        adhd_dir.mkdir()
        control_dir = base_dir / "control"
        control_dir.mkdir()

        # Create log files in different directories
        (base_dir / "session_1.json").write_text(orjson.dumps(sample_log_data).decode())
        (adhd_dir / "participant_01.json").write_text(
            orjson.dumps(sample_log_data).decode()
        )
        (control_dir / "participant_02.json").write_text(
            orjson.dumps(sample_log_data).decode()
        )

        sessions = load_all_logs(base_dir)

        assert len(sessions) == 3
        expected_paths = {
            "session_1.json",
            "ADHD/participant_01.json",
            "control/participant_02.json",
        }
        assert set(sessions.keys()) == expected_paths

        # Check relative paths in metadata
        for path, session in sessions.items():
            assert session.metadata["relative_path"] == path

    def test_load_all_logs_custom_pattern(self, tmp_path, sample_log_data):
        """Test custom file pattern filtering."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create files with different extensions
        (log_dir / "log1.json").write_text(orjson.dumps(sample_log_data).decode())
        (log_dir / "log2.bwell").write_text(orjson.dumps(sample_log_data).decode())
        (log_dir / "log3.txt").write_text("not a log file")

        # Test default pattern (*.json)
        sessions_json = load_all_logs(log_dir)
        assert len(sessions_json) == 1
        assert "log1.json" in sessions_json

        # Test custom pattern (*.bwell)
        sessions_bwell = load_all_logs(log_dir, file_pattern="*.bwell")
        assert len(sessions_bwell) == 1
        assert "log2.bwell" in sessions_bwell

        # Test wildcard pattern - only valid JSON files will load successfully
        sessions_all = load_all_logs(log_dir, file_pattern="log*")
        assert len(sessions_all) == 2  # Only valid JSON files loaded (log3.txt fails)

    def test_load_all_logs_empty_directory(self, tmp_path):
        """Test behavior with empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        sessions = load_all_logs(empty_dir)
        assert sessions == {}

    def test_load_all_logs_nonexistent_directory(self, tmp_path):
        """Test error handling for non-existent directory."""
        non_existent = tmp_path / "does_not_exist"

        with pytest.raises(LogReadError) as exc_info:
            load_all_logs(non_existent)

        assert "Folder not found" in str(exc_info.value)
        assert str(non_existent) in str(exc_info.value)

    def test_load_all_logs_file_instead_of_directory(self, sample_log_file):
        """Test error handling when path is a file, not a directory."""
        with pytest.raises(LogReadError) as exc_info:
            load_all_logs(sample_log_file)

        assert "Path is not a directory" in str(exc_info.value)

    def test_load_all_logs_skip_errors_true(self, tmp_path, sample_log_data):
        """Test error handling with skip_errors=True."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create valid and invalid log files
        (log_dir / "valid.json").write_text(orjson.dumps(sample_log_data).decode())
        (log_dir / "invalid.json").write_text("invalid json content")
        (log_dir / "empty.json").write_text("")

        # Should skip errors and return only valid sessions
        sessions = load_all_logs(log_dir, skip_errors=True)

        assert len(sessions) == 1
        assert "valid.json" in sessions
        assert isinstance(sessions["valid.json"], LogSession)

    def test_load_all_logs_skip_errors_false(self, tmp_path, sample_log_data):
        """Test error handling with skip_errors=False."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create valid and invalid log files
        (log_dir / "valid.json").write_text(orjson.dumps(sample_log_data).decode())
        (log_dir / "invalid.json").write_text("invalid json content")

        # Should raise error on first invalid file
        with pytest.raises(LogReadError) as exc_info:
            load_all_logs(log_dir, skip_errors=False)

        assert "Failed to load log file" in str(exc_info.value)

    def test_load_all_logs_kwargs_passed_through(self, tmp_path, sample_log_data):
        """Test that kwargs are passed through to read_records."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        log_file = log_dir / "test.json"
        log_file.write_text(orjson.dumps(sample_log_data).decode())

        # Test encoding parameter is passed through
        sessions = load_all_logs(log_dir, encoding="utf-8")
        assert len(sessions) == 1
        assert "test.json" in sessions

    def test_load_all_logs_max_workers(self, log_directory):
        """Test max_workers parameter."""
        # Test with different max_workers values
        sessions_default = load_all_logs(log_directory)
        sessions_limited = load_all_logs(log_directory, max_workers=2)
        sessions_single = load_all_logs(log_directory, max_workers=1)

        # Results should be the same regardless of worker count
        assert (
            len(sessions_default) == len(sessions_limited) == len(sessions_single) == 3
        )
        assert (
            set(sessions_default.keys())
            == set(sessions_limited.keys())
            == set(sessions_single.keys())
        )

    def test_load_all_logs_metadata_preservation(self, log_directory):
        """Test that original metadata is preserved and new metadata is
        added."""
        sessions = load_all_logs(log_directory)

        for relative_path, session in sessions.items():
            # Should have original file_path metadata
            assert "file_path" in session.metadata

            # Should have new relative_path metadata
            assert session.metadata["relative_path"] == relative_path

            # file_path should be absolute, relative_path should be relative
            assert Path(session.metadata["file_path"]).is_absolute()
            assert not Path(relative_path).is_absolute()

    def test_load_all_logs_large_directory(self, tmp_path, sample_log_data):
        """Test performance with larger number of files."""
        log_dir = tmp_path / "many_logs"
        log_dir.mkdir()

        # Create 20 log files
        num_files = 20
        for i in range(num_files):
            log_file = log_dir / f"log_{i:02d}.json"
            # Modify data slightly to make each file unique
            data = sample_log_data.copy()
            for record in data["data"]:
                record["timestamp"] = record["timestamp"] + i
            log_file.write_text(orjson.dumps(data).decode())

        sessions = load_all_logs(log_dir)

        assert len(sessions) == num_files
        # Verify all files were loaded correctly
        for i in range(num_files):
            expected_path = f"log_{i:02d}.json"
            assert expected_path in sessions
            assert len(sessions[expected_path]) == 9  # Each has 9 records

    def test_load_all_logs_string_path(self, log_directory):
        """Test that string paths work as well as Path objects."""
        sessions_path = load_all_logs(log_directory)
        sessions_str = load_all_logs(str(log_directory))

        # Results should be identical
        assert sessions_path.keys() == sessions_str.keys()
        assert len(sessions_path) == len(sessions_str)
