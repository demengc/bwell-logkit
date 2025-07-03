"""
Tests for the reader module.
"""

import json

import pytest

from bwell_logkit.exceptions import LogReadError
from bwell_logkit.logs import LogSession
from bwell_logkit.reader import _heal_json, load_log, read_records


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

        result = json.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_missing_closing_bracket_only(self):
        """Test healing bWell log with missing } only."""
        malformed = '{"data": [{"test": "value"}]'
        healed = _heal_json(malformed)

        result = json.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_already_valid(self):
        """Test healing already valid JSON doesn't break it."""
        valid = '{"data": [{"test": "value"}]}'
        healed = _heal_json(valid)

        result = json.loads(healed)
        assert result["data"][0]["test"] == "value"

    def test_heal_json_strip_whitespace(self):
        """Test that healing strips whitespace."""
        malformed = '  {"data": [{"test": "value"}]  '
        healed = _heal_json(malformed)

        result = json.loads(healed)
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
