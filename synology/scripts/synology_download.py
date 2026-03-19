import os
import json
import requests
import argparse
import sys
import time

# Suppress insecure request warnings if using verify=False
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def login(nas_url, username, password):
    auth_url = f"{nas_url.rstrip('/')}/webapi/auth.cgi"
    params = {
        "api": "SYNO.API.Auth",
        "version": "2",
        "method": "login",
        "account": username,
        "passwd": password,
        "session": "DownloadStation",
        "format": "sid"
    }
    response = requests.get(auth_url, params=params, verify=False)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        raise Exception(f"Login failed (Error code: {error_code})")
    return data["data"]["sid"]

def create_task(nas_url, sid, uri_or_file):
    task_url = f"{nas_url.rstrip('/')}/webapi/DownloadStation/task.cgi"
    
    if os.path.isfile(uri_or_file) and uri_or_file.endswith('.torrent'):
        files = {'file': open(uri_or_file, 'rb')}
        payload = {
            "api": "SYNO.DownloadStation.Task",
            "version": "1",
            "method": "create",
            "_sid": sid
        }
        response = requests.post(task_url, data=payload, files=files, verify=False)
    else:
        params = {
            "api": "SYNO.DownloadStation.Task",
            "version": "1",
            "method": "create",
            "uri": uri_or_file,
            "_sid": sid
        }
        response = requests.get(task_url, params=params, verify=False)
    
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        raise Exception(f"Task creation failed (Error code: {error_code})")
    return True

def list_tasks(nas_url, sid, filter_type="all"):
    task_url = f"{nas_url.rstrip('/')}/webapi/DownloadStation/task.cgi"
    params = {
        "api": "SYNO.DownloadStation.Task",
        "version": "1",
        "method": "list",
        "additional": "detail,transfer",
        "filter": filter_type,
        "_sid": sid
    }
    response = requests.get(task_url, params=params, verify=False, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        raise Exception(f"List tasks failed (Error code: {error_code})")
    return data["data"]["tasks"]

def get_storage_info(nas_url, sid):
    storage_url = f"{nas_url.rstrip('/')}/webapi/entry.cgi"
    params = {
        "api": "SYNO.Storage.CGI.Storage",
        "version": "1",
        "method": "load_info",
        "_sid": sid
    }
    response = requests.get(storage_url, params=params, verify=False, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        params["api"] = "SYNO.Core.Storage.Volume"
        params["method"] = "list"
        response = requests.get(storage_url, params=params, verify=False, timeout=10)
        data = response.json()
        if not data.get("success"):
            error_code = data.get("error", {}).get("code", "Unknown")
            raise Exception(f"Storage info failed (Error code: {error_code})")
        return data["data"]["volumes"]
    return data["data"]["volumes"]

def get_download_info(nas_url, sid):
    info_url = f"{nas_url.rstrip('/')}/webapi/DownloadStation/info.cgi"
    params = {
        "api": "SYNO.DownloadStation.Info",
        "version": "1",
        "method": "getinfo",
        "_sid": sid
    }
    response = requests.get(info_url, params=params, verify=False, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        raise Exception(f"Download info failed (Error code: {error_code})")
    return data["data"]

def file_list(nas_url, sid, folder_path):
    url = f"{nas_url.rstrip('/')}/webapi/entry.cgi"
    method = "list"
    api = "SYNO.FileStation.List"
    if folder_path == "/":
        method = "list_share"
    
    params = {
        "api": api,
        "version": "2",
        "method": method,
        "_sid": sid
    }
    if method == "list":
        params["folder_path"] = folder_path
        params["additional"] = json.dumps(["size", "time"])
        
    response = requests.get(url, params=params, verify=False)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        raise Exception(f"File list failed (Error code: {error_code})")
    return data["data"]["files"] if "files" in data["data"] else data["data"]["shares"]

def file_delete(nas_url, sid, paths, recursive=True):
    url = f"{nas_url.rstrip('/')}/webapi/entry.cgi"
    # Try synchronous delete first
    params = {
        "api": "SYNO.FileStation.Delete",
        "version": "1",
        "method": "delete",
        "path": ",".join(paths) if isinstance(paths, list) else paths,
        "recursive": "true" if recursive else "false",
        "_sid": sid
    }
    response = requests.get(url, params=params, verify=False)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        error_code = data.get("error", {}).get("code", "Unknown")
        # If too many files, error 900 might happen, but normally synchronous is fine for few files.
        raise Exception(f"Delete failed (Error code: {error_code})")
    return True

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"

def main():
    parser = argparse.ArgumentParser(description="Manage Synology NAS and File Station")
    parser.add_argument("target", nargs="?", help="Magnet link, URL, or local .torrent file path")
    parser.add_argument("--config", help="Path to config.json with NAS credentials")
    parser.add_argument("--list", choices=["all", "downloading", "completed"], help="List tasks by status")
    parser.add_argument("--status", action="store_true", help="Get NAS storage status")
    parser.add_argument("--ls", help="List files in a specific NAS path (e.g. /video or /)")
    parser.add_argument("--rm", nargs="+", help="Delete one or more files/folders in NAS (absolute paths)")
    args = parser.parse_args()

    # Determine config file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(script_dir)
    default_config = os.path.join(skill_root, "config.json")
    config_path = args.config if args.config else default_config

    # Load configuration
    nas_url = os.environ.get("SYNOLOGY_NAS_URL")
    username = os.environ.get("SYNOLOGY_USERNAME")
    password = os.environ.get("SYNOLOGY_PASSWORD")

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            nas_url = config.get("nas_url", nas_url)
            username = config.get("username", username)
            password = config.get("password", password)

    if not all([nas_url, username, password]):
        print("Error: Missing Synology configuration.")
        sys.exit(1)

    try:
        sid = login(nas_url, username, password)
        
        if args.status:
            print("\n--- NAS Status ---")
            try:
                volumes = get_storage_info(nas_url, sid)
                print("Storage (Volume) Info:")
                for vol in volumes:
                    vol_path = vol.get('volume_path') or vol.get('mount_path') or vol.get('id')
                    status = vol.get('status')
                    size_data = vol.get('size') or vol
                    total = int(size_data.get('total') or size_data.get('total_size') or 0)
                    used = int(size_data.get('used') or size_data.get('used_size') or 0)
                    if total == 0: continue
                    free = total - used
                    print(f"Volume: {vol_path} | Status: {status} | Used: {format_size(used)}/{format_size(total)}")
            except Exception as e:
                print(f"Note: Could not retrieve full storage info ({e}).")
            print("")

        if args.list:
            tasks = list_tasks(nas_url, sid, args.list)
            print(f"\n--- Download Tasks ({args.list}) ---")
            for t in tasks:
                title = t.get('title')
                status = t.get('status')
                size = int(t.get('size', 0))
                print(f"[{status.upper()}] {title} ({format_size(size)})")
            print("")

        if args.ls:
            files = file_list(nas_url, sid, args.ls)
            print(f"\n--- Files in {args.ls} ---")
            for f in files:
                ftype = "DIR" if f.get('isdir') else "FILE"
                name = f.get('name')
                size = f.get('additional', {}).get('size', 0)
                print(f"[{ftype}] {name} ({format_size(size)})")
            print("")

        if args.rm:
            file_delete(nas_url, sid, args.rm)
            print(f"Success: Deleted {len(args.rm)} item(s) from NAS.")
        
        if args.target:
            create_task(nas_url, sid, args.target)
            print(f"Success: Task for '{args.target}' added.")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
