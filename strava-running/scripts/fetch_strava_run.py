#!/usr/bin/env python3
"""
Fetch latest running activity from Strava using stravalib.
Reads credentials from config file and generates GPX from streams.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from stravalib.client import Client
    import gpxpy
    import gpxpy.gpx
except ImportError:
    print("❌ Please install required packages: pip3 install stravalib gpxpy", file=sys.stderr)
    sys.exit(1)


def parse_quantity(value):
    """Parse a value that may be a pint Quantity object or a plain number.

    stravalib returns pint Quantity objects for many fields (distance, speed, etc.)
    when the units library is available. This function safely extracts the
    magnitude (numerical value) regardless of the input type.

    Args:
        value: A pint Quantity, a number, or None

    Returns:
        float: The numerical value, or 0.0 if value is None
    """
    if value is None:
        return 0.0
    if hasattr(value, 'magnitude'):
        return float(value.magnitude)
    return float(value)


def read_config():
    """Read Strava credentials from config file"""
    script_dir = Path(__file__).parent.parent
    config_file = script_dir / "references" / "strava_config.json"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}", file=sys.stderr)
        print('Create a file with: {"client_id": "...", "client_secret": "...", "refresh_token": "..."}', file=sys.stderr)
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    return config


def authenticate_strava(config):
    """Authenticate with Strava using refresh token"""
    client = Client()

    try:
        refresh_response = client.refresh_access_token(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            refresh_token=config['refresh_token'],
        )

        # Update tokens
        client.access_token = refresh_response['access_token']
        new_refresh_token = refresh_response['refresh_token']

        # Optionally update config if refresh_token changed
        if new_refresh_token != config['refresh_token']:
            print(f"⚠️  Refresh token has changed. Please update your config.", file=sys.stderr)

        return client
    except Exception as e:
        print(f"❌ Strava authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


def get_latest_run(client):
    """Get the latest running activity"""
    try:
        # Get recent activities (limit 10)
        activities = list(client.get_activities(limit=10))

        if not activities:
            print("❌ No activities found", file=sys.stderr)
            sys.exit(1)

        # Filter for running activities
        running_activities = [act for act in activities if act.type == 'Run']

        if not running_activities:
            print("❌ No running activities found", file=sys.stderr)
            sys.exit(1)

        # Get the latest running activity
        latest_activity = running_activities[0]

        # Get full activity details
        detailed_activity = client.get_activity(latest_activity.id)

        return detailed_activity

    except Exception as e:
        print(f"❌ Failed to fetch activities: {e}", file=sys.stderr)
        sys.exit(1)


def get_activity_streams(client, activity_id):
    """Get activity streams for GPX generation"""
    try:
        streams = client.get_activity_streams(
            activity_id,
            types=['time', 'latlng', 'altitude', 'heartrate', 'distance', 'cadence']
        )
        return streams
    except Exception as e:
        print(f"⚠️ Failed to get activity streams: {e}", file=sys.stderr)
        return {}


def generate_gpx(activity, streams, output_dir):
    """Generate GPX file from Strava streams"""

    # Check if we have required streams
    if not streams.get('time') or not streams.get('latlng'):
        print("⚠️ No GPS data available (treadmill run?), skipping GPX generation")
        return None

    try:
        time_list = streams['time'].data
        latlng_list = streams['latlng'].data

        # Activity start time
        start_time = activity.start_date_local

        # Create GPX
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = activity.name
        gpx_track.type = "Run"
        gpx.tracks.append(gpx_track)

        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        # Optional streams
        altitude_list = streams.get('altitude').data if streams.get('altitude') else None
        heartrate_list = streams.get('heartrate').data if streams.get('heartrate') else None

        # Add track points
        for i, latlng in enumerate(latlng_list):
            point_time = start_time + timedelta(seconds=time_list[i])

            point_kwargs = {
                'latitude': latlng[0],
                'longitude': latlng[1],
                'time': point_time,
            }

            if altitude_list and i < len(altitude_list):
                point_kwargs['elevation'] = altitude_list[i]

            point = gpxpy.gpx.GPXTrackPoint(**point_kwargs)

            # Add heart rate extension if available
            if heartrate_list and i < len(heartrate_list):
                hr = heartrate_list[i]
                # Create GPX extension for heart rate
                from xml.etree import ElementTree
                gpx_extension_hr = ElementTree.fromstring(
                    f'''<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                    <gpxtpx:hr>{hr}</gpxtpx:hr>
                    </gpxtpx:TrackPointExtension>
                    '''
                )
                point.extensions.append(gpx_extension_hr)

            gpx_segment.points.append(point)

        # Save GPX file
        gpx_path = os.path.join(output_dir, f"{activity.id}.gpx")
        with open(gpx_path, 'w') as f:
            f.write(gpx.to_xml())

        return gpx_path

    except Exception as e:
        print(f"⚠️ Failed to generate GPX: {e}", file=sys.stderr)
        return None


def format_duration(duration):
    """Format duration to HH:MM:SS"""
    if not duration:
        return "N/A"

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def format_pace(meters_per_second):
    """Format pace from m/s to min/km"""
    if not meters_per_second or meters_per_second <= 0:
        return "N/A"

    seconds_per_km = 1000 / meters_per_second
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def get_activity_laps(client, activity_id):
    """Get activity laps (splits)"""
    try:
        laps = list(client.get_activity_laps(activity_id))
        return laps
    except Exception as e:
        print(f"⚠️ Failed to get activity laps: {e}", file=sys.stderr)
        return []


def analyze_activity(activity, streams, laps, gpx_path=None):
    """Analyze the activity and return formatted data"""

    # Basic metrics
    distance_km = parse_quantity(activity.distance) / 1000 if activity.distance else 0
    duration_str = format_duration(activity.moving_time)
    duration_seconds = activity.moving_time.total_seconds() if activity.moving_time else 0

    avg_speed = parse_quantity(activity.average_speed)  # m/s
    avg_pace = format_pace(avg_speed)

    avg_hr = activity.average_heartrate
    max_hr = activity.max_heartrate
    calories = activity.calories
    elevation_gain = parse_quantity(activity.total_elevation_gain)
    avg_cadence = parse_quantity(activity.average_cadence)

    # Date and time
    start_time_local = activity.start_date_local
    date_str = start_time_local.strftime('%Y-%m-%d')
    time_str = start_time_local.strftime('%H:%M')

    # Process laps (splits)
    splits = []
    for lap in laps:
        lap_distance = parse_quantity(lap.distance) / 1000 if lap.distance else 0  # km
        lap_duration = lap.elapsed_time.total_seconds() if lap.elapsed_time else 0
        lap_speed = parse_quantity(lap.average_speed)
        lap_elevation = parse_quantity(lap.total_elevation_gain)

        splits.append({
            'lap_number': lap.lap_index,
            'distance_km': round(lap_distance, 2),
            'duration': format_duration(lap.elapsed_time),
            'duration_seconds': lap_duration,
            'pace': format_pace(lap_speed),
            'avg_hr': int(lap.average_heartrate) if lap.average_heartrate else None,
            'max_hr': int(lap.max_heartrate) if lap.max_heartrate else None,
            'elevation_gain': round(lap_elevation, 1) if lap_elevation else None,
        })

    # If no laps but streams available, create splits from streams
    if not splits and streams.get('distance'):
        print("⚠️ No laps found, using stream data", file=sys.stderr)
        # Could implement kilometer-based splits here

    result = {
        'activity_id': activity.id,
        'activity_name': activity.name,
        'activity_type': 'running',
        'date': date_str,
        'time': time_str,
        'distance_km': round(distance_km, 2),
        'duration': duration_str,
        'duration_seconds': duration_seconds,
        'avg_pace': avg_pace,
        'avg_hr': round(avg_hr, 1) if avg_hr else "N/A",
        'max_hr': int(max_hr) if max_hr else "N/A",
        'calories': int(calories) if calories else "N/A",
        'elevation_gain': round(elevation_gain, 1) if elevation_gain else "N/A",
        'avg_cadence': round(avg_cadence, 1) if avg_cadence else "N/A",
        'gpx_path': gpx_path,
        'splits': splits,
        # Additional Strava-specific data
        'strava_data': {
            'total_elevation_gain': round(parse_quantity(activity.total_elevation_gain), 1) if activity.total_elevation_gain else None,
            'average_speed': round(parse_quantity(activity.average_speed), 2) if activity.average_speed else None,
            'max_speed': round(parse_quantity(activity.max_speed), 2) if activity.max_speed else None,
            'average_watts': round(parse_quantity(activity.average_watts), 1) if activity.average_watts else None,
            'kilojoules': round(parse_quantity(activity.kilojoules), 1) if activity.kilojoules else None,
            'has_heartrate': activity.has_heartrate,
            'suffer_score': activity.suffer_score,
            'streams_available': list(streams.keys()) if streams else [],
        }
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_strava_run.py <output_dir>", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    os.makedirs(output_dir, exist_ok=True)

    print("📖 Reading config...", file=sys.stderr)
    config = read_config()

    print("🔐 Authenticating with Strava...", file=sys.stderr)
    client = authenticate_strava(config)
    print("✅ Authentication successful", file=sys.stderr)

    print("📥 Fetching latest running activity...", file=sys.stderr)
    activity = get_latest_run(client)
    print(f"✅ Found activity: {activity.name} (ID: {activity.id})", file=sys.stderr)

    print("📊 Fetching activity streams...", file=sys.stderr)
    streams = get_activity_streams(client, activity.id)

    print("📍 Generating GPX file...", file=sys.stderr)
    gpx_path = generate_gpx(activity, streams, output_dir)
    if gpx_path:
        print(f"✅ GPX saved: {gpx_path}", file=sys.stderr)

    print("📈 Fetching activity laps...", file=sys.stderr)
    laps = get_activity_laps(client, activity.id)
    print(f"✅ Found {len(laps)} laps", file=sys.stderr)

    print("📊 Analyzing activity...", file=sys.stderr)
    result = analyze_activity(activity, streams, laps, gpx_path)

    # Output JSON result to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
