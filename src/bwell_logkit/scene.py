"""Scene management and segmentation for bWell log data."""

from collections import defaultdict
from typing import Literal, Optional

from .exceptions import SceneNotFoundError
from .types import LogRecord, RecordFields, RecordTypes, SceneInfo


class SceneManager:
    """Manages scene segmentation and provides access to scene instances."""

    def __init__(self, records: list[LogRecord]):
        self._records = records
        self._scenes = self._build_scene_index()

    def _build_scene_index(self) -> dict[str, list[SceneInfo]]:
        scene_entries = [
            r
            for r in self._records
            if r.get(RecordFields.RECORD_TYPE) == RecordTypes.SCENE_ENTRY
        ]

        if not scene_entries:
            return {}

        scenes: dict[str, list[SceneInfo]] = defaultdict(list)

        for i, entry in enumerate(scene_entries):
            scene_name = entry.get(RecordFields.SceneEntry.SCENE_NAME)

            if not scene_name:
                continue

            start_gt = entry.get(RecordFields.GAME_TIME_SECS, 0)
            start_epoch = entry.get(RecordFields.MILLIS_SINCE_EPOCH, 0)

            if i + 1 < len(scene_entries):
                end_gt = scene_entries[i + 1].get(RecordFields.GAME_TIME_SECS, start_gt)
                end_epoch = scene_entries[i + 1].get(
                    RecordFields.MILLIS_SINCE_EPOCH, start_epoch
                )
            else:
                # Find the last record's timestamp
                gt_timestamps = [
                    r.get(RecordFields.GAME_TIME_SECS, 0) for r in self._records
                ]
                epoch_timestamps = [
                    r.get(RecordFields.MILLIS_SINCE_EPOCH, 0) for r in self._records
                ]
                end_gt = max(gt_timestamps, default=start_gt)
                end_epoch = max(epoch_timestamps, default=start_epoch)

            end_gt = float(end_gt) if end_gt is not None else start_gt
            end_epoch = int(end_epoch) if end_epoch is not None else start_epoch

            instance_idx = len(scenes[scene_name])
            scenes[scene_name].append(
                SceneInfo(
                    name=scene_name,
                    instance=instance_idx,
                    start_game_time_secs=start_gt,
                    end_game_time_secs=end_gt,
                    start_millis_since_epoch=start_epoch,
                    end_millis_since_epoch=end_epoch,
                )
            )
        return dict(scenes)

    def list_scenes(self) -> list[str]:
        """List all available scene names."""
        return list(self._scenes.keys())

    def has_scene(self, scene_name: str, instance: int = 0) -> bool:
        """Check if a scene instance exists."""
        return scene_name in self._scenes and instance < len(self._scenes[scene_name])

    def get_scene_count(self, scene_name: str) -> int:
        """Get the number of instances for a scene."""
        return len(self._scenes.get(scene_name, []))

    def get_scene_info(self, scene_name: str, instance: int = 0) -> SceneInfo:
        """Get information about a specific scene instance."""
        if not self.has_scene(scene_name, instance):
            raise SceneNotFoundError(scene_name, instance, self.list_scenes())
        return self._scenes[scene_name][instance]

    def get_scene_records(self, scene_name: str, instance: int = 0) -> list[LogRecord]:
        """Get all records within a specific scene instance."""
        info = self.get_scene_info(scene_name, instance)
        return [
            r
            for r in self._records
            if info.start_game_time_secs
            <= r.get(RecordFields.GAME_TIME_SECS, 0)
            <= info.end_game_time_secs
        ]

    def get_scene_instances(
        self,
        scene_name: Optional[str] = None,
        sort_by: Optional[Literal["game_time", "epoch"]] = None,
    ) -> list[SceneInfo]:
        """
        Get information about scene instances.

        Args:
            scene_name:
                If provided, return only instances of that specific scene.
                If None, return instances of *all* scenes.
            sort_by:
                If 'game_time', sort ascending by start_game_time_secs.
                If 'epoch',     sort ascending by start_millis_since_epoch.
                If None,        preserve insertion order, grouped by scene.

        Raises:
            SceneNotFoundError: if scene_name is provided but not found.
        """

        if scene_name is not None:
            if scene_name not in self._scenes:
                raise SceneNotFoundError(scene_name, 0, self.list_scenes())
            instances = list(self._scenes[scene_name])
        else:
            instances = []
            for inst_list in self._scenes.values():
                instances.extend(inst_list)

        if sort_by == "epoch":
            instances.sort(key=lambda s: s.start_millis_since_epoch)
        elif sort_by == "game_time":
            instances.sort(key=lambda s: s.start_game_time_secs)

        return instances

    def get_scene_summary(self) -> dict[str, dict]:
        """Get a summary of all scenes and their instances."""
        summary = {}
        for name, instances in self._scenes.items():
            total_duration = sum(i.duration_secs for i in instances)
            summary[name] = {
                "instance_count": len(instances),
                "total_duration_secs": total_duration,
                "average_duration_secs": (
                    total_duration / len(instances) if instances else 0
                ),
                "instances": [
                    {
                        "instance": i.instance,
                        "start_game_time_secs": i.start_game_time_secs,
                        "end_game_time_secs": i.end_game_time_secs,
                        "duration_secs": i.duration_secs,
                        "start_millis_since_epoch": i.start_millis_since_epoch,
                        "end_millis_since_epoch": i.end_millis_since_epoch,
                    }
                    for i in instances
                ],
            }
        return summary
