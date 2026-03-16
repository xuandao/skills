#!/usr/bin/env python3
"""
长桥证券月结单完整分析工作流
包含：下载 → 解密 → 提取 → AI 分析 → 生成月度报告
"""

import os
import sys
import json
import subprocess
import base64
import re
from datetime import datetime
from pathlib import Path
from decimal import Decimal

# 添加必要的导入
try:
    import pikepdf
    import pdfplumber
except ImportError:
    print("❌ 缺少依赖库，正在安装...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--user", "pikepdf", "pdfplumber"])
    import pikepdf
    import pdfplumber

# 配置
CONFIG = {
    "gmail_query": "from:noreply@longbridge.hk subject:月结单",
    "download_dir": Path.home() / "Downloads" / "longbridge-statements",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/长桥",
    "pdf_password": "96087252",
}

def run_command(cmd, capture=True):
    """运行命令"""
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
        return result.stdout, result.stderr, result.returncode
    else:
        return subprocess.run(cmd, shell=isinstance(cmd, str))

def get_latest_statement():
    """获取最新月结单"""
    print("📧 搜索最新月结单邮件...")
    
    cmd = [
        "gws", "gmail", "users", "messages", "list",
        "--params", json.dumps({"userId": "me", "q": CONFIG["gmail_query"], "maxResults": 1})
    ]
    
    stdout, stderr, code = run_command(cmd)
    if code != 0:
        raise Exception(f"搜索邮件失败: {stderr}")
    
    data = json.loads(stdout)
    if not data.get("messages"):
        raise Exception("未找到月结单邮件")
    
    message_id = data["messages"][0]["id"]
    print(f"✅ 找到邮件: {message_id}")
    
    # 获取邮件详情
    cmd = [
        "gws", "gmail", "users", "messages", "get",
        "--params", json.dumps({"userId": "me", "id": message_id})
    ]
    
    stdout, stderr, code = run_command(cmd)
    if code != 0:
        raise Exception(f"获取邮件失败: {stderr}")
    
    message = json.loads(stdout)
    
    # 查找 PDF 附件
    parts = message["payload"].get("parts", [message["payload"]])
    for part in parts:
        filename = part.get("filename", "")
        if re.search(r"statement.*\.pdf", filename, re.I):
            attachment_id = part["body"].get("attachmentId")
            if attachment_id:
                print(f"✅ 找到附件: {filename}")
                return message_id, attachment_id, filename
    
    raise Exception("未找到 PDF 附件")

def download_and_decrypt(message_id, attachment_id, filename):
    """下载并解密 PDF"""
    print("⬇️  下载附件...")
    
    # 下载
    cmd = [
        "gws", "gmail", "users", "messages", "attachments", "get",
        "--params", json.dumps({"userId": "me", "messageId": message_id, "id": attachment_id})
    ]
    
    stdout, stderr, code = run_command(cmd)
    if code != 0:
        raise Exception(f"下载失败: {stderr}")
    
    data = json.loads(stdout)
    pdf_data = base64.urlsafe_b64decode(data["data"])
    
    # 保存加密 PDF
    CONFIG["download_dir"].mkdir(parents=True, exist_ok=True)
    pdf_path = CONFIG["download_dir"] / filename
    pdf_path.write_bytes(pdf_data)
    print(f"✅ 已下载: {pdf_path}")
    
    # 解密
    print("🔓 解密 PDF...")
    decrypted_path = pdf_path.with_name(pdf_path.stem + "-decrypted.pdf")
    
    try:
        pdf = pikepdf.open(pdf_path, password=CONFIG["pdf_password"])
        pdf.save(decrypted_path)
        print("✅ 解密成功")
    except pikepdf.PasswordError:
        raise Exception("密码错误")
    
    return decrypted_path

def extract_text(pdf_path):
    """提取 PDF 文本"""
    print("📄 提取文本...")
    
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text += page.extract_text() + "\n\n"
    
    print("✅ 提取完成")
    return text

