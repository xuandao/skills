import os
import datetime
import shutil
import json
import re
import subprocess
from pathlib import Path

# --- Configuration ---
OBSIDIAN_ROOT = "/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7"
DAILY_FOLDER = os.path.join(OBSIDIAN_ROOT, "Projects/Daily")
ARCHIVE_FOLDER = os.path.join(OBSIDIAN_ROOT, "Archive/Daily")
TEMPLATE_PATH = os.path.join(OBSIDIAN_ROOT, "Resources/Templates/daily-template.md")
FAVORITES_FOLDER = os.path.join(OBSIDIAN_ROOT, "Resources/收藏夹")
OPENCLAW_CONFIG = "/Users/xuandao/.openclaw/openclaw.json"
OPENCLAW_CRON_JOBS = "/Users/xuandao/.openclaw/cron/jobs.json"

def get_today():
    return datetime.date.today()

def get_yesterday():
    return get_today() - datetime.timedelta(days=1)

def format_date(date, fmt="%Y-%m-%d"):
    return date.strftime(fmt)

def get_chinese_weekday(date):
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return weekdays[date.weekday()]

# 1. Archive logic (older than 7 days)
def archive_old_notes():
    today = get_today()
    cutoff_date = today - datetime.timedelta(days=7)
    
    if not os.path.exists(ARCHIVE_FOLDER):
        os.makedirs(ARCHIVE_FOLDER)
        
    archived_count = 0
    for filename in os.listdir(DAILY_FOLDER):
        if filename.endswith(".md"):
            try:
                # Expecting YYYY-MM-DD.md
                date_str = filename.replace(".md", "")
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if file_date < cutoff_date:
                    src = os.path.join(DAILY_FOLDER, filename)
                    dst = os.path.join(ARCHIVE_FOLDER, filename)
                    shutil.move(src, dst)
                    archived_count += 1
            except ValueError:
                continue
    return archived_count

# 2. Migration and Today's Note
def get_unfinished_tasks(yesterday_str):
    yesterday_path = os.path.join(DAILY_FOLDER, f"{yesterday_str}.md")
    tasks = []
    if os.path.exists(yesterday_path):
        with open(yesterday_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # We look for tasks (- [ ]) but NOT those marked done
            # Also need to be careful with subtasks or indentation
            for line in lines:
                if line.strip().startswith("- [ ]") and "📅" in line:
                    # Capture the task but maybe remove/update the date tag if needed
                    # For simplicity, we just take the line as is
                    tasks.append(line.rstrip())
    return tasks

def create_today_note(today_str, weekday_str, unfinished_tasks):
    today_path = os.path.join(DAILY_FOLDER, f"{today_str}.md")
    if os.path.exists(today_path):
        # Already exists, we might want to append tasks if not there, 
        # but the request says "Create today's Daily Note"
        # Let's read it to avoid duplication if it exists
        with open(today_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
        
        content = template.replace("{{date:YYYY-MM-DD}}", today_str)
        content = content.replace("{{date:dddd}}", weekday_str)

    # Insert unfinished tasks if any
    if unfinished_tasks:
        # Find the "## 📋 今日待办" or "## 今日待办" section
        section_pattern = r"(## 📋 今日待办|## 今日待办)"
        match = re.search(section_pattern, content)
        if match:
            header = match.group(0)
            # Find where the next section starts or end of file
            parts = re.split(section_pattern, content)
            # parts[0] is before header, parts[1] is header, parts[2] is after header
            
            # Check if these tasks are already in the note
            existing_tasks = set(re.findall(r"- \[ \] .*", content))
            new_tasks_to_add = [t for t in unfinished_tasks if t not in existing_tasks]
            
            if new_tasks_to_add:
                # Insert after the header
                header_pos = content.find(header) + len(header)
                content = content[:header_pos] + "\n" + "\n".join(new_tasks_to_add) + content[header_pos:]

    with open(today_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return today_path

# 3. openClaw Status
def get_openclaw_summary():
    # Cron jobs
    try:
        with open(OPENCLAW_CRON_JOBS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jobs = data.get("jobs", [])
            total_jobs = len(jobs)
            enabled_jobs = sum(1 for j in jobs if j.get("enabled"))
            # Check for errors in state
            errors = []
            for j in jobs:
                state = j.get("state", {})
                if state.get("lastStatus") == "error":
                    errors.append(j.get("name", "Unknown Job"))
    except Exception:
        total_jobs, enabled_jobs, errors = 0, 0, []

    # Tokens / Status via CLI
    try:
        result = subprocess.run(["openclaw", "status"], capture_output=True, text=True)
        status_output = result.stdout
        # Basic parsing for active sessions/tokens if possible
        # Or just include the summary line
        token_line = "Tokens: (Check openclaw status for details)"
        for line in status_output.split('\n'):
            if "Sessions" in line and "active" in line:
                token_line = line.strip()
                break
    except Exception:
        token_line = "Unable to fetch openclaw status"

    return {
        "total": total_jobs,
        "enabled": enabled_jobs,
        "errors": errors,
        "tokens": token_line
    }

# 4. Recent Favorites
def get_recent_favorites():
    favorites = []
    if os.path.exists(FAVORITES_FOLDER):
        # Sort by filename (which starts with date) descending
        files = sorted([f for f in os.listdir(FAVORITES_FOLDER) if f.endswith(".md")], reverse=True)
        for f in files[:3]:
            path = os.path.join(FAVORITES_FOLDER, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Extract title (first # H1)
                title_match = re.search(r"^# (.*)", content, re.MULTILINE)
                title = title_match.group(1) if title_match else f
                # Extract summary (first > quote or "核心观点" section)
                summary_match = re.search(r"^> (.*)", content, re.MULTILINE)
                summary = summary_match.group(1) if summary_match else "暂无摘要"
                favorites.append({"title": title, "summary": summary, "link": f})
    return favorites

def main():
    today = get_today()
    today_str = format_date(today)
    yesterday_str = format_date(get_yesterday())
    weekday_str = get_chinese_weekday(today)

    # Archive
    archived_count = archive_old_notes()

    # Tasks
    unfinished_tasks = get_unfinished_tasks(yesterday_str)

    # Today's Note
    today_note_path = create_today_note(today_str, weekday_str, unfinished_tasks)

    # openClaw Summary
    oc_summary = get_openclaw_summary()

    # Favorites
    favs = get_recent_favorites()

    # Prepare Telegram Summary (Markdown format for Telegram)
    # We will let the Agent handle the "Poem" and "History" part or add placeholders
    # Since this script runs via cron/agent, the agent can fill these in if we structure the payload.
    # However, to be autonomous, we'll ask the agent to "Generate a summary based on this data" 
    # OR we can use the model inside the agent turn.
    
    summary_data = {
        "today": f"{today_str} {weekday_str}",
        "archived": archived_count,
        "tasks_migrated": len(unfinished_tasks),
        "oc_status": oc_summary,
        "recent_favs": favs
    }
    
    # Print the JSON result so the calling agent can use it to compose the final message
    print(json.dumps(summary_data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
