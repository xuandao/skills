#!/usr/bin/env python3
"""
Analyze specific Strava activities to understand data structure.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_strava_run import read_config, authenticate_strava, get_activity_streams, get_activity_laps


def analyze_activity(client, activity_id):
    """Fetch and analyze a specific activity"""

    print(f"\n{'='*60}")
    print(f"Analyzing Activity ID: {activity_id}")
    print('='*60)

    # Get detailed activity
    activity = client.get_activity(activity_id)

    print("\n📋 BASIC ACTIVITY INFO:")
    print(f"  Name: {activity.name}")
    print(f"  Type: {activity.type}")
    print(f"  Distance: {activity.distance} m ({activity.distance/1000:.2f} km)" if activity.distance else "  Distance: N/A")
    print(f"  Moving Time: {activity.moving_time}")
    print(f"  Elapsed Time: {activity.elapsed_time}")
    print(f"  Average Speed: {activity.average_speed} m/s" if activity.average_speed else "  Average Speed: N/A")
    print(f"  Max Speed: {activity.max_speed} m/s" if activity.max_speed else "  Max Speed: N/A")
    print(f"  Average HR: {activity.average_heartrate} bpm" if activity.average_heartrate else "  Average HR: N/A")
    print(f"  Max HR: {activity.max_heartrate} bpm" if activity.max_heartrate else "  Max HR: N/A")
    print(f"  Calories: {activity.calories}" if activity.calories else "  Calories: N/A")
    print(f"  Total Elevation Gain: {activity.total_elevation_gain} m" if activity.total_elevation_gain else "  Total Elevation Gain: N/A")
    print(f"  Average Cadence: {activity.average_cadence} spm" if activity.average_cadence else "  Average Cadence: N/A")
    print(f"  Average Watts: {activity.average_watts} W" if activity.average_watts else "  Average Watts: N/A")
    print(f"  Max Watts: {activity.max_watts} W" if activity.max_watts else "  Max Watts: N/A")
    print(f"  Kilojoules: {activity.kilojoules}" if activity.kilojoules else "  Kilojoules: N/A")
    print(f"  Has Heartrate: {activity.has_heartrate}")
    print(f"  Suffer Score: {activity.suffer_score}" if activity.suffer_score else "  Suffer Score: N/A")
    print(f"  Start Date (Local): {activity.start_date_local}")
    print(f"  Timezone: {activity.timezone}")
    print(f"  Location City: {activity.location_city}" if activity.location_city else "  Location City: N/A")

    # Device info
    print(f"\n📱 DEVICE INFO:")
    print(f"  Device Name: {activity.device_name}" if activity.device_name else "  Device Name: N/A")
    print(f"  Gear ID: {activity.gear_id}" if activity.gear_id else "  Gear ID: N/A")

    # Maps
    print(f"\n🗺️ MAP INFO:")
    if activity.map:
        print(f"  Map ID: {activity.map.id if hasattr(activity.map, 'id') else 'N/A'}")
        print(f"  Has Summary Polyline: {bool(activity.map.summary_polyline)}")
        print(f"  Summary Polyline (first 100 chars): {activity.map.summary_polyline[:100]}..." if activity.map.summary_polyline else "  Summary Polyline: None")
    else:
        print("  No map data")

    # Streams
    print(f"\n📊 STREAMS DATA:")
    streams = get_activity_streams(client, activity_id)

    if streams:
        for stream_type, stream_data in streams.items():
            if stream_data and hasattr(stream_data, 'data'):
                data_len = len(stream_data.data)
                print(f"  {stream_type}: {data_len} points")
                if data_len > 0:
                    # Show first and last few values
                    first_vals = stream_data.data[:3]
                    last_vals = stream_data.data[-3:]
                    print(f"    First 3: {first_vals}")
                    print(f"    Last 3: {last_vals}")
            else:
                print(f"  {stream_type}: No data")
    else:
        print("  No streams available")

    # Laps
    print(f"\n🔄 LAPS DATA:")
    laps = get_activity_laps(client, activity_id)

    if laps:
        print(f"  Total Laps: {len(laps)}")
        for i, lap in enumerate(laps[:5]):  # Show first 5 laps
            print(f"\n  Lap {lap.lap_index}:")
            print(f"    Distance: {lap.distance} m" if lap.distance else "    Distance: N/A")
            print(f"    Elapsed Time: {lap.elapsed_time}")
            print(f"    Moving Time: {lap.moving_time}" if lap.moving_time else "    Moving Time: N/A")
            print(f"    Average Speed: {lap.average_speed} m/s" if lap.average_speed else "    Average Speed: N/A")
            print(f"    Average HR: {lap.average_heartrate} bpm" if lap.average_heartrate else "    Average HR: N/A")
            print(f"    Max HR: {lap.max_heartrate} bpm" if lap.max_heartrate else "    Max HR: N/A")
            print(f"    Average Cadence: {lap.average_cadence}" if lap.average_cadence else "    Average Cadence: N/A")
            print(f"    Elevation Gain: {lap.total_elevation_gain} m" if lap.total_elevation_gain else "    Elevation Gain: N/A")
            if i >= 4 and len(laps) > 5:
                print(f"    ... and {len(laps) - 5} more laps")
                break
    else:
        print("  No laps data")

    # Segment Efforts
    print(f"\n🏃 SEGMENT EFFORTS:")
    if hasattr(activity, 'segment_efforts') and activity.segment_efforts:
        print(f"  Total Segments: {len(activity.segment_efforts)}")
        for seg in activity.segment_efforts[:3]:
            print(f"    - {seg.name}: {seg.elapsed_time}")
    else:
        print("  No segment efforts")

    # Best Efforts
    print(f"\n⭐ BEST EFFORTS:")
    if hasattr(activity, 'best_efforts') and activity.best_efforts:
        for effort in activity.best_efforts[:5]:
            print(f"  {effort.name}: {effort.elapsed_time}")
    else:
        print("  No best efforts data")

    # Splits
    print(f"\n📏 SPLITS METRIC:")
    if hasattr(activity, 'splits_metric') and activity.splits_metric:
        print(f"  Total Splits: {len(activity.splits_metric)}")
        for split in activity.splits_metric[:5]:
            print(f"    km {split.split}: {split.elapsed_time} @ {split.average_speed} m/s")
        if len(activity.splits_metric) > 5:
            print(f"    ... and {len(activity.splits_metric) - 5} more splits")
    else:
        print("  No metric splits")

    print(f"\n📏 SPLITS STANDARD:")
    if hasattr(activity, 'splits_standard') and activity.splits_standard:
        print(f"  Total Splits: {len(activity.splits_standard)}")
    else:
        print("  No standard splits")

    # Photos
    print(f"\n📸 PHOTOS:")
    if hasattr(activity, 'photos') and activity.photos:
        print(f"  Photos count: {activity.photos.count}" if hasattr(activity.photos, 'count') else "  Photos available")
    else:
        print("  No photos")

    # Return data for comparison
    return {
        'activity_id': activity_id,
        'name': activity.name,
        'type': activity.type,
        'distance': float(activity.distance) if activity.distance else 0,
        'moving_time': str(activity.moving_time),
        'average_speed': float(activity.average_speed) if activity.average_speed else 0,
        'has_streams': bool(streams),
        'stream_types': list(streams.keys()) if streams else [],
        'has_laps': bool(laps),
        'laps_count': len(laps) if laps else 0,
        'has_map': bool(activity.map and activity.map.summary_polyline),
    }


def main():
    config = read_config()
    client = authenticate_strava(config)

    # Activity IDs from user
    activities = [
        17848143875,  # 跑步机
        17809829875,  # 公路跑
    ]

    results = []
    for activity_id in activities:
        try:
            result = analyze_activity(client, activity_id)
            results.append(result)
        except Exception as e:
            print(f"❌ Error analyzing activity {activity_id}: {e}")
            import traceback
            traceback.print_exc()

    # Comparison summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    for r in results:
        print(f"\n{r['name']} (ID: {r['activity_id']}):")
        print(f"  Has GPS/Map: {r['has_map']}")
        print(f"  Has Streams: {r['has_streams']} ({', '.join(r['stream_types'])})")
        print(f"  Has Laps: {r['has_laps']} ({r['laps_count']} laps)")


if __name__ == '__main__':
    main()
