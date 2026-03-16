#!/usr/bin/env python3
"""
长桥证券日结单完整分析工作流
包含：下载 → 解密 → 提取 → AI 分析 → 生成报告
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
    "gmail_query": "from:noreply@longbridge.hk subject:日结单",
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
    """获取最新日结单"""
    print("📧 搜索最新日结单邮件...")
    
    cmd = [
        "gws", "gmail", "users", "messages", "list",
        "--params", json.dumps({"userId": "me", "q": CONFIG["gmail_query"], "maxResults": 1})
    ]
    
    stdout, stderr, code = run_command(cmd)
    if code != 0:
        raise Exception(f"搜索邮件失败: {stderr}")
    
    data = json.loads(stdout)
    if not data.get("messages"):
        raise Exception("未找到日结单邮件")
    
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

def parse_statement(text):
    """解析日结单数据 - 优化版"""
    data = {
        "account_summary": {},
        "positions": {
            "stocks": [],
            "funds": [],
            "money_market": []
        },
        "transactions": [],
        "currencies": {}
    }
    
    # 1. 提取账户总览（精确匹配表格行）
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
    
    # 2. 提取美股持仓（使用更精确的正则表达式）
    # 匹配格式: SYMBOL 名称 期初数量 变更 期末数量 价格 市值 成本 盈亏 保证金比例 保证金
    # 名称可能包含中文、英文、空格、连字符等
    stock_pattern = r'([A-Z]{2,5})\s+([^\d]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([-\d,\.]+)\s+([\d,\.]+%)\s+([\d,\.]+)'
    
    stock_section = re.search(r'股票 \(美国市场; 美元\)(.*?)汇总 \(美元\)', text, re.DOTALL)
    if stock_section:
        stock_text = stock_section.group(1)
        
        for match in re.finditer(stock_pattern, stock_text):
            try:
                symbol = match.group(1)
                name = match.group(2).strip()
                quantity = parse_number(match.group(5))  # 期末持仓
                price = parse_number(match.group(6))
                market_value = parse_number(match.group(7))
                cost = parse_number(match.group(8))
                pnl = parse_number(match.group(9))
                
                # 只添加有实际持仓的股票
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
    
    # 3. 提取货币基金（余额通）- 需要区分币种
    # 港元基金
    hkd_fund_section = re.search(r'余额通 \(余额通; 港元\)(.*?)汇总 \(港元\)', text, re.DOTALL)
    if hkd_fund_section:
        fund_text = hkd_fund_section.group(1)
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
                    "currency": "HKD"
                })
            except Exception as e:
                print(f"⚠️  解析港元基金失败: {match.group(0)[:50]}... - {e}")
    
    # 美元基金（余额通 + 其他基金）
    usd_sections = [
        (r'余额通 \(余额通; 美元\)(.*?)汇总 \(美元\)', "余额通"),
        (r'基⾦ \(基⾦; 美元\)(.*?)汇总 \(美元\)', "基金")
    ]
    
    for pattern, section_name in usd_sections:
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
                        "currency": "USD"
                    })
                except Exception as e:
                    print(f"⚠️  解析美元{section_name}失败: {match.group(0)[:50]}... - {e}")
    
    # 4. 提取交易记录
    trans_pattern = r'(\d{4}\.\d{2}\.\d{2})\s+(现⾦分红|公司⾏动其他费⽤|利息|转账)\s+([^\n]+?)\s+([-\d,\.]+)'
    for match in re.finditer(trans_pattern, text):
        data["transactions"].append({
            "date": match.group(1),
            "type": match.group(2),
            "description": match.group(3).strip(),
            "amount": parse_number(match.group(4))
        })
    
    return data

def get_stock_fundamentals(symbol):
    """获取股票基本面评估（基于常见知识）"""
    
    # 股票基本面数据库（可以扩展）
    fundamentals = {
        "AMZN": {
            "name": "亚马逊",
            "sector": "科技/电商",
            "strengths": ["云计算 AWS 领先", "电商龙头地位", "现金流强劲"],
            "risks": ["估值偏高", "监管压力", "竞争加剧"],
            "outlook": "长期看好",
            "recommendation": "核心持仓，适合长期持有"
        },
        "GOOGL": {
            "name": "谷歌",
            "sector": "科技/互联网",
            "strengths": ["搜索广告垄断", "AI 技术领先", "多元化业务"],
            "risks": ["监管风险", "AI 竞争", "广告收入依赖"],
            "outlook": "长期看好",
            "recommendation": "优质资产，可逢低加仓"
        },
        "BABA": {
            "name": "阿里巴巴",
            "sector": "科技/电商",
            "strengths": ["中国电商龙头", "云计算增长", "估值较低"],
            "risks": ["政策监管", "竞争激烈", "宏观经济"],
            "outlook": "中性偏谨慎",
            "recommendation": "短期波动大，建议控制仓位"
        },
        "LI": {
            "name": "理想汽车",
            "sector": "新能源汽车",
            "strengths": ["增程式技术路线", "销量持续增长", "产品线扩张"],
            "risks": ["竞争白热化", "价格战压力", "利润率下降", "政策依赖"],
            "outlook": "谨慎",
            "recommendation": "行业竞争激烈，建议减仓观察"
        },
        "FIG": {
            "name": "Figma",
            "sector": "软件/设计工具",
            "strengths": ["设计工具领先", "协作功能强"],
            "risks": ["Adobe 收购失败", "估值暴跌", "流动性差", "私有公司"],
            "outlook": "悲观",
            "recommendation": "收购失败后前景不明，建议止损"
        },
        "TSLA": {
            "name": "特斯拉",
            "sector": "新能源汽车",
            "strengths": ["电动车领导者", "自动驾驶技术", "品牌影响力"],
            "risks": ["估值极高", "竞争加剧", "马斯克风险"],
            "outlook": "中性",
            "recommendation": "波动大，不建议重仓"
        },
        "QQQ": {
            "name": "纳指100 ETF",
            "sector": "ETF/科技",
            "strengths": ["分散投资", "科技股集合", "流动性好"],
            "risks": ["科技股集中", "估值偏高"],
            "outlook": "长期看好",
            "recommendation": "核心配置，适合定投"
        },
        "SPY": {
            "name": "标普500 ETF",
            "sector": "ETF/大盘",
            "strengths": ["最分散", "长期向上", "低费率"],
            "risks": ["短期波动"],
            "outlook": "长期看好",
            "recommendation": "最稳健配置，长期持有"
        },
        "PFF": {
            "name": "优先股 ETF",
            "sector": "ETF/固收",
            "strengths": ["稳定分红", "波动较小", "收益率可观"],
            "risks": ["利率风险", "信用风险"],
            "outlook": "稳健",
            "recommendation": "固收配置，适合长期持有"
        },
        "TSLL": {
            "name": "2倍做多特斯拉",
            "sector": "杠杆ETF",
            "strengths": ["放大收益"],
            "risks": ["放大亏损", "时间损耗", "极高波动"],
            "outlook": "高风险",
            "recommendation": "不适合长期持有，建议清仓"
        }
    }
    
    return fundamentals.get(symbol, {
        "name": symbol,
        "sector": "未知",
        "strengths": ["需要进一步研究"],
        "risks": ["信息不足"],
        "outlook": "未知",
        "recommendation": "建议自行研究基本面"
    })

def generate_fundamental_analysis(stocks, high_risk, medium_risk):
    """生成基本面分析报告"""
    
    analysis = "### 🎯 止损建议（含基本面分析）\n\n"
    
    if not high_risk and not medium_risk:
        return ""
    
    # 分析深度亏损持仓
    if high_risk:
        analysis += "#### 🔴 深度亏损持仓\n\n"
        
        for stock in sorted(high_risk, key=lambda x: x["pnl_pct"]):
            fund = get_stock_fundamentals(stock["symbol"])
            
            analysis += f"**{stock['symbol']} - {stock['name']}**\n\n"
            analysis += f"- **当前状态**: 亏损 {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)\n"
            analysis += f"- **行业**: {fund['sector']}\n"
            analysis += f"- **优势**: {', '.join(fund['strengths'])}\n"
            analysis += f"- **风险**: {', '.join(fund['risks'])}\n"
            analysis += f"- **前景**: {fund['outlook']}\n"
            analysis += f"- **建议**: {fund['recommendation']}\n\n"
            
            # 根据亏损程度给出具体操作建议
            if stock['pnl_pct'] < -50:
                analysis += f"  💡 **操作**: 亏损已超过 50%，建议尽快止损，避免继续扩大损失\n\n"
            elif stock['pnl_pct'] < -40:
                analysis += f"  💡 **操作**: 亏损较大，建议减仓 50-70%，保留小部分观察\n\n"
            else:
                analysis += f"  💡 **操作**: 已触及止损线（-30%），建议评估基本面后决定是否减仓\n\n"
    
    # 分析中度亏损持仓
    if medium_risk:
        analysis += "#### 🟡 中度亏损持仓\n\n"
        
        for stock in sorted(medium_risk, key=lambda x: x["pnl_pct"]):
            fund = get_stock_fundamentals(stock["symbol"])
            
            analysis += f"**{stock['symbol']} - {stock['name']}**: {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)\n"
            analysis += f"- **前景**: {fund['outlook']} | **建议**: {fund['recommendation']}\n\n"
    
    return analysis

def generate_report(data, date, filename):
    """生成分析报告 - 优化版"""
    
    summary = data["account_summary"]
    stocks = data["positions"]["stocks"]
    funds = data["positions"]["funds"]
    transactions = data["transactions"]
    
    # 计算关键指标
    total_assets = summary.get("total_assets", 0)
    cash_balance = summary.get("cash_balance", 0)
    market_value = summary.get("market_value", 0)  # 这是所有投资的市值（股票+基金）
    margin_loan = summary.get("margin_loan", 0)
    
    cash_ratio = (cash_balance / total_assets * 100) if total_assets > 0 else 0
    margin_ratio = (margin_loan / total_assets * 100) if total_assets > 0 else 0
    
    # 计算实际持仓市值（从持仓数据计算，用于验证）
    stock_market_value = sum(s["market_value"] for s in stocks)
    fund_market_value_usd = sum(f["market_value"] for f in funds if f.get("currency") == "USD")
    fund_market_value_hkd = sum(f["market_value"] for f in funds if f.get("currency") == "HKD")
    
    # 转换为 HKD 计算总市值
    USD_TO_HKD = 7.818
    calculated_market_value_hkd = (stock_market_value + fund_market_value_usd) * USD_TO_HKD + fund_market_value_hkd
    
    # 计算总盈亏
    total_stock_pnl = sum(s["pnl"] for s in stocks)
    total_fund_pnl = sum(f["pnl"] for f in funds)
    total_pnl = total_stock_pnl + total_fund_pnl
    
    # 分析风险持仓
    high_risk = [s for s in stocks if s["pnl_pct"] < -30]
    medium_risk = [s for s in stocks if -30 <= s["pnl_pct"] < -10]
    profitable = [s for s in stocks if s["pnl_pct"] > 0]
    
    # 计算集中度（基于实际股票市值）
    if stocks:
        stocks_sorted = sorted(stocks, key=lambda x: x["market_value"], reverse=True)
        # 集中度应该基于总市值（包括基金）
        top1_ratio = (stocks_sorted[0]["market_value"] * USD_TO_HKD / calculated_market_value_hkd * 100) if calculated_market_value_hkd > 0 else 0
        top3_value = sum(s["market_value"] for s in stocks_sorted[:3])
        top3_ratio = (top3_value * USD_TO_HKD / calculated_market_value_hkd * 100) if calculated_market_value_hkd > 0 else 0
    else:
        top1_ratio = top3_ratio = 0
    
    # 生成报告
    report = f"""---
