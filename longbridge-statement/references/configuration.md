# Configuration Guide

## User-Specific Settings

Before using the skill, update these settings in `scripts/longbridge-auto-analysis.py`:

### Required Configuration

```python
CONFIG = {
    # Gmail search query
    "gmail_query": "from:noreply@longbridge.hk subject:日结单",
    
    # Download directory for PDFs
    "download_dir": Path.home() / "Downloads" / "longbridge-statements",
    
    # Obsidian vault location
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/长桥",
    
    # PDF decryption password
    "pdf_password": "96087252",
}
```

### Finding Your Obsidian Vault Path

**macOS (iCloud)**:
```bash
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/
```

**macOS (Local)**:
```bash
~/Documents/<VaultName>/
```

**Linux**:
```bash
~/Documents/<VaultName>/
```

**Windows**:
```
C:\Users\<Username>\Documents\<VaultName>\
```

### Gmail Query Customization

Modify the query to filter statements:

```python
# Last 7 days only
"gmail_query": "from:noreply@longbridge.hk subject:日结单 newer_than:7d"

# Specific date range
"gmail_query": "from:noreply@longbridge.hk subject:日结单 after:2026/03/01 before:2026/03/31"

# Exclude read emails
"gmail_query": "from:noreply@longbridge.hk subject:日结单 is:unread"
```

## Risk Thresholds

Customize risk levels in `parse_statement()`:

```python
# Current defaults
LOW_RISK_THRESHOLD = -10    # P&L > -10%
HIGH_RISK_THRESHOLD = -30   # P&L <= -30%

CASH_HEALTHY = 15           # Cash ratio >= 15%
CASH_WARNING = 10           # Cash ratio 10-15%
```

## Report Customization

### Output Format

Change report structure in `generate_report()`:

```python
# Add custom sections
report += "\n## 📈 Performance Metrics\n\n"
report += f"- Total Return: {total_return:.2f}%\n"
report += f"- Sharpe Ratio: {sharpe_ratio:.2f}\n"

# Change table format
report += "| Symbol | Name | Quantity | Value | P&L | P&L% |\n"
```

### Language

Switch between Chinese and English:

```python
# English headers
HEADERS = {
    "account_summary": "Account Summary",
    "positions": "Positions",
    "risk_warning": "Risk Warning",
    "recommendations": "Recommendations"
}

# Chinese headers (default)
HEADERS = {
    "account_summary": "账户概况",
    "positions": "持仓明细",
    "risk_warning": "风险提示",
    "recommendations": "建议"
}
```

## Automation Settings

### Cron Schedule

```bash
# Daily at 22:00 (after market close)
0 22 * * * python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-auto-analysis.py

# Weekdays only at 22:00
0 22 * * 1-5 python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-auto-analysis.py

# Every 6 hours
0 */6 * * * python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-auto-analysis.py
```

### Notification Integration

Add notifications on completion:

```python
# At end of main()
if report_path:
    # macOS notification
    os.system(f'osascript -e \'display notification "Report generated" with title "Longbridge Analysis"\'')
    
    # Or send to messaging service
    # subprocess.run(["openclaw", "message", "send", "--target", "me", "--message", f"Report ready: {report_path}"])
```

## Advanced Options

### Multiple Accounts

Handle multiple Longbridge accounts:

```python
ACCOUNTS = {
    "H10111344": {
        "password": "96087252",
        "obsidian_path": "Areas/理财/长桥/账户1"
    },
    "H20222455": {
        "password": "12345678",
        "obsidian_path": "Areas/理财/长桥/账户2"
    }
}

# Detect account from filename
account_id = re.search(r'H\d+', filename).group()
config = ACCOUNTS[account_id]
```

### Historical Comparison

Track changes over time:

```python
# Load previous report
previous_report = load_previous_report(date - timedelta(days=1))

# Compare positions
for symbol in current_positions:
    if symbol in previous_positions:
        change = current_positions[symbol] - previous_positions[symbol]
        report += f"- {symbol}: {change:+.2f}%\n"
```

### Export to CSV

Add CSV export:

```python
import csv

def export_to_csv(positions, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'name', 'quantity', 'price', 'value', 'pnl'])
        writer.writeheader()
        writer.writerows(positions)
```

## Environment Variables

Use environment variables for sensitive data:

```python
import os

CONFIG = {
    "pdf_password": os.getenv("LONGBRIDGE_PASSWORD", "default_password"),
    "gmail_query": os.getenv("LONGBRIDGE_GMAIL_QUERY", "from:noreply@longbridge.hk subject:日结单"),
}
```

Set in shell:
```bash
export LONGBRIDGE_PASSWORD="96087252"
export LONGBRIDGE_GMAIL_QUERY="from:noreply@longbridge.hk subject:日结单"
```

## Logging

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('longbridge-analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting analysis...")
```
