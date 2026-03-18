import subprocess
import json
import os

# --- Configuration ---
SKILL_DIR = "/Users/xuandao/.openclaw/workspace/skills/daily-summary"
MANAGER_SCRIPT = os.path.join(SKILL_DIR, "scripts/daily_manager.py")
TELEGRAM_TARGET = "5247154884" # From your jobs.json

def run_manager():
    result = subprocess.run(["python3", MANAGER_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running manager: {result.stderr}")
        return None
    return json.loads(result.stdout)

def main():
    data = run_manager()
    if not data:
        return

    prompt = f"""
请基于以下数据生成一份精美的每日晨报（Markdown 格式），直接通过 Telegram 发送给我。
要求：
1. 包含一句励志的古诗词（带作者）。
2. 包含 3 条历史上的今天（{data['today']}）发生的重大事件。
3. 汇总 openClaw 系统状态。
4. 列出最近收藏的 3 篇文章及其摘要。
5. 提及今日已归档 {data['archived']} 篇旧笔记，并从昨日继承了 {data['tasks_migrated']} 项任务。

数据如下：
{json.dumps(data, ensure_ascii=False, indent=2)}
"""

    # Use 'openclaw agent' with --deliver and explicit target
    gen_cmd = [
        "openclaw", "agent", 
        "--channel", "telegram",
        "--to", TELEGRAM_TARGET,
        "--message", prompt,
        "--deliver"
    ]
    subprocess.run(gen_cmd)
    print("Summary request sent to OpenClaw Agent for delivery.")

if __name__ == "__main__":
    main()