date: {date}
source: {filename}
type: 持仓分析
---

# 长桥证券持仓分析报告

**报告日期**: {date}  
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**数据来源**: {filename}

---

## 📊 账户概况

| 项目 | 金额 (HKD) | 备注 |
|------|-----------|------|
| 💰 总资产 | {total_assets:,.2f} | 约 {total_assets / 7.8:.0f} CNY |
| 📈 市值 | {market_value:,.2f} | {market_value / total_assets * 100:.1f}% |
| 💵 现金余额 | {cash_balance:,.2f} | {cash_ratio:.1f}% |
| 🏦 融资金额 | {margin_loan:,.2f} | {margin_ratio:.1f}% |
| 💎 含贷权益 | {summary.get('equity_value', 0):,.2f} | - |

### 持仓构成

- **美股**: {stock_market_value:,.2f} USD (约 {stock_market_value * USD_TO_HKD:,.0f} HKD)
- **货币基金 (USD)**: {fund_market_value_usd:,.2f} USD (约 {fund_market_value_usd * USD_TO_HKD:,.0f} HKD)
- **货币基金 (HKD)**: {fund_market_value_hkd:,.2f} HKD
- **现金**: {cash_balance:,.2f} HKD
- **合计**: {calculated_market_value_hkd + cash_balance:,.2f} HKD

