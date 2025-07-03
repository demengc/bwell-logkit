"""
Custom exceptions for bwell-logkit.
"""


class BwellLogKitError(Exception):
    """Base exception for all bwell-logkit errors."""

    pass


class LogReadError(BwellLogKitError):
    """Raised when log file cannot be read or parsed."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error


class SceneNotFoundError(BwellLogKitError):
    """Raised when requested scene is not found in the log data."""

    def __init__(
        self,
        scene_name: str,
        instance: int = 0,
        available_scenes: list[str] | None = None,
    ):
        self.scene_name = scene_name
        self.instance = instance
        self.available_scenes = available_scenes or []

        message = f"Scene '{scene_name}' (instance {instance}) not found"
        if self.available_scenes:
            message += f". Available scenes: " f"{', '.join(self.available_scenes)}"
        super().__init__(message)


class ExtractionError(BwellLogKitError):
    """Raised when data extraction to DataFrame fails."""

    def __init__(self, message: str, extractor_type: str | None = None):
        super().__init__(message)
        self.extractor_type = extractor_type
