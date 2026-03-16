#!/usr/bin/env python3
"""
Fetch latest running activity from Garmin Connect using garth library.
Reads credentials from config file.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    from garth import Client
except ImportError:
    print("❌ Please install garth: pip3 install garth", file=sys.stderr)
    sys.exit(1)

def read_config():
    """Read Garmin credentials from config file"""
    # Try to find config in skill directory
    script_dir = Path(__file__).parent.parent
    config_file = script_dir / "references" / "garmin_config.json"
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}", file=sys.stderr)
        print("Create a file with: {\"email\": \"your@email.com\", \"password\": \"yourpassword\"}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config.get('email'), config.get('password')

def login_garmin(email, password):
    """Login to Garmin Connect using garth"""
    try:
        client = Client()
        client.login(email, password)
        return client
    except Exception as e:
        print(f"❌ Login failed: {e}", file=sys.stderr)
        sys.exit(1)

def get_latest_run(client):
    """Get the latest running activity with splits data"""
    try:
        # Get recent activities
        activities = client.connectapi(
            "/activitylist-service/activities/search/activities",
            params={"limit": 20}
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
        
        activity = running_activities[0]
        activity_id = activity.get('activityId')
        
        # Get splits data
        try:
            splits_data = client.connectapi(f"/activity-service/activity/{activity_id}/splits")
            activity['splits'] = splits_data.get('lapDTOs', [])
        except Exception as e:
            print(f"⚠️ Failed to fetch splits data: {e}", file=sys.stderr)
            activity['splits'] = []
        
        return activity
    except Exception as e:
        print(f"❌ Failed to fetch activities: {e}", file=sys.stderr)
        sys.exit(1)

def download_gpx(client, activity_id, output_dir):
    """Download GPX file for the activity"""
    try:
        # Download GPX using garth's download method
        gpx_data = client.download(int(activity_id))
        
        # Save GPX file
        gpx_path = os.path.join(str(output_dir), f"{activity_id}.gpx")
        with open(gpx_path, 'wb') as f:
            f.write(gpx_data)
        
        return gpx_path
    except Exception as e:
        print(f"⚠️ Failed to download GPX: {e}", file=sys.stderr)
        return None

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    if not seconds:
        return "N/A"
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
            # Handle different datetime formats
            if 'T' in start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%H:%M')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
            time_str = "N/A"
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
        time_str = "N/A"
    
    # Process splits data
    splits = []
    interval_counter = {}  # 用于计数每种类型的间歇
    
    for lap in activity.get('splits', []):
        split_distance = lap.get('distance', 0) / 1000  # meters to km
        split_duration = lap.get('duration', 0)
        split_speed = lap.get('averageSpeed', 0)
        split_hr = lap.get('averageHR')
        split_cadence = lap.get('averageRunCadence')
        split_stride = lap.get('strideLength')  # cm
        split_vertical_osc = lap.get('verticalOscillation')  # cm
        split_vertical_ratio = lap.get('verticalRatio')  # %
        split_ground_contact = lap.get('groundContactTime')  # ms
        split_power = lap.get('averagePower')  # watts
        
        # 获取训练阶段类型
        intensity_type = lap.get('intensityType', '')
        step_type_map = {
            'WARMUP': '热身',
            'INTERVAL': '跑步',
            'ACTIVE': '跑步',
            'RECOVERY': '休息',
            'REST': '休息',
            'COOLDOWN': '缓和'
        }
        step_type = step_type_map.get(intensity_type, '')
        
        # 为间歇跑分配编号
        interval = ''
        if step_type == '跑步':
            if intensity_type not in interval_counter:
                interval_counter[intensity_type] = 0
            # 每两圈算一组间歇
            interval_counter[intensity_type] += 1
            interval = str((interval_counter[intensity_type] + 1) // 2)
        
        splits.append({
            'lap_number': lap.get('lapIndex', 0),
            'interval': interval,
            'step_type': step_type,
            'distance_km': round(split_distance, 2),
            'duration': format_duration(split_duration),
            'duration_seconds': split_duration,
            'pace': format_pace(split_speed),
            'avg_hr': split_hr,
            'avg_cadence': round(split_cadence, 1) if split_cadence else None,
            'stride_length': round(split_stride / 100, 2) if split_stride else None,  # convert cm to m
            'vertical_oscillation': round(split_vertical_osc, 1) if split_vertical_osc else None,  # cm
            'vertical_ratio': round(split_vertical_ratio, 1) if split_vertical_ratio else None,  # %
            'ground_contact_time': round(split_ground_contact, 1) if split_ground_contact else None,  # ms
            'avg_power': round(split_power) if split_power else None  # watts
        })
    
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
        'avg_hr': avg_hr if avg_hr else "N/A",
        'max_hr': max_hr if max_hr else "N/A",
        'calories': calories if calories else "N/A",
        'elevation_gain': elevation_gain if elevation_gain else "N/A",
        'avg_cadence': avg_cadence if avg_cadence else "N/A",
        'gpx_path': gpx_path,
        'splits': splits
    }
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_garmin_run_v3.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print("📖 Reading config...")
    email, password = read_config()
    
    print("🔐 Logging in to Garmin Connect...")
    client = login_garmin(email, password)
    
    print("📥 Fetching latest running activity...")
    activity = get_latest_run(client)
    
    activity_id = activity.get('activityId')
    print(f"✅ Found activity: {activity.get('activityName')} (ID: {activity_id})")
    
    print("📍 Downloading GPX file...")
    gpx_path = download_gpx(client, activity_id, output_dir)
    if gpx_path:
        print(f"✅ GPX saved: {gpx_path}")
    
    print("📊 Analyzing activity...")
    result = analyze_activity(activity, gpx_path)
    
    # Output JSON result
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
