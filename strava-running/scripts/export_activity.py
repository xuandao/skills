#!/usr/bin/env python3
"""
Export Strava activity data to JSON for analysis.
Run this and send the output JSON file for analysis.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_strava_run import read_config, authenticate_strava


def export_activity_data(client, activity_id, output_file):
    """Export all activity data to JSON"""

    print(f"Fetching activity {activity_id}...")

    # Get detailed activity
    activity = client.get_activity(activity_id)

    # Get streams
    print("Fetching streams...")
    try:
        streams = client.get_activity_streams(
            activity_id,
            types=['time', 'latlng', 'altitude', 'heartrate', 'distance', 'cadence', 'watts', 'temp', 'velocity_smooth']
        )
    except Exception as e:
        print(f"Warning: Could not get streams: {e}")
        streams = {}

    # Get laps
    print("Fetching laps...")
    try:
        laps = list(client.get_activity_laps(activity_id))
    except Exception as e:
        print(f"Warning: Could not get laps: {e}")
        laps = []

    # Build full data structure
    data = {
        'activity_id': activity_id,
        'export_time': str(datetime.now()),
        'activity': {
            'id': activity.id,
            'name': activity.name,
            'type': activity.type,
            'distance': float(activity.distance) if activity.distance else None,
            'moving_time_seconds': activity.moving_time.total_seconds() if activity.moving_time else None,
            'elapsed_time_seconds': activity.elapsed_time.total_seconds() if activity.elapsed_time else None,
            'average_speed': float(activity.average_speed) if activity.average_speed else None,
            'max_speed': float(activity.max_speed) if activity.max_speed else None,
            'average_heartrate': activity.average_heartrate,
            'max_heartrate': activity.max_heartrate,
            'calories': activity.calories,
            'total_elevation_gain': float(activity.total_elevation_gain) if activity.total_elevation_gain else None,
            'average_cadence': activity.average_cadence,
            'average_watts': activity.average_watts,
            'max_watts': activity.max_watts,
            'kilojoules': activity.kilojoules,
            'has_heartrate': activity.has_heartrate,
            'suffer_score': activity.suffer_score,
            'start_date_local': str(activity.start_date_local) if activity.start_date_local else None,
            'timezone': activity.timezone,
            'device_name': activity.device_name,
            'gear_id': activity.gear_id,
            'location_city': activity.location_city,
            'description': activity.description,
            'commute': activity.commute,
            'private': activity.private,
        },
        'streams': {},
        'laps': [],
        'splits_metric': [],
        'splits_standard': [],
        'best_efforts': [],
    }

    # Add streams data
    if streams:
        for stream_type, stream_data in streams.items():
            if stream_data and hasattr(stream_data, 'data'):
                data['streams'][stream_type] = {
                    'length': len(stream_data.data),
                    'first_10': stream_data.data[:10],
                    'last_10': stream_data.data[-10:],
                    'sample': stream_data.data[::len(stream_data.data)//10][:10] if len(stream_data.data) > 100 else stream_data.data[:10],
                }

    # Add laps data
    for lap in laps:
        lap_data = {
            'lap_index': lap.lap_index,
            'split_index': lap.split_index if hasattr(lap, 'split_index') else None,
            'distance': float(lap.distance) if lap.distance else None,
            'moving_time_seconds': lap.moving_time.total_seconds() if lap.moving_time else None,
            'elapsed_time_seconds': lap.elapsed_time.total_seconds() if lap.elapsed_time else None,
            'average_speed': float(lap.average_speed) if lap.average_speed else None,
            'average_heartrate': lap.average_heartrate,
            'max_heartrate': lap.max_heartrate,
            'average_cadence': lap.average_cadence,
            'total_elevation_gain': float(lap.total_elevation_gain) if lap.total_elevation_gain else None,
        }
        data['laps'].append(lap_data)

    # Add splits
    if hasattr(activity, 'splits_metric') and activity.splits_metric:
        for split in activity.splits_metric:
            data['splits_metric'].append({
                'distance': float(split.distance) if hasattr(split, 'distance') else None,
                'elapsed_time': split.elapsed_time.total_seconds() if hasattr(split, 'elapsed_time') and split.elapsed_time else None,
                'elevation_difference': float(split.elevation_difference) if hasattr(split, 'elevation_difference') else None,
                'average_speed': float(split.average_speed) if hasattr(split, 'average_speed') else None,
            })

    if hasattr(activity, 'splits_standard') and activity.splits_standard:
        for split in activity.splits_standard:
            data['splits_standard'].append({
                'distance': float(split.distance) if hasattr(split, 'distance') else None,
                'elapsed_time': split.elapsed_time.total_seconds() if hasattr(split, 'elapsed_time') and split.elapsed_time else None,
            })

    # Add best efforts
    if hasattr(activity, 'best_efforts') and activity.best_efforts:
        for effort in activity.best_efforts:
            data['best_efforts'].append({
                'name': effort.name,
                'elapsed_time': effort.elapsed_time.total_seconds() if effort.elapsed_time else None,
                'distance': float(effort.distance) if effort.distance else None,
            })

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Data exported to: {output_file}")
    print(f"\nFile size: {os.path.getsize(output_file) / 1024:.1f} KB")

    return data


if __name__ == '__main__':
    from datetime import datetime

    if len(sys.argv) < 2:
        print("Usage: export_activity.py <activity_id> [output_file]")
        print("\nExamples:")
        print("  python3 export_activity.py 17848143875")
        print("  python3 export_activity.py 17848143875 treadmill_data.json")
        print("  python3 export_activity.py 17809829875 outdoor_data.json")
        sys.exit(1)

    activity_id = int(sys.argv[1])
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"activity_{activity_id}_data.json"

    print(f"Exporting Strava activity {activity_id}...\n")

    config = read_config()
    client = authenticate_strava(config)

    export_activity_data(client, activity_id, output_file)

    print("\n" + "="*60)
    print("Next steps:")
    print("1. Find the exported JSON file above")
    print("2. Send it to me for analysis")
    print("="*60)
