#!/usr/bin/env python3
"""
Basic usage example for bwell-logkit.

This example demonstrates the core functionality:
- Loading a bWell log file
- Basic filtering operations
- Data export to different formats
"""

from pathlib import Path

from bwell_logkit import load_all_logs, load_log
from bwell_logkit.types import MovementSources, RecordTypes


def main():
    # Replace with your actual log file path
    log_file = Path("path/to/sample_log.json")

    # Check if file exists (you'll need to provide your own log file)
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        print("Please provide a valid bWell log file to run this example.")
        return

    print("=== Basic bwell-logkit Usage Example ===\n")

    # 1. Load the log file
    print("1a. Loading log file...")
    session = load_log(log_file)
    print(f"   Loaded {len(session)} records")

    # Alternatively, load all logs from a directory recursively and in parallel
    print("1b. Loading all logs from a directory...")
    sessions = load_all_logs(
        "path/to",
        file_pattern="*.json",  # Custom file pattern
        max_workers=4,  # Limit parallel workers
        skip_errors=False,  # Skip files that fail to load
    )

    for relative_path, session in sessions.items():
        print(f"   {relative_path}: {len(session)} records")

    # 2. Get basic statistics
    print("\n2. Session statistics:")
    stats = session.get_stats()
    print(f"   Record types: {list(stats['record_types'].keys())}")
    if stats["game_time_range"]:
        start, end = stats["game_time_range"]
        print(
            f"   Game time range: {start:.2f} - {end:.2f} seconds ("
            f"{end - start:.2f}s total)"
        )

    # 3. Filter by record type
    print("\n3. Filtering by record type...")
    movement_session = session.filter_type(RecordTypes.ABSOLUTE_ACTIVITY.value)
    print(f"   Movement records: {len(movement_session)}")

    settings_session = session.filter_type(RecordTypes.GAME_SETTINGS.value)
    print(f"   Game settings records: {len(settings_session)}")

    # 4. Filter by custom filter
    print("\n4. Filtering by custom filter (head senderTag)...")
    head_movement = movement_session.filter(
        lambda r: r.get("senderTag") == MovementSources.HEAD.value
    )
    print(f"   Head tracking records: {len(head_movement)}")

    # 5. Time-based filtering
    print("\n5. Time-based filtering...")
    if len(session) > 0:
        # Filter first 30 seconds
        early_session = session.filter_time_range(0, 30)
        print(f"   First 30 seconds: {len(early_session)} records")

        # Filter a middle portion
        mid_session = session.filter_time_range(30, 60)
        print(f"   30-60 seconds: {len(mid_session)} records")

    # 6. Scene analysis
    print("\n6. Scene analysis...")
    scenes = session.list_scenes()
    print(f"   Available scenes: {scenes}")

    if scenes:
        # Get scene summary
        scene_summary = session.scene_manager.get_scene_summary()
        for scene_name, info in scene_summary.items():
            print(
                f"   {scene_name}: {info['instance_count']} instance(s), "
                f"total duration: {info['total_duration_secs']:.2f}s"
            )

    # 7. Export data
    print("\n7. Exporting data...")

    # Export to pandas DataFrame
    print("   Converting to pandas DataFrame...")
    df = session.to_pandas()
    print(f"   DataFrame shape: {df.shape}")
    if len(df) > 0:
        print(f"   Columns: {list(df.columns)}")

    # Export to CSV (uncomment to create files)
    # print("   Exporting to CSV...")
    # session.export_csv("full_session.csv")
    # if len(movement_session) > 0:
    #     movement_session.export_csv("movement_data.csv")

    # 8. Chained filtering example
    print("\n8. Chained filtering example...")
    complex_filter = (
        session.filter_type(RecordTypes.ABSOLUTE_ACTIVITY.value)
        .filter_time_range(10, 120)  # 10-120 seconds
        .filter(lambda r: r.get("senderTag") == MovementSources.HEAD.value)
    )
    print(f"   Head movement in 10-120s range: {len(complex_filter)} records")

    # 9. View all scene instances in chronological order
    print("\n9. Viewing all scene instances in chronological order...")
    scene_instances = session.scene_manager.get_all_scene_instances_chron()
    for scene_instance in scene_instances:
        name = scene_instance.name
        index = scene_instance.instance
        print(f"   {name}: {index}")

    # 10. Adding participant information to metadata
    print("\n10. Adding participant information to metadata...")
    session.set_metadata("participant_id", "P001")
    session.set_metadata("participant_age", 25)
    session.set_metadata("study_condition", "control")

    # Or update multiple metadata fields at once
    participant_info = {
        "participant_id": "P001",
        "participant_age": 25,
        "study_condition": "control",
        "session_date": "2024-01-15",
        "researcher": "Dr. Smith",
    }
    session.update_metadata(participant_info)

    # Access the metadata
    print("Session metadata:", session.metadata)

    # Metadata is preserved when filtering
    filtered_session = session.filter_type(RecordTypes.ABSOLUTE_ACTIVITY.value)
    print("Filtered session still has metadata:", filtered_session.metadata)

    # Scene views also inherit and can modify metadata
    if session.list_scenes():
        scene = session.scene(session.list_scenes()[0])
        scene.set_metadata("scene_notes", "Participant seemed engaged")
        print("Scene metadata:", scene.metadata)

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()