### 关键指标

- **现金比例**: {cash_ratio:.1f}% {'🟢 健康' if cash_ratio >= 15 else '🟡 偏低' if cash_ratio >= 10 else '🔴 过低'}
- **融资使用**: {margin_ratio:.1f}% {'🟢 安全' if margin_ratio < 30 else '🟡 适中' if margin_ratio < 50 else '🔴 偏高'}
- **总盈亏**: {total_pnl:,.2f} USD {'🟢' if total_pnl > 0 else '🔴'} (约 {total_pnl * USD_TO_HKD:,.0f} HKD)
- **股票集中度**: Top1 {top1_ratio:.1f}% | Top3 {top3_ratio:.1f}% {'🟢' if top3_ratio < 60 else '🟡'}

---

## 💼 美股持仓明细

"""
    
    if stocks:
        # 按市值排序
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
        
        report += f"\n**合计**: {len(funds)} 只基金，"
        report += f"USD {fund_market_value_usd:,.2f} + HKD {fund_market_value_hkd:,.2f}\n"
    
    report += "\n---\n\n## ⚠️ 风险分析\n\n"
    
    # 风险评估
    risk_score = 0
    risk_items = []
    
    if cash_ratio < 5:
        risk_score += 3
        risk_items.append(f"🔴 **现金严重不足**: 仅 {cash_ratio:.1f}%，建议至少保持 10-15%")
    elif cash_ratio < 10:
        risk_score += 1
        risk_items.append(f"🟡 **现金偏低**: {cash_ratio:.1f}%，建议提升至 10-15%")
    
    if margin_ratio > 50:
        risk_score += 3
        risk_items.append(f"🔴 **融资比例过高**: {margin_ratio:.1f}%，存在强平风险")
    elif margin_ratio > 30:
        risk_score += 1
        risk_items.append(f"🟡 **融资比例适中**: {margin_ratio:.1f}%，注意市场波动")
    
    if high_risk:
        risk_score += 2
        risk_items.append(f"🔴 **深度亏损持仓** ({len(high_risk)} 只):")
        for stock in sorted(high_risk, key=lambda x: x["pnl_pct"]):
            risk_items.append(f"  - **{stock['symbol']} {stock['name']}**: {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)")
    
    if medium_risk:
        risk_score += 1
        risk_items.append(f"🟡 **中度亏损持仓** ({len(medium_risk)} 只):")
        for stock in sorted(medium_risk, key=lambda x: x["pnl_pct"]):
            risk_items.append(f"  - {stock['symbol']} {stock['name']}: {stock['pnl']:,.2f} USD ({stock['pnl_pct']:.1f}%)")
    
    if top1_ratio > 40:
        risk_score += 2
        risk_items.append(f"🔴 **持仓过度集中**: 最大持仓占比 {top1_ratio:.1f}%")
    elif top3_ratio > 70:
        risk_score += 1
        risk_items.append(f"🟡 **持仓集中度偏高**: 前三大持仓占比 {top3_ratio:.1f}%")
    
    if risk_items:
        report += "\n".join(risk_items) + "\n"
    else:
        report += "🟢 **整体风险可控**，各项指标正常\n"
    
    # 风险评分
    report += f"\n**风险评分**: {risk_score}/10 "
    if risk_score >= 7:
        report += "🔴 高风险"
    elif risk_score >= 4:
        report += "🟡 中等风险"
    else:
        report += "🟢 低风险"
    
    report += "\n\n---\n\n## 💡 操作建议\n\n"
    
    # 生成基本面分析
    fundamental_analysis = generate_fundamental_analysis(stocks, high_risk, medium_risk)
    if fundamental_analysis:
        report += fundamental_analysis
    
    # 生成其他建议
    suggestions = []
    
    # 现金管理建议（如果没有深度亏损才建议）
    if cash_ratio < 10 and not high_risk:
        suggestions.append("### 💵 现金管理\n")
        target_cash = total_assets * 0.12  # 目标 12%
        need_raise = target_cash - cash_balance
        suggestions.append(f"- 建议减仓约 {need_raise:,.0f} HKD，提升现金比例至 12%")
        if profitable:
            top_profit = sorted(profitable, key=lambda x: x["pnl"], reverse=True)[0]
            suggestions.append(f"- 可考虑减持盈利较好的 {top_profit['symbol']} (盈利 {top_profit['pnl_pct']:+.1f}%)")
        suggestions.append("")
    elif cash_ratio < 10 and high_risk:
        suggestions.append("### 💵 现金管理\n")
        suggestions.append(f"- 优先处理深度亏损持仓，止损后可提升现金比例")
        suggestions.append("")
    
    if top1_ratio > 35:
        suggestions.append("### 📊 分散风险\n")
        suggestions.append(f"- 最大持仓 {stocks_sorted[0]['symbol']} 占比 {top1_ratio:.1f}%，建议降至 30% 以下")
        suggestions.append(f"- 可考虑增加其他优质标的，或增持 ETF 分散风险")
    
    if not suggestions:
        suggestions.append("### ✅ 持续优化\n")
        suggestions.append("- 当前配置合理，继续保持")
        suggestions.append("- 定期复盘（每周检查，每月调整）")
        suggestions.append("- 关注市场变化，及时调整策略")
    
    report += "\n".join(suggestions)
    
    # 交易记录
    if transactions:
        report += "\n\n---\n\n## 📝 近期交易\n\n"
        report += "| 日期 | 类型 | 说明 | 金额 (USD) |\n"
        report += "|------|------|------|------------|\n"
        for trans in transactions:
            report += f"| {trans['date']} | {trans['type']} | {trans['description']} | {trans['amount']:+,.2f} |\n"
    
    report += "\n\n---\n\n## 📎 附件\n\n"
    report += f"- 原始 PDF: `{filename}`\n"
    report += f"- 下载位置: `~/Downloads/longbridge-statements/`\n"
    
    return report

def analyze_with_ai(text, filename):
    """使用 AI 分析日结单"""
    print("🤖 AI 分析中...")
    
    # 提取日期
    date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', text)
    if date_match:
        report_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        file_date = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
    else:
        report_date = datetime.now().strftime("%Y-%m-%d")
        file_date = datetime.now().strftime("%Y%m%d")
    
    # 解析关键数据
    analysis = parse_statement(text)
    
    # 生成报告
    report = generate_report(analysis, report_date, filename)
    
    # 保存到 Obsidian
    CONFIG["obsidian_dir"].mkdir(parents=True, exist_ok=True)
    report_path = CONFIG["obsidian_dir"] / f"{file_date}-持仓分析.md"
    report_path.write_text(report, encoding="utf-8")
    
    print(f"✅ 报告已保存: {report_path}")
    return report_path

def main():
    """主函数"""
    print("\n=== 长桥证券日结单自动分析 ===\n")
    
    try:
        # 1. 获取最新日结单
        message_id, attachment_id, filename = get_latest_statement()
        
        # 2. 下载并解密
        decrypted_pdf = download_and_decrypt(message_id, attachment_id, filename)
        
        # 3. 提取文本
        text = extract_text(decrypted_pdf)
        
        # 4. AI 分析并生成报告
        report_path = analyze_with_ai(text, filename)
        
        print(f"\n✅ 完成！报告已保存到:\n{report_path}\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
