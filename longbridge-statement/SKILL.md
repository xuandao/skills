---
name: longbridge-statement
description: Automatically fetch, decrypt, and analyze Longbridge Securities daily/monthly statements from Gmail. Use when user asks to check/analyze/download Longbridge statements, review stock positions, or generate portfolio reports. Handles PDF decryption, text extraction, position analysis, risk assessment, and generates Markdown reports to Obsidian vault. Supports batch processing for historical data.
---

# Longbridge Statement Analyzer

Automatically fetch Longbridge Securities statements (daily/monthly) from Gmail, decrypt PDFs, analyze positions, and generate reports.

## Quick Start

### Daily Statement Analysis

Run the daily analysis script:

```bash
python3 scripts/longbridge-auto-analysis.py
```

### Monthly Statement Analysis

Run the monthly analysis script:

```bash
python3 scripts/longbridge-monthly-analysis.py
```

### Batch Process Historical Statements

Process multiple months at once (e.g., 2025/01 - 2026/01):

```bash
python3 scripts/batch-process-monthly.py
```

All scripts will:
1. Search Gmail for statements from `noreply@longbridge.hk`
2. Download PDF attachments
3. Decrypt with configured password
4. Extract text content
5. Analyze positions and risks
6. Generate Markdown reports to Obsidian

## Configuration

Edit the script's `CONFIG` dictionary:

```python
CONFIG = {
    # For daily statements
    "gmail_query": "from:noreply@longbridge.hk subject:日结单",
    
    # For monthly statements
    "gmail_query": "from:noreply@longbridge.hk subject:月结单",
    
    "download_dir": Path.home() / "Downloads" / "longbridge-statements",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/长桥",
    "pdf_password": "96087252",
}
```

## Output

### Downloaded Files
- `~/Downloads/longbridge-statements/statement-*.pdf` - Original encrypted PDF
- `~/Downloads/longbridge-statements/statement-*-decrypted.pdf` - Decrypted PDF

### Obsidian Reports

**Daily Report**:
- Location: `Areas/理财/长桥/YYYYMMDD-持仓分析.md`
- Contains:
  - Account summary (total assets, cash, margin)
  - Position details with P&L
  - Risk warnings (deep losses, low cash)
  - Actionable recommendations

**Monthly Report**:
- Location: `Areas/理财/长桥/YYYYMM-长桥月度结单分析.md`
- Format: Same as 202602 template (detailed analysis)
- Contains:
  - Monthly account overview
  - Cash flow summary (deposits, withdrawals, dividends)
  - Position analysis with full details (quantity, price, cost, P&L)
  - Risk assessment and recommendations
  - Structured frontmatter for Dataview queries

**Batch Processing**:
- Processes multiple months at once
- Uses the same detailed format as single-month analysis
- Generates consistent reports for trend analysis
- Supports Dataview cross-month queries

## Batch Processing

### Process Historical Statements

To analyze multiple months (e.g., 2025/01 - 2026/01):

```bash
python3 scripts/batch-process-monthly.py
```

**What it does**:
1. Searches Gmail for all monthly statements
2. Identifies target months (configured in script)
3. Processes each month using the full analysis pipeline
4. Generates detailed reports in the same format as 202602

**Configuration**:
Edit `TARGET_MONTHS` in `batch-process-monthly.py`:

```python
TARGET_MONTHS = [
    "202501", "202502", "202503", "202504", "202505", "202506",
    "202507", "202508", "202509", "202510", "202511", "202512",
    "202601"
]
```

**Time estimate**: ~2-3 minutes per month (30-40 minutes for 13 months)

**Output**: All reports saved to `Areas/理财/长桥/YYYYMM-长桥月度结单分析.md`

## Automation

### Cron Jobs

**Monthly Statement (Recommended)**:

Run automatically on the 6th of each month at 9:00 AM:

```bash
# Add to crontab
0 9 6 * * /usr/bin/python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-monthly-analysis.py >> ~/Library/Logs/longbridge-monthly.log 2>&1
```

**Daily Statement**:

Run automatically every day at 22:00 (after market close):

