# Synology API Documentation

## Authentication (SYNO.API.Auth)
- **Endpoint**: `/webapi/auth.cgi`
- **Version**: `2`
- **Method**: `login`
- **Parameters**: `api`, `version`, `method`, `account`, `passwd`, `session=DownloadStation`, `format=sid`

## Download Station (SYNO.DownloadStation.Task)
- **Endpoint**: `/webapi/DownloadStation/task.cgi`
- **Methods**: `create`, `list`, `delete`, `pause`, `resume`
- **Filter**: `all`, `downloading`, `completed`, `active`, `inactive`

## File Station List (SYNO.FileStation.List)
- **Endpoint**: `/webapi/entry.cgi`
- **Method**: `list`
- **Parameters**:
    - `folder_path`: Absolute path (e.g., `"/video"`)
    - `additional`: `["size", "time", "perm"]`
- **Method**: `list_share` (Lists root shared folders)

## File Station Delete (SYNO.FileStation.Delete)
- **Endpoint**: `/webapi/entry.cgi`
- **Method**: `delete` (Synchronous) or `start` (Asynchronous)
- **Parameters**:
    - `path`: One or more absolute paths (comma-separated)
    - `recursive`: `true` or `false`

## Storage Info
- **DSM 7+ API**: `SYNO.Storage.CGI.Storage` (Method: `load_info`)
- **DSM 6 API**: `SYNO.Core.Storage.Volume` (Method: `list`)
