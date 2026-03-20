import os
import datetime
import shutil
import json
import re
import subprocess
from pathlib import Path

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "config.json")

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
OBSIDIAN_ROOT = config.get("OBSIDIAN_ROOT")
DAILY_FOLDER = os.path.join(OBSIDIAN_ROOT, config.get("DAILY_FOLDER"))
ARCHIVE_FOLDER = os.path.join(OBSIDIAN_ROOT, config.get("ARCHIVE_FOLDER"))
TEMPLATE_PATH = os.path.join(OBSIDIAN_ROOT, config.get("TEMPLATE_PATH"))

def get_today():
    return datetime.date.today()

def format_date(date, fmt="%Y-%m-%d"):
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_str = weekdays[date.weekday()]
    return f"{date.strftime(fmt)} {weekday_str}"

def get_weather():
    """
    获取今日天气。
    """
    try:
        # 使用 wttr.in 获取天气，简要格式
        result = subprocess.run(
            ["curl", "-s", "wttr.in/?format=%c+%t+%w+%p"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "未知天气"

def get_calendar_events():
    """
    获取今日日历事件。
    优先使用 icalBuddy，如果不存在则尝试使用 AppleScript。
    """
    events = []
    today = get_today()
    today_str = today.strftime("%Y-%m-%d")
    
    # 检查 icalBuddy 是否存在
    icalbuddy_exists = False
    try:
        result = subprocess.run(["which", "icalBuddy"], capture_output=True, timeout=2)
        icalbuddy_exists = result.returncode == 0
    except:
        pass
    
    # 尝试使用 icalBuddy
    if icalbuddy_exists:
        try:
            result = subprocess.run(
                ["icalBuddy", "-n", "-li", "20", "-iep", "datetime,title", "-po", "datetime,title", "-ea", "eventsToday"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                # 解析 icalBuddy 输出
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("•"):
                        # 格式通常是 "时间: 事件标题"
                        if ":" in line:
                            events.append(line)
                        else:
                            events.append(f"全天: {line}")
                if events:
                    return events
        except Exception:
            pass
    
    # 尝试使用 AppleScript 作为备选
    try:
        applescript = '''
        tell application "Calendar"
            set todayStart to current date
            set time of todayStart to 0
            set todayEnd to todayStart + (23 * hours + 59 * minutes)
            set eventList to {}
            repeat with cal in calendars
                set calEvents to (every event of cal whose start date ≥ todayStart and start date ≤ todayEnd)
                repeat with evt in calEvents
                    set eventTime to time string of (start date of evt)
                    set eventTitle to summary of evt
                    set end of eventList to (eventTime & ": " & eventTitle)
                end repeat
            end repeat
            return eventList as string
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split(", ")
            for line in lines:
                line = line.strip()
                if line:
                    events.append(line)
            if events:
                return events
    except Exception:
        pass
    
    # 如果没有任何事件，添加提示信息
    if not events and not icalbuddy_exists:
        events.append("💡 安装 icalBuddy 以获取日历: brew install ical-buddy")
    
    return events

def archive_and_collect_tasks():
    """
    归档 7 天前的笔记，并从中提取未完成的任务。
    """
    today = get_today()
    cutoff_date = today - datetime.timedelta(days=7)
    
    if not os.path.exists(ARCHIVE_FOLDER):
        os.makedirs(ARCHIVE_FOLDER)
        
    collected_tasks = []
    archived_count = 0
    
    for filename in os.listdir(DAILY_FOLDER):
        if not filename.endswith(".md"):
            continue
            
        try:
            date_str = filename.replace(".md", "")
            # 提取日期部分（处理文件名可能包含空格或其他字符的情况）
            match = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
            if not match:
                continue
            date_part = match.group(1)
            file_date = datetime.datetime.strptime(date_part, "%Y-%m-%d").date()
            
            if file_date < cutoff_date:
                file_path = os.path.join(DAILY_FOLDER, filename)
                
                # 1. 提取未完成待办
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith("- [ ]") and "📅" in line:
                            collected_tasks.append(line.rstrip())
                
                # 2. 执行移动
                shutil.move(file_path, os.path.join(ARCHIVE_FOLDER, filename))
                archived_count += 1
                
        except (ValueError, Exception):
            continue
            
    return archived_count, collected_tasks

def create_today_note(tasks, weather_info, calendar_events):
    """
    创建今日笔记并插入提取到的任务、天气和日历信息。
    """
    today = get_today()
    today_str = today.strftime("%Y-%m-%d")
    full_date_str = format_date(today)
    today_path = os.path.join(DAILY_FOLDER, f"{today_str}.md")
    
    # 构建天气和日历信息块
    info_block = f"> 天气：{weather_info}"
    if calendar_events:
        info_block += "\n> \n> 📅 **今日日程**："
        for event in calendar_events[:5]:  # 最多显示5个事件
            info_block += f"\n> • {event}"
    
    # 如果今日笔记已存在，则读取内容；否则使用模板
    if os.path.exists(today_path):
        with open(today_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        if os.path.exists(TEMPLATE_PATH):
            with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                content = f.read().replace("{{date:YYYY-MM-DD}}", today_str)
        else:
            content = f"# {full_date_str}\n\n{info_block}\n\n## 📋 今日待办\n\n"

    # 检查是否已包含天气信息，如果没有则添加，如果存在则更新
    if "天气：" not in content:
        # 在第一行标题后添加天气和日历信息
        lines = content.split("\n")
        if lines[0].startswith("# "):
            lines.insert(1, f"\n{info_block}")
            content = "\n".join(lines)
    else:
        # 更新现有的天气/日历信息块
        lines = content.split("\n")
        new_lines = []
        skip_until_empty = False
        for i, line in enumerate(lines):
            if i == 0:
                new_lines.append(line)
                new_lines.append("")
                new_lines.append(info_block)
                skip_until_empty = True
            elif skip_until_empty:
                # 跳过旧的天气/日历信息块，直到遇到空行或新的章节
                if line.startswith("## ") or (line.strip() == "" and i > 2):
                    skip_until_empty = False
                    if line.startswith("## "):
                        new_lines.append("")
                        new_lines.append(line)
                continue
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

    # 插入任务（避免重复插入）
    if tasks:
        section_pattern = r"(## 📋 今日待办|## 今日待办)"
        match = re.search(section_pattern, content)
        if match:
            header = match.group(0)
            
            # 简单去重逻辑
            existing_content = content
            unique_tasks = []
            for t in tasks:
                # 如果任务内容（去掉日期标签后）不在现有笔记中，则添加
                task_content = re.sub(r"📅 \d{4}-\d{2}-\d{2}", "", t).strip()
                if task_content not in existing_content:
                    unique_tasks.append(t)
            
            if unique_tasks:
                pos = content.find(header) + len(header)
                content = content[:pos] + "\n" + "\n".join(unique_tasks) + content[pos:]

    with open(today_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return today_path

def main():
    # 1. 获取天气和日历
    weather_info = get_weather()
    calendar_events = get_calendar_events()
    today_info = format_date(get_today())
    
    # 2. 归档并打捞任务
    archived_count, rescued_tasks = archive_and_collect_tasks()
    
    # 3. 创建/更新今日笔记
    today_path = create_today_note(rescued_tasks, weather_info, calendar_events)
    
    print(json.dumps({
        "status": "success",
        "date": today_info,
        "weather": weather_info,
        "calendar_events": calendar_events,
        "calendar_events_count": len(calendar_events),
        "archived_count": archived_count,
        "tasks_rescued_count": len(rescued_tasks),
        "today_note_path": today_path,
        "obsidian_root": OBSIDIAN_ROOT
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
