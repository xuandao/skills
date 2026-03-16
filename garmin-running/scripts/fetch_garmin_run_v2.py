#!/usr/bin/env python3
"""
Fetch latest running activity from Garmin Connect using garth library.
"""

import os
import sys
import json
from datetime import datetime

try:
    from garth import Client
except ImportError:
    print("❌ Please install garth: pip3 install garth", file=sys.stderr)
    sys.exit(1)

def login_garmin(email, password):
    """Login to Garmin Connect using garth"""
    try:
        client = Client()
        client.login(email, password)
        return client
    except Exception as e:
        print(f"❌ Login failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def get_latest_run(client):
    """Get the latest running activity"""
    try:
        # Get recent activities
        activities = client.connectapi(
            "/activitylist-service/activities/search/activities",
            params={"limit": 10}
        )
        
        if not activities:
            print("❌ No activities found", file=sys.stderr)
            sys.exit(1)
        
        # Filter for running activities
        running_types = ['running', 'treadmill_running', 'trail_running', 'indoor_running']
        running_activities = [
            act for act in activities 
            if act.get('activityType', {}).get('typeKey', '').lower() in running_types
        ]
        
        if not running_activities:
            print("❌ No running activities found", file=sys.stderr)
            sys.exit(1)
        
        return running_activities[0]
    except Exception as e:
        print(f"❌ Failed to fetch activities: {e}", file=sys.stderr)
        sys.exit(1)

def download_gpx(client, activity_id, output_dir):
    """Download GPX file for the activity"""
    try:
        # Download GPX
        gpx_data = client.download(activity_id, file_type="gpx")
        
        # Save GPX file
        gpx_path = os.path.join(output_dir, f"{activity_id}.gpx")
        with open(gpx_path, 'wb') as f:
            f.write(gpx_data)
        
        return gpx_path
    except Exception as e:
        print(f"⚠️ Failed to download GPX: {e}", file=sys.stderr)
        return None

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def format_pace(meters_per_second):
    """Format pace from m/s to min/km"""
    if not meters_per_second or meters_per_second == 0:
        return "N/A"
    
    seconds_per_km = 1000 / meters_per_second
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"

def analyze_activity(activity, gpx_path=None):
    """Analyze the activity and return formatted data"""
    # Extract key metrics
    distance_m = activity.get('distance', 0)
    distance_km = distance_m / 1000 if distance_m else 0
    duration_sec = activity.get('duration', 0)
    avg_hr = activity.get('averageHR')
    max_hr = activity.get('maxHR')
    avg_speed = activity.get('averageSpeed')  # m/s
    calories = activity.get('calories')
    elevation_gain = activity.get('elevationGain')
    avg_cadence = activity.get('averageRunningCadenceInStepsPerMinute')
    
    # Activity metadata
    activity_name = activity.get('activityName', 'Running')
    start_time = activity.get('startTimeLocal')
    activity_type = activity.get('activityType', {}).get('typeKey', 'running')
    
    # Parse start time
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%H:%M')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
            time_str = "N/A"
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
        time_str = "N/A"
    
    result = {
        'activity_id': activity.get('activityId'),
        'activity_name': activity_name,
        'activity_type': activity_type,
        'date': date_str,
        'time': time_str,
        'distance_km': round(distance_km, 2),
        'duration': format_duration(duration_sec),
        'duration_seconds': duration_sec,
        'avg_pace': format_pace(avg_speed) if avg_speed else "N/A",
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'calories': calories,
        'elevation_gain': elevation_gain,
        'avg_cadence': avg_cadence,
        'gpx_path': gpx_path
    }
    
    return result

def main():
    if len(sys.argv) < 4:
        print("Usage: fetch_garmin_run_v2.py <email> <password> <output_dir>", file=sys.stderr)
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    output_dir = sys.argv[3]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print("🔐 Logging in to Garmin Connect...")
    client = login_garmin(email, password)
    
    print("📥 Fetching latest running activity...")
    activity = get_latest_run(client)
    
    activity_id = activity.get('activityId')
    print(f"✅ Found activity: {activity.get('activityName')} (ID: {activity_id})")
    
    print("📍 Downloading GPX file...")
    gpx_path = download_gpx(client, activity_id, output_dir)
    
    print("📊 Analyzing activity...")
    result = analyze_activity(activity, gpx_path)
    
    # Output JSON result
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