def parse_number(s):
    """解析数字字符串，处理逗号和负号"""
    if not s or s == "N/A":
        return 0.0
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def parse_monthly_statement(text):
    """解析月结单数据 - 月结单格式可能与日结单略有不同"""
    data = {
        "account_summary": {},
        "positions": {
            "stocks": [],
            "funds": [],
        },
        "monthly_summary": {
            "deposits": 0,
            "withdrawals": 0,
            "dividends": 0,
            "interest": 0,
            "fees": 0,
            "net_pnl": 0
        },
        "transactions": []
    }
    
    # 1. 提取账户总览
    account_pattern = r'资⾦余额\s+市值\s+总资产\s+融资⾦额.*?含贷权益价值\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+[\d,\.]+\s+([\d,\.]+)\s+[\d,\.]+\s+[\d,\.]+\s+([\d,\.]+)'
    if match := re.search(account_pattern, text, re.DOTALL):
        data["account_summary"] = {
            "cash_balance": parse_number(match.group(1)),
            "market_value": parse_number(match.group(2)),
            "total_assets": parse_number(match.group(3)),
            "margin_loan": parse_number(match.group(4)),
            "margin_requirement": parse_number(match.group(5)),
            "equity_value": parse_number(match.group(6))
        }
    
    # 2. 提取美股持仓
    stock_pattern = r'([A-Z]{2,5})\s+([^\d]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([-\d,\.]+)\s+([\d,\.]+%)\s+([\d,\.]+)'
    
    stock_section = re.search(r'股票 \(美国市场; 美元\)(.*?)汇总 \(美元\)', text, re.DOTALL)
    if stock_section:
        stock_text = stock_section.group(1)
        
        for match in re.finditer(stock_pattern, stock_text):
            try:
                symbol = match.group(1)
                name = match.group(2).strip()
                quantity = parse_number(match.group(5))
                price = parse_number(match.group(6))
                market_value = parse_number(match.group(7))
                cost = parse_number(match.group(8))
                pnl = parse_number(match.group(9))
                
                if quantity > 0 and market_value > 0:
                    data["positions"]["stocks"].append({
                        "symbol": symbol,
                        "name": name,
                        "quantity": quantity,
                        "price": price,
                        "market_value": market_value,
                        "cost": cost,
                        "pnl": pnl,
                        "pnl_pct": (pnl / (market_value - pnl) * 100) if (market_value - pnl) != 0 else 0
                    })
            except Exception as e:
                print(f"⚠️  解析股票行失败: {match.group(0)[:80]}... - {e}")
    
    # 3. 提取货币基金
    fund_sections = [
        (r'余额通 \(余额通; 港元\)(.*?)汇总 \(港元\)', "HKD"),
        (r'余额通 \(余额通; 美元\)(.*?)汇总 \(美元\)', "USD"),
        (r'基⾦ \(基⾦; 美元\)(.*?)汇总 \(美元\)', "USD")
    ]
    
    for pattern, currency in fund_sections:
        section = re.search(pattern, text, re.DOTALL)
        if section:
            fund_text = section.group(1)
            fund_pattern = r'(HK\d+)\s+([^\n]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([-\d,\.]+)'
            for match in re.finditer(fund_pattern, fund_text):
                try:
                    code = match.group(1)
                    name = match.group(2).strip()
                    quantity = parse_number(match.group(5))
                    price = parse_number(match.group(6))
                    market_value = parse_number(match.group(7))
                    cost = parse_number(match.group(8))
                    pnl = parse_number(match.group(9))
                    
                    data["positions"]["funds"].append({
                        "code": code,
                        "name": name,
                        "quantity": quantity,
                        "price": price,
                        "market_value": market_value,
                        "cost": cost,
                        "pnl": pnl,
                        "pnl_pct": (pnl / (market_value - pnl) * 100) if (market_value - pnl) != 0 else 0,
                        "currency": currency
                    })
                except Exception as e:
                    print(f"⚠️  解析基金失败: {match.group(0)[:50]}... - {e}")
    
    # 4. 提取月度交易汇总（月结单特有）
    # 查找入金、出金、分红、利息等
    trans_pattern = r'(\d{4}\.\d{2}\.\d{2})\s+(现⾦分红|公司⾏动其他费⽤|利息|转账|入金|出金)\s+([^\n]+?)\s+([-\d,\.]+)'
    for match in re.finditer(trans_pattern, text):
        trans_type = match.group(2)
        amount = parse_number(match.group(4))
        
        data["transactions"].append({
            "date": match.group(1),
            "type": trans_type,
            "description": match.group(3).strip(),
            "amount": amount
        })
        
        # 汇总统计
        if "入金" in trans_type or "转账" in trans_type and amount > 0:
            data["monthly_summary"]["deposits"] += amount
        elif "出金" in trans_type or "转账" in trans_type and amount < 0:
            data["monthly_summary"]["withdrawals"] += abs(amount)
        elif "分红" in trans_type:
            data["monthly_summary"]["dividends"] += amount
        elif "利息" in trans_type:
            data["monthly_summary"]["interest"] += amount
        elif "费用" in trans_type:
            data["monthly_summary"]["fees"] += abs(amount)
    
    return data