```bash
# Add to crontab
0 22 * * * /usr/bin/python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-auto-analysis.py >> ~/Library/Logs/longbridge-daily.log 2>&1
```

**Install cron job**:

```bash
# Edit crontab
crontab -e

# Or use command
(crontab -l 2>/dev/null; echo "0 9 6 * * /usr/bin/python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-monthly-analysis.py >> ~/Library/Logs/longbridge-monthly.log 2>&1") | crontab -
```

**View logs**:

```bash
# Monthly statement logs
tail -f ~/Library/Logs/longbridge-monthly.log

# Daily statement logs
tail -f ~/Library/Logs/longbridge-daily.log
```

**Test cron job**:

```bash
# Test if the script runs correctly in cron environment
bash ~/.openclaw/workspace/skills/longbridge-statement/scripts/test-cron.sh
```

### Heartbeat Integration

Add to `HEARTBEAT.md`:

```markdown
## Monthly Tasks (6th of month)
- Check Longbridge monthly statement
  - Cron job will auto-run at 9:00 AM
  - Check logs: `tail ~/Library/Logs/longbridge-monthly.log`
```

## Dependencies

The script auto-installs required packages:
- `pikepdf` - PDF decryption
- `pdfplumber` - Text extraction

Manual installation:
```bash
pip3 install --user pikepdf pdfplumber
```

## Statement Format

### Supported Format

All scripts are configured to parse the **new format** (July 2025 onwards):

```
股票 (美国市场; 美元)
代码 名称 期初数量 变更 期末数量 价格 市值 成本 盈亏 保证金比例 保证金
AMZN 亚马逊 105.00 0.00 105.00 207.92 21,831.60 223.05 -1,588.97 25.00% 5,457.90
```

**Features**:
- Clear section headers
- Structured table format
- Complete position details (quantity, price, cost, P&L)
- Risk indicators (margin ratio)

### Legacy Format

Statements from January-June 2025 use an older format:

```
综合账户月结单
苹果 0.00 20.00 20.00 237.59 4,751.80 245.00 -148.20 18.00% 855.32
```

**Limitations**:
- No section headers
- Different data structure
- Requires separate parser (not implemented)

**Impact**: Historical data (202501-202506) has partial information only (transactions, dividends), but no position details.

**Recommendation**: Use data from July 2025 onwards (202507+) for complete analysis. All future statements will use the new format.

## Troubleshooting

### No statement found
- Check Gmail for emails from `noreply@longbridge.hk`
- For daily: verify email subject contains "日结单"
- For monthly: verify email subject contains "月结单"
- Test: `gws gmail users messages list --params '{"userId": "me", "q": "from:noreply@longbridge.hk"}'`

### Wrong password
- Update `pdf_password` in script's `CONFIG`
- Current password: `96087252`

### Parsing errors
- Statement format may have changed
- Check extracted text in `~/Downloads/longbridge-statements/*.txt`
- Update regex patterns in `parse_statement()` or `parse_monthly_statement()` function

## Monthly vs Daily Reports

### Daily Report Features
- Real-time position snapshot
- Daily P&L tracking
- Immediate risk alerts
- Quick decision support

### Monthly Report Features
- Cash flow summary (deposits, withdrawals, dividends, interest)
- Monthly performance review
- Transaction history
- Trend analysis
- Comprehensive risk assessment

## Advanced Usage

### Custom Analysis

Modify parsing functions to extract additional data:
- Transaction history details
- Dividend payment schedules
- Margin requirements breakdown
- Currency exposure analysis
- Sector allocation

### Report Customization

Edit `generate_report()` or `generate_monthly_report()` to change:
- Risk thresholds (currently -30% for high risk)
- Report format and sections
- Recommendation logic
- Chart generation (requires additional libraries)

### Integration with Other Tools

The scripts output structured data that can be:
- Imported to spreadsheets
- Sent to notification services
- Integrated with portfolio trackers
- Used for tax reporting

## Reference Files

See `references/` for:
- Statement format examples
- Parsing patterns
- Risk calculation formulas
