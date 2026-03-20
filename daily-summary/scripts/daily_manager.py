import os
import datetime
import shutil
import json
import re
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
    return date.strftime(fmt)

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
            file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
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
                
        except ValueError:
            continue
            
    return archived_count, collected_tasks

def create_today_note(tasks):
    """
    创建今日笔记并插入提取到的任务。
    """
    today_str = format_date(get_today())
    today_path = os.path.join(DAILY_FOLDER, f"{today_str}.md")
    
    # 如果今日笔记已存在，则读取内容；否则使用模板
    if os.path.exists(today_path):
        with open(today_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        if os.path.exists(TEMPLATE_PATH):
            with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                content = f.read().replace("{{date:YYYY-MM-DD}}", today_str)
        else:
            content = "## 📋 今日待办\n\n"

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
    # 1. 归档并打捞任务
    archived_count, rescued_tasks = archive_and_collect_tasks()
    
    # 2. 创建/更新今日笔记
    today_path = create_today_note(rescued_tasks)
    
    print(json.dumps({
        "status": "success",
        "archived_count": archived_count,
        "tasks_rescued_count": len(rescued_tasks),
        "today_note_path": today_path,
        "obsidian_root": OBSIDIAN_ROOT
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
