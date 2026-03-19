---
name: synology
description: Manage Synology NAS (Download Station & File Station). Use when the user asks to download torrents, list/delete tasks, check storage space, list files in NAS directories, or delete files on the NAS.
---

# Synology

A comprehensive skill to manage your Synology NAS downloads, files, and system status.

## Workflow

1.  **Detect Trigger**: 
    -   **Downloads**: Torrent files, magnet links, or asking about download tasks.
    -   **Files**: Asking to list files in a NAS directory or delete specific files/folders.
    -   **Status**: Asking about disk space or NAS health.
2.  **Configuration**: Ensure `config.json` in the skill root is configured with your NAS details.
3.  **Execution**: Calls `scripts/synology_download.py` with appropriate flags.

## Configuration Guide

Create `config.json` in the skill root:

```json
{
  "nas_url": "http://YOUR_NAS_IP:5000",
  "username": "YOUR_ACCOUNT",
  "password": "YOUR_PASSWORD"
}
```

## Usage Examples

### Manage Downloads
- **Add Task**: `python scripts/synology_download.py "magnet:?xt=urn:btih:..."`
- **List Tasks**: `python scripts/synology_download.py --list downloading`

### File Operations
- **List Directory**: `python scripts/synology_download.py --ls /video` (Use `/` to list shared folders)
- **Delete Files**: `python scripts/synology_download.py --rm "/video/temp.mp4" "/video/old_folder"`

### System Status
- **Check Space**: `python scripts/synology_download.py --status`

## Dependencies
Requires `requests`:
```bash
pip install requests
```