def generate_monthly_report(data, year_month, filename):
    """生成月度分析报告"""
    
    summary = data["account_summary"]
    stocks = data["positions"]["stocks"]
    funds = data["positions"]["funds"]
    monthly = data["monthly_summary"]
    transactions = data["transactions"]
    
    # 计算关键指标
    total_assets = summary.get("total_assets", 0)
    cash_balance = summary.get("cash_balance", 0)
    market_value = summary.get("market_value", 0)
    margin_loan = summary.get("margin_loan", 0)
    
    cash_ratio = (cash_balance / total_assets * 100) if total_assets > 0 else 0
    margin_ratio = (margin_loan / total_assets * 100) if total_assets > 0 else 0
    
    # 计算持仓市值
    stock_market_value = sum(s["market_value"] for s in stocks)
    fund_market_value_usd = sum(f["market_value"] for f in funds if f.get("currency") == "USD")
    fund_market_value_hkd = sum(f["market_value"] for f in funds if f.get("currency") == "HKD")
    
    USD_TO_HKD = 7.818
    
    # 计算总盈亏
    total_stock_pnl = sum(s["pnl"] for s in stocks)
    total_fund_pnl = sum(f["pnl"] for f in funds)
    total_pnl = total_stock_pnl + total_fund_pnl
    
    # 分析风险持仓
    high_risk = [s for s in stocks if s["pnl_pct"] < -30]
    medium_risk = [s for s in stocks if -30 <= s["pnl_pct"] < -10]
    profitable = [s for s in stocks if s["pnl_pct"] > 0]
    
    # 生成报告
    report = f"""---
date: {year_month}
source: {filename}
type: 月度结单分析
---

# 长桥证券月度结单分析

**报告月份**: {year_month}  
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**数据来源**: {filename}

---

## 📊 账户概况

| 项目 | 金额 (HKD) | 备注 |
|------|-----------|------|
| 💰 总资产 | {total_assets:,.2f} | 约 {total_assets / 7.8 if total_assets > 0 else 0:.0f} CNY |
| 📈 市值 | {market_value:,.2f} | {market_value / total_assets * 100 if total_assets > 0 else 0:.1f}% |
| 💵 现金余额 | {cash_balance:,.2f} | {cash_ratio:.1f}% |
| 🏦 融资金额 | {margin_loan:,.2f} | {margin_ratio:.1f}% |
| 💎 含贷权益 | {summary.get('equity_value', 0):,.2f} | - |

### 持仓构成

- **美股**: {stock_market_value:,.2f} USD (约 {stock_market_value * USD_TO_HKD:,.0f} HKD)
- **货币基金 (USD)**: {fund_market_value_usd:,.2f} USD (约 {fund_market_value_usd * USD_TO_HKD:,.0f} HKD)
- **货币基金 (HKD)**: {fund_market_value_hkd:,.2f} HKD
- **现金**: {cash_balance:,.2f} HKD

---

## 💰 月度资金流水

| 项目 | 金额 (USD) | 备注 |
|------|-----------|------|
| 📥 入金 | {monthly['deposits']:,.2f} | - |
| 📤 出金 | {monthly['withdrawals']:,.2f} | - |
| 💵 分红收入 | {monthly['dividends']:,.2f} | - |
| 💰 利息收入 | {monthly['interest']:,.2f} | - |
| 💸 手续费 | {monthly['fees']:,.2f} | - |
| 📊 净流入 | {monthly['deposits'] - monthly['withdrawals']:+,.2f} | - |

### 月度收益分析

- **投资收益**: {total_pnl:,.2f} USD {'🟢' if total_pnl > 0 else '🔴'}
- **分红+利息**: {monthly['dividends'] + monthly['interest']:,.2f} USD
- **总收益**: {total_pnl + monthly['dividends'] + monthly['interest']:,.2f} USD
- **收益率**: {(total_pnl / (market_value - total_pnl) * 100) if (market_value - total_pnl) != 0 else 0:.2f}%

---

## 💼 美股持仓明细

"""
    
    if stocks:
        stocks_sorted = sorted(stocks, key=lambda x: x["market_value"], reverse=True)
        
        report += "| 代码 | 名称 | 数量 | 价格 | 市值 (USD) | 成本 | 盈亏 (USD) | 盈亏率 | 风险 |\n"
        report += "|------|------|------|------|-----------|------|-----------|--------|------|\n"
        
        for stock in stocks_sorted:
            risk_emoji = "🟢" if stock["pnl_pct"] > -10 else "🟡" if stock["pnl_pct"] > -30 else "🔴"
            pnl_emoji = "📈" if stock["pnl"] > 0 else "📉"
            
            report += f"| {stock['symbol']} | {stock['name']} | {stock['quantity']:.0f} | {stock['price']:.2f} | "
            report += f"{stock['market_value']:,.2f} | {stock['cost']:.2f} | "
            report += f"{pnl_emoji} {stock['pnl']:,.2f} | {stock['pnl_pct']:+.1f}% | {risk_emoji} |\n"
        
        report += f"\n**合计**: {len(stocks)} 只股票，市值 {sum(s['market_value'] for s in stocks):,.2f} USD，"
        report += f"盈亏 {total_stock_pnl:+,.2f} USD\n"
    else:
        report += "_未检测到股票持仓_\n"
    
    # 货币基金
    if funds:
        report += "\n### 💰 货币基金\n\n"
        report += "| 代码 | 名称 | 币种 | 市值 | 盈亏 | 盈亏率 |\n"
        report += "|------|------|------|------|------|--------|\n"
        
        for fund in funds:
            currency = fund.get("currency", "USD")
            report += f"| {fund['code']} | {fund['name']} | {currency} | "
            report += f"{fund['market_value']:,.2f} | {fund['pnl']:+,.2f} | {fund['pnl_pct']:+.1f}% |\n"
        
        report += f"\n**合计**: {len(funds)} 只基金\n"
    
    report += "\n---\n\n## ⚠️ 风险分析\n\n"
    
    # 风险评估
    risk_items = []
    
    if cash_ratio < 5:
        risk_items.append(f"🔴 **现金严重不足**: 仅 {cash_ratio:.1f}%，建议至少保持 10-15%")
    elif cash_ratio < 10:
        risk_items.append(f"🟡 **现金偏低**: {cash_ratio:.1f}%，建议提升至 10-15%")
    
    if margin_ratio > 50:
        risk_items.append(f"🔴 **融资比例过高**: {margin_ratio:.1f}%，存在强平风险")
    elif margin_ratio > 30:
        risk_items.append(f"🟡 **融资比例适中**: {margin_ratio:.1f}%，注意市场波动")
    
    if high_risk:
        risk_items.append(f"🔴 **深度亏损持仓** ({len(high_risk)} 只):")
        for stock in sorted(high_risk, key=lambda x: x["pnl_pct"]):
            risk_items.append(f"  - **{stock['symbol']} {stock['name']}**: {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)")
    
    if medium_risk:
        risk_items.append(f"🟡 **中度亏损持仓** ({len(medium_risk)} 只):")
        for stock in sorted(medium_risk, key=lambda x: x["pnl_pct"]):
            risk_items.append(f"  - {stock['symbol']} {stock['name']}: {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)")
    
    if risk_items:
        report += "\n".join(risk_items) + "\n"
    else:
        report += "🟢 **整体风险可控**，各项指标正常\n"
    
    report += "\n---\n\n## 💡 月度总结与建议\n\n"
    
    # 月度总结
    report += "### 📈 本月亮点\n\n"
    
    if profitable:
        top_profit = sorted(profitable, key=lambda x: x["pnl"], reverse=True)[0]
        report += f"- **最佳表现**: {top_profit['symbol']} {top_profit['name']} 盈利 {top_profit['pnl']:,.2f} USD ({top_profit['pnl_pct']:+.1f}%)\n"
    
    if monthly['dividends'] > 0:
        report += f"- **分红收入**: {monthly['dividends']:,.2f} USD\n"
    
    if monthly['deposits'] > 0:
        report += f"- **资金流入**: {monthly['deposits']:,.2f} USD\n"
    
    # 改进建议
    report += "\n### 🎯 改进建议\n\n"
    
    if high_risk:
        report += "1. **止损优先**: 处理深度亏损持仓，避免继续扩大损失\n"
    
    if cash_ratio < 10:
        report += "2. **提升现金**: 建议将现金比例提升至 10-15%\n"
    
    if len(stocks) > 15:
        report += "3. **精简持仓**: 持仓过多，建议集中优质标的\n"
    
    report += "\n---\n\n## 📝 交易记录\n\n"
    
    if transactions:
        report += "| 日期 | 类型 | 说明 | 金额 (USD) |\n"
        report += "|------|------|------|------------|\n"
        for trans in transactions[:20]:  # 只显示前20条
            report += f"| {trans['date']} | {trans['type']} | {trans['description']} | {trans['amount']:+,.2f} |\n"
        
        if len(transactions) > 20:
            report += f"\n_... 共 {len(transactions)} 条交易记录_\n"
    else:
        report += "_本月无交易记录_\n"
    
    report += "\n\n---\n\n## 📎 附件\n\n"
    report += f"- 原始 PDF: `{filename}`\n"
    report += f"- 下载位置: `~/Downloads/longbridge-statements/`\n"
    
    return report

def main():
    """主函数"""
    print("\n=== 长桥证券月结单自动分析 ===\n")
    
    try:
        # 1. 获取最新月结单
        message_id, attachment_id, filename = get_latest_statement()
        
        # 2. 下载并解密
        decrypted_pdf = download_and_decrypt(message_id, attachment_id, filename)
        
        # 3. 提取文本
        text = extract_text(decrypted_pdf)
        
        # 4. 解析数据
        print("🤖 分析月结单...")
        data = parse_monthly_statement(text)
        
        # 5. 提取年月
        date_match = re.search(r'(\d{4})\.(\d{2})', text)
        if date_match:
            year_month = f"{date_match.group(1)}{date_match.group(2)}"
        else:
            year_month = datetime.now().strftime("%Y%m")
        
        # 6. 生成报告
        report = generate_monthly_report(data, year_month, filename)
        
        # 7. 保存到 Obsidian
        CONFIG["obsidian_dir"].mkdir(parents=True, exist_ok=True)
        report_path = CONFIG["obsidian_dir"] / f"{year_month}-长桥月度结单分析.md"
        report_path.write_text(report, encoding="utf-8")
        
        print(f"✅ 报告已保存: {report_path}\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

