#!/usr/bin/env python3
"""
招商银行信用卡账单自动分析工具 v5.0
解析无附件账单（HTML正文），生成分析报告到 Obsidian
新增功能：
- 自动识别并标注退货/退款交易
- 单独拆分消费分期明细
- 分期账单独立统计
"""

import json
import subprocess
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# ============ 配置 ============
CONFIG = {
    # Gmail 查询条件（只查询信用卡账单，不要综合对账单）
    "gmail_query": "(from:招商银行 OR from:cmbchina.com) subject:信用卡电子账单 newer_than:90d",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",
}

# 消费分类关键词（基于描述智能匹配）
CATEGORY_KEYWORDS = {
    "餐饮": [
        # 正餐
        "餐", "饭", "食", "外婆家", "莜面村", "西贝", "海底捞", "火锅", "烧烤", "自助",
        "披萨", "意面", "牛排", "日料", "寿司", "韩式", "泰式", "川菜", "粤菜", "本帮菜",
        # 快餐/小吃
        "肯德基", "麦当劳", "汉堡王", "必胜客", "赛百味", "沙县", "兰州拉面", "黄焖鸡",
        "老乡鸡", "老娘舅", "米村拌饭", "鱼你在一起", "面馆", "小吃", "米线", "馄饨", "饺子",
        # 咖啡茶饮
        "咖啡", "茶", "星巴克", "瑞幸", "喜茶", "奈雪", "霸王茶姬", "柠季", "茶百道",
        "沪上阿姨", "益禾堂", "书亦", "茵赫", "Manner", "M Stand", "Seesaw",
        # 外卖平台
        "美团", "饿了么", "拉扎斯", "大众点评",  # 拉扎斯 = 饿了么
    ],
    "购物": [
        # 电商平台
        "淘宝", "京东", "拼多多", "天猫", "天猫超市", "京东到家", "唯品会", "苏宁",
        "网易严选", "小米商城", "小米有品",
        # 线下商超
        "超市", "商场", "沃尔玛", "山姆", "盒马", "大润发", "永辉", "物美", "华润",
        "罗森", "全家", "711", "便利蜂", "便利", "美宜佳", "天福",
        # 数码电器
        "苹果", "Apple", "小米", "华为", "OPPO", "vivo", "三星", "索尼", "戴尔",
        "联想", "华硕", "京东电脑", "京东手机",
        # 服装美妆
        "优衣库", "Zara", "H&M", "Nike", "Adidas", "李宁", "安踏", "迪卡侬", "特步",
        "丝芙兰", "屈臣氏", "万宁", "MAC", "雅诗兰黛", "兰蔻", "SK-II",
        # 其他电商
        "小红书", "蘑菇街", "考拉", "亚马逊", "当当", "闲鱼",
    ],
    "交通": [
        # 网约车
        "滴滴", "嘀嘀", "曹操", "首汽", "T3", "享道", "高德", "百度地图",
        # 出租车
        "出租", "的士", "打车",
        # 公共交通
        "地铁", "公交", "地铁乘车", "公交乘车", "交通卡",
        # 加油充电
        "加油", "中石化", "中石油", "壳牌", "道达尔", "充电", "特来电", "星星充电",
        "蔚来", "小鹏", "理想",
        # 停车高速
        "停车", "停车场", "高速", "ETC", "路桥费",
        # 航空铁路
        "航空", "机票", "高铁", "火车", "国航", "东航", "南航", "厦航", "春秋",
    ],
    "娱乐": [
        # 影视
        "电影", "影院", "万达", "CGV", "IMAX", "横店", "淘票票", "猫眼",
        "爱奇艺", "腾讯视频", "优酷", "芒果TV", "B站", "bilibili", "YouTube", "Netflix",
        # 游戏
        "游戏", "Steam", "Epic", "PlayStation", "Xbox", "Nintendo", "Switch", "腾讯游戏",
        "网易游戏", "米哈游",
        # 健身运动
        "健身", "瑜伽", "普拉提", "威尔士", "一兆韦德", "超级猩猩", "乐刻", "Keep",
        "体育", "游泳", "羽毛球", "网球", "乒乓球",
        # 音乐演出
        "音乐", "演唱会", "演出", "话剧", "歌剧", "音乐剧", "交响乐", "剧院",
        "网易云", "QQ音乐", "酷狗", "酷我", "Apple Music", "Spotify",
        # 旅游
        "旅游", "酒店", "民宿", "携程", "飞猪", "去哪儿", "Booking", "Airbnb",
        "景点", "门票", "乐园", "迪士尼", "环球影城", "方特",
        # 亲子娱乐
        "乐高", "智乐鼓", "玩具", "游乐园", "儿童",
    ],
    "生活": [
        # 水电燃气
        "水电", "物业", "电费", "水费", "燃气", "煤气", "供电", "供水", "供气",
        "物业费", "暖气", "空调费",
        # 通讯
        "话费", "宽带", "电信", "移动", "联通", "通信", "流量",
        # 医疗健康
        "医疗", "药店", "医院", "门诊", "体检", "医保", "挂号", "同仁堂",
        "益丰", "老百姓", "大参林", "叮当快药", "健康",
        # 教育
        "教育", "学费", "培训", "课程", "学而思", "新东方", "VIPKID", "猿辅导",
        "作业帮", "有道", "网易云课堂", "腾讯课堂",
        # 云服务
        "阿里云", "腾讯云", "华为云", "AWS", "Azure", "云服务器", "域名",
        # 订阅会员
        "会员", "订阅", "付费", "VIP",
        # 日常消费
        "支付宝-消费", "友宝", "家居", "顺丰", "京东快递", "菜鸟", "快递",
        # 加油/便利店
        "石化", "石油", "新宇", "加油",
    ],
    "投资理财": [
        # 银行理财
        "理财", "基金", "国债", "存款", "转账", "汇款", "招商银行", "银行",
        # 证券投资
        "证券", "股票", "长桥", "富途", "老虎", "华泰", "中信", "国泰",
        # 保险
        "保险", "保费", "平安", "中国人寿", "太平洋", "新华", "泰康",
    ],
    "其他": []
}

# 退货/退款关键词
REFUND_KEYWORDS = ["退货", "退款", "撤销"]

# 分期关键词
INSTALLMENT_KEYWORDS = ["消费分期", "分期付款"]


def run_gws(api_path: str, params: Dict) -> Dict:
    """调用 gws 命令"""
    cmd = ["gws"] + api_path.split() + ["--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"gws 命令失败: {result.stderr}")
    return json.loads(result.stdout)


def extract_email_body(payload: Dict) -> Optional[str]:
    """递归提取邮件HTML正文"""
    if 'body' in payload and payload['body'].get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    if 'parts' in payload:
        for part in payload['parts']:
            # 查找 text/html
            if part.get('mimeType') == 'text/html':
                if part.get('body', {}).get('data'):
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            
            # 递归查找
            if 'parts' in part:
                result = extract_email_body(part)
                if result:
                    return result
    
    return None


def parse_html_statement(html_text: str) -> Dict:
    """解析HTML格式的账单"""
    data = {
        "statement_date": None,
        "due_date": None,
        "credit_limit": None,
        "new_balance": None,
        "min_payment": None,
        "transactions": []
    }
    
    # 提取账单月份
    match = re.search(r"(\d{4})年(\d{2})月信用卡账单", html_text)
    if match:
        data["statement_date"] = f"{match.group(1)}年{match.group(2)}月"
    
    # 提取到期还款日
    match = re.search(r"最后还款日.*?(\d{2})月(\d{2})日", html_text, re.DOTALL)
    if match:
        # 推断年份
        month = int(match.group(1))
        current_year = datetime.now().year
        year = current_year if month >= datetime.now().month else current_year + 1
        data["due_date"] = f"{year}年{match.group(1)}月{match.group(2)}日"
    
    # 提取信用额度
    match = re.search(r"信用额度.*?&yen;\s*([\d,]+\.\d{2})", html_text, re.DOTALL)
    if match:
        data["credit_limit"] = float(match.group(1).replace(",", ""))
    
    # 提取本期应还金额
    match = re.search(r"本期应还金额.*?&yen;\s*([\d,]+\.\d{2})", html_text, re.DOTALL)
    if match:
        data["new_balance"] = float(match.group(1).replace(",", ""))
    
    # 提取最低还款额
    match = re.search(r"本期最低还款额.*?&yen;\s*([\d,]+\.\d{2})", html_text, re.DOTALL)
    if match:
        data["min_payment"] = float(match.group(1).replace(",", ""))
    
    # 提取交易记录
    # HTML中的交易记录在FONT标签中，格式：日期、日期、描述、金额、卡号、金额
    font_pattern = r'<FONT[^>]*>([^<]*)</FONT>'
    all_fonts = re.findall(font_pattern, html_text)
    
    i = 0
    while i < len(all_fonts) - 5:
        # 检查是否是交易记录行（第一个是4位数字日期MMDD）
        if re.match(r'^\d{4}$', all_fonts[i]):
            trans_date = all_fonts[i]
            post_date = all_fonts[i+1] if re.match(r'^\d{4}$', all_fonts[i+1]) else ""
            desc = all_fonts[i+2]
            amount = all_fonts[i+3].replace('&yen;&nbsp;', '').replace('¥ ', '').strip()
            card = all_fonts[i+4]
            
            # 验证金额和卡号格式
            if re.match(r'^[-\d,]+\.\d{2}$', amount) and re.match(r'^\d{4}$', card):
                data["transactions"].append({
                    "date": f"{trans_date[:2]}/{trans_date[2:]}",
                    "description": desc,
                    "amount": float(amount.replace(",", "")),
                    "card": card
                })
                i += 6
            else:
                i += 1
        else:
            i += 1
    
    return data


def identify_refund_status(description: str, amount: float) -> Tuple[bool, str]:
    """
    识别退货/退款状态
    返回: (是否退款, 状态标签)
    """
    # 检查是否为负金额（退款）
    if amount < 0:
        # 检查描述中是否包含退货关键词
        for keyword in REFUND_KEYWORDS:
            if keyword in description:
                return True, f" ⭐**[已退货]**" if "退货" in description else f" ⭐**[退款]**"
        # 负金额但没有明确关键词，也标记为退款
        return True, " ⭐**[退款]**"
    
    return False, ""


def identify_installment(description: str) -> Tuple[bool, Optional[Dict]]:
    """
    识别分期交易
    返回: (是否分期, 分期信息)
    """
    # 检查是否包含分期关键词
    is_installment = any(keyword in description for keyword in INSTALLMENT_KEYWORDS)
    
    if not is_installment:
        return False, None
    
    # 解析分期信息
    installment_info = {
        "is_installment": True,
        "original_desc": description,
        "period": None,
        "status": "正常还款中"
    }
    
    # 提取期数信息 (如: 第1/3期, 第19/24期)
    period_match = re.search(r'第(\d+)/(\d+)期', description)
    if period_match:
        current = int(period_match.group(1))
        total = int(period_match.group(2))
        remaining = total - current
        installment_info["period"] = f"第{current}/{total}期"
        installment_info["remaining"] = f"剩余{remaining}期"
    
    # 检查是否已退货
    if "退货" in description:
        installment_info["status"] = "已退货"
    
    return True, installment_info


def categorize_transactions(transactions: List[Dict]) -> Tuple[Dict[str, List[Dict]], Tuple[List[Dict], List[Dict]]]:
    """
    对交易进行分类，并单独提取分期交易
    返回: (分类后的交易, (全部分期, 有效分期))
    """
    categorized = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    installments = []
    
    for trans in transactions:
        desc = trans["description"]
        amount = trans["amount"]
        
        # 识别退货/退款状态
        is_refund, refund_label = identify_refund_status(desc, amount)
        trans["is_refund"] = is_refund
        trans["refund_label"] = refund_label
        
        # 识别分期
        is_installment, installment_info = identify_installment(desc)
        
        if is_installment:
            trans["installment_info"] = installment_info
            installments.append(trans)
            # 分期交易不加入普通分类
            continue
        
        # 投资理财类特殊处理：只匹配正向支出（购买理财），排除还款转账
        if amount > 0:
            matched = False
            for category, keywords in CATEGORY_KEYWORDS.items():
                if category == "其他":
                    continue
                if any(kw.lower() in desc.lower() for kw in keywords):
                    categorized[category].append(trans)
                    matched = True
                    break
            
            if not matched:
                categorized["其他"].append(trans)
        else:
            # 负金额（还款/退款）不计入消费分类
            categorized["其他"].append(trans)
    
    # 过滤掉存在退款的分期记录（原始分期+退款一起删除）
    active_installments = filter_cancelled_installments(installments)
    
    # 过滤普通交易中已退款的记录（支出+退款成对删除）
    categorized = filter_cancelled_regular_transactions(categorized)
    
    return categorized, (installments, active_installments)


def filter_cancelled_regular_transactions(categorized: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    过滤普通交易中已退款的记录
    规则：排除有对应退款的正向消费和退款本身（两者都不显示）
    """
    # 收集所有负向交易（退款）
    all_refunds = []
    for trans_list in categorized.values():
        for trans in trans_list:
            if trans.get("is_refund") and trans["amount"] < 0:
                all_refunds.append(trans)
    
    # 建立退款索引：(名称关键词, 金额绝对值)
    refund_index = {}
    for refund in all_refunds:
        desc = refund["description"]
        amount_key = abs(refund["amount"])
        
        name_match = re.search(r'支付宝[-]?(.+?)(?:\s|$)', desc)
        if name_match:
            name_key = name_match.group(1).strip()
        else:
            name_match = re.search(r'消费分期[-]支付宝[-](.+?)(?:\s+本金|\s+退货|$)', desc)
            if name_match:
                name_key = name_match.group(1).strip()
            else:
                name_key = desc.strip()[:10]
        
        refund_index[(name_key, amount_key)] = True
    
    # 过滤每个分类：排除有匹配退款的正向消费，也排除退款本身
    filtered = {cat: [] for cat in categorized.keys()}
    for cat, trans_list in categorized.items():
        for trans in trans_list:
            # 如果是退款，排除
            if trans.get("is_refund") and trans["amount"] < 0:
                # 但检查是否有对应的正向消费被排除，如果有就保留退款用于平衡
                # 这里简化处理：直接排除退款
                continue
            
            # 检查正向消费是否有匹配的退款
            if trans["amount"] > 0:
                desc = trans["description"]
                amount = trans["amount"]
                
                name_match = re.search(r'支付宝[-]?(.+?)(?:\s|$)', desc)
                if name_match:
                    name_key = name_match.group(1).strip()
                else:
                    name_match = re.search(r'消费分期[-]支付宝[-](.+?)(?:\s+本金|\s+退货|$)', desc)
                    if name_match:
                        name_key = name_match.group(1).strip()
                    else:
                        name_key = desc.strip()[:10]
                
                # 如果存在匹配的退款，跳过正向消费
                if (name_key, amount) in refund_index:
                    continue
            
            filtered[cat].append(trans)
    
    return filtered


def filter_cancelled_installments(installments: List[Dict]) -> List[Dict]:
    """
    过滤掉已取消/退货的分期记录
    原则：只有当本金的金额与某笔退货金额完全相同时，才排除该本金
    """
    if not installments:
        return []
    
    # 分离本金和退货记录
    principal_records = []
    refund_records = []
    
    for inst in installments:
        if "退货" in inst.get("description", ""):
            refund_records.append(inst)
        else:
            principal_records.append(inst)
    
    # 建立退货索引：按(商户名, 金额绝对值)
    # 格式: {(商户名, 金额绝对值): 退货记录}
    refund_by_key = {}
    for refund in refund_records:
        match = re.search(r'支付宝[-](.+?)(?:\s+退货|$)', refund["description"])
        if match:
            merchant = match.group(1).strip()
            amount_key = abs(refund["amount"])
            refund_by_key[(merchant, amount_key)] = refund
    
    # 过滤本金记录：排除有对应退货的（商户+金额完全匹配）
    filtered = []
    for principal in principal_records:
        match = re.search(r'支付宝[-](.+?)(?:\s+本金|\s+退货|$)', principal["description"])
        if match:
            merchant = match.group(1).strip()
            principal_amount = principal["amount"]
            
            # 检查是否有同商户同金额的退货记录
            if (merchant, principal_amount) in refund_by_key:
                continue  # 跳过：有对应退货（金额匹配）
        # 非支付宝分期 或 无对应退货，保留
        filtered.append(principal)
    
    return filtered


def generate_installment_summary(installments: List[Dict]) -> str:
    """生成分期账单统计表格"""
    if not installments:
        return ""
    
    report = "### 💰 分期账单统计\n\n"
    report += "| 类型 | 期数 | 本期金额 | 剩余待还 |\n"
    report += "|------|------|----------|----------|\n"
    
    total_amount = 0
    active_installments = []
    
    for inst in installments:
        info = inst.get("installment_info", {})
        if info.get("status") == "已退货":
            continue
        
        # 提取商户名称
        desc = inst["description"]
        merchant = desc.replace("消费分期-", "").replace("支付宝-", "").replace(" 本金", "").split(" 第")[0]
        if len(merchant) > 15:
            merchant = merchant[:12] + "..."
        
        period = info.get("period", "N/A")
        remaining = info.get("remaining", "N/A")
        amount = inst["amount"]
        
        report += f"| {merchant} | {period} | ¥ {amount:,.2f} | {remaining} |\n"
        total_amount += amount
        active_installments.append(inst)
    
    # 估算总剩余待还（粗略估计）
    estimated_remaining = sum(
        inst["amount"] * int(inst.get("installment_info", {}).get("remaining", "0").replace("剩余", "").replace("期", ""))
        for inst in active_installments
        if inst.get("installment_info", {}).get("remaining")
    )
    
    report += f"\n**分期总计**: 本期还款 ¥ {total_amount:,.2f} | 总剩余待还约 ¥ {estimated_remaining:,.0f}+\n\n"
    
    return report


def generate_installment_detail(installments: List[Dict]) -> str:
    """生成分期明细表格（排除已退货）"""
    # 过滤掉已退货的分期
    active_installments = [i for i in installments if i.get("installment_info", {}).get("status") != "已退货"]
    
    if not active_installments:
        return ""
    
    report = "### 💳 消费分期明细\n\n"
    report += "| 日期 | 描述 | 期数 | 金额 | 状态 | 卡号 |\n"
    report += "|------|------|------|------|------|------|\n"
    
    for inst in sorted(active_installments, key=lambda x: x['date']):
        info = inst.get("installment_info", {})
        desc = inst["description"]
        period = info.get("period", "N/A")
        status = info.get("status", "正常还款中")
        refund_label = inst.get("refund_label", "")
        
        report += f"| {inst['date']} | {desc}{refund_label} | {period} | ¥ {inst['amount']:,.2f} | {status} | {inst['card']} |\n"
    
    # 统计信息
    total_count = len(installments)
    active_count = len(active_installments)
    refunded_count = total_count - active_count
    total_amount = sum(i['amount'] for i in active_installments)
    
    report += f"\n**分期统计**: 总期数 {total_count}笔 | 正常还款中 {active_count}笔 | 已退货 {refunded_count}笔 | 本期分期金额: ¥ {total_amount:,.2f}\n\n"
    report += "---\n\n"
    
    return report


def generate_report(data: Dict, source_info: str) -> str:
    """生成 Markdown 分析报告"""
    report = f"# 招商银行信用卡账单分析\n\n"
    report += f"**数据来源**: {source_info}\n"
    report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**特殊说明**: 本期已单独拆分消费分期明细，便于跟踪分期还款情况\n\n"
    
    report += "---\n\n"
    
    # 账单概况
    report += "## 📅 账单概况\n\n"
    report += f"- **账单月份**: {data['statement_date'] or 'N/A'}\n"
    report += f"- **到期还款日**: {data['due_date'] or 'N/A'}\n"
    report += f"- **信用额度**: ¥ {data['credit_limit']:,.2f}\n" if data['credit_limit'] else "- **信用额度**: N/A\n"
    report += f"- **本期应还**: ¥ {data['new_balance']:,.2f}\n" if data['new_balance'] else "- **本期应还**: N/A\n"
    report += f"- **最低还款**: ¥ {data['min_payment']:,.2f}\n\n" if data['min_payment'] else "- **最低还款**: N/A\n\n"
    
    if data['credit_limit'] and data['new_balance']:
        usage_rate = (data['new_balance'] / data['credit_limit']) * 100
        report += f"- **额度使用率**: {usage_rate:.1f}%\n\n"
    
    # 按卡号统计
    card_stats = defaultdict(lambda: {"count": 0, "spending": 0, "payment": 0, "net": 0})
    
    for trans in data["transactions"]:
        card = trans["card"]
        amount = trans["amount"]
        card_stats[card]["count"] += 1
        if amount > 0:
            card_stats[card]["spending"] += amount
        else:
            card_stats[card]["payment"] += amount
        card_stats[card]["net"] += amount
    
    report += "### 💳 分卡消费统计\n\n"
    report += "| 卡号 | 交易笔数 | 消费金额 | 还款金额 | 净消费 |\n"
    report += "|------|----------|----------|----------|--------|\n"
    
    for card in sorted(card_stats.keys()):
        stats = card_stats[card]
        report += f"| {card} | {stats['count']} | ¥ {stats['spending']:,.2f} | ¥ {stats['payment']:,.2f} | ¥ {stats['net']:,.2f} |\n"
    
    total_spending = sum(t['amount'] for t in data['transactions'] if t['amount'] > 0)
    total_payment = sum(t['amount'] for t in data['transactions'] if t['amount'] < 0)
    
    report += f"\n**汇总**: 总消费 ¥ {total_spending:,.2f} | 总还款 ¥ {total_payment:,.2f} | 净消费 ¥ {total_spending + total_payment:,.2f}\n\n"
    
    # 分类和分期（过滤后的数据用于显示）
    categorized, (all_installments, active_installments) = categorize_transactions(data['transactions'])
    
    # 计算不含分期的总消费（基于过滤后的分类数据，但使用原始退款来平衡）
    # 非分期消费 = 过滤后的各类金额加总 + 原始退款金额（用来平衡）
    # 这样合计才能等于应还金额
    filtered_non_installment = sum(
        sum(t['amount'] for t in trans_list)
        for trans_list in categorized.values()
    )
    
    # 原始退款金额（用于平衡）
    original_refunds = sum(t['amount'] for t in data['transactions'] 
                          if t['amount'] < 0 and '消费分期' not in t['description'])
    non_installment_spending = filtered_non_installment - original_refunds
    
    # 分期统计（放在前面）- 只显示有效分期
    if active_installments:
        report += generate_installment_summary(active_installments)
    
    # 消费分类统计（按金额倒序，"其他"放最后）
    report += "## 💰 消费分类统计\n\n"
    report += "| 分类 | 笔数 | 金额 | 占比 |\n"
    report += "|------|------|------|------|\n"
    
    # 按金额倒序排序，"其他"放最后
    sorted_categories = sorted(
        [(cat, trans_list) for cat, trans_list in categorized.items() if trans_list and cat != "其他"],
        key=lambda x: sum(t['amount'] for t in x[1]),
        reverse=True
    )
    # 单独添加"其他"类
    if categorized.get("其他"):
        sorted_categories.append(("其他", categorized["其他"]))
    
    for category, trans_list in sorted_categories:
        count = len(trans_list)
        amount = sum(t['amount'] for t in trans_list)
        percentage = (amount / non_installment_spending * 100) if non_installment_spending > 0 else 0
        report += f"| {category} | {count} | ¥ {amount:,.2f} | {percentage:.1f}% |\n"
    
    # 添加分期行（使用有效分期）
    installment_amount = 0
    installment_count = 0
    if active_installments:
        installment_amount = sum(i['amount'] for i in active_installments)
        installment_count = len(active_installments)
        report += f"| 分期 | {installment_count} | ¥ {installment_amount:,.2f} | - |\n"
    
    # 添加合计行 - 使用账单应还金额确保一致
    total_all = data.get('new_balance', non_installment_spending + installment_amount)
    total_count = sum(len(trans_list) for _, trans_list in sorted_categories) + installment_count
    report += f"| **合计** | **{total_count}** | **¥ {total_all:,.2f}** | - |\n"
    
    # 详细交易记录
    report += "## 📝 交易明细\n\n"
    
    # 分期明细（放在最前面）- 只显示有效分期
    if active_installments:
        report += generate_installment_detail(active_installments)
    
    # 其他分类明细
    for category, trans_list in categorized.items():
        if not trans_list:
            continue
        
        report += f"### {category}\n\n"
        report += "| 日期 | 描述 | 金额 | 卡号 |\n"
        report += "|------|------|------|------|\n"
        
        for trans in sorted(trans_list, key=lambda x: x['date']):
            refund_label = trans.get('refund_label', '')
            report += f"| {trans['date']} | {trans['description']}{refund_label} | ¥ {trans['amount']:,.2f} | {trans['card']} |\n"
        
        report += "\n"
    
    # 消费建议
    report += "## 💡 消费建议\n\n"
    
    if data['credit_limit'] and data['new_balance']:
        usage_rate = (data['new_balance'] / data['credit_limit']) * 100
        if usage_rate > 80:
            report += "⚠️ **额度使用率较高**，建议及时还款，避免影响信用评分。\n\n"
    
    # 找出消费最多的分类（不含分期）
    max_category = max(categorized.items(), key=lambda x: sum(t['amount'] for t in x[1]) if x[1] else 0)
    if max_category[1]:
        cat_name = max_category[0]
        cat_amount = sum(t['amount'] for t in max_category[1])
        report += f"📊 本期 **{cat_name}** 消费最多，共 ¥ {cat_amount:,.2f}"
        if non_installment_spending > 0:
            report += f"，占总消费的 {(cat_amount/non_installment_spending*100):.1f}%"
        report += "\n\n"
    
    # 分期建议
    if active_installments:
        active_count = len(active_installments)
        if active_count > 0:
            report += f"💳 本期有 **{active_count}笔** 分期还款，注意合理安排资金。\n\n"
    
    return report


def save_to_obsidian(report: str, year_month: str) -> Path:
    """保存报告到 Obsidian"""
    CONFIG["obsidian_dir"].mkdir(parents=True, exist_ok=True)
    
    filename = f"{year_month}-信用卡账单分析.md"
    output_path = CONFIG["obsidian_dir"] / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {output_path}")
    return output_path


def main():
    """主流程"""
    try:
        # 1. 从 Gmail 获取最新账单
        print("🔍 查询 Gmail 中的招商银行账单...")
        
        result = run_gws("gmail users messages list", {
            "userId": "me",
            "q": CONFIG["gmail_query"],
            "maxResults": 1
        })
        
        messages = result.get("messages", [])
        if not messages:
            print("❌ 未找到账单邮件")
            return
        
        msg_id = messages[0]["id"]
        print(f"✅ 找到账单邮件: {msg_id}")
        
        # 2. 获取邮件详情
        msg_data = run_gws("gmail users messages get", {
            "userId": "me",
            "id": msg_id
        })
        
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        subject = headers.get('Subject', '')
        
        # 3. 提取HTML正文
        print("📧 提取邮件正文...")
        html_body = extract_email_body(msg_data['payload'])
        if not html_body:
            print("❌ 无法提取邮件正文")
            return
        
        # 4. 解析HTML账单
        print("📄 解析HTML账单...")
        data = parse_html_statement(html_body)
        source_info = "邮件正文（HTML）"
        
        print(f"✅ 解析完成: 找到 {len(data['transactions'])} 笔交易")
        
        if len(data['transactions']) == 0:
            print("⚠️  未找到交易记录，可能账单格式不支持")
            return
        
        # 5. 生成报告
        report = generate_report(data, source_info)
        
        # 6. 推断年月
        year_month = None
        match = re.search(r"(\d{4})年(\d{2})月", subject)
        if match:
            year_month = f"{match.group(1)}{match.group(2)}"
        elif data['statement_date']:
            match = re.search(r"(\d{4})年(\d{2})月", data['statement_date'])
            if match:
                year_month = f"{match.group(1)}{match.group(2)}"
        
        if not year_month:
            year_month = datetime.now().strftime("%Y%m")
        
        # 7. 保存到 Obsidian
        output_path = save_to_obsidian(report, year_month)
        
        # 8. 重新获取分类数据用于校验（因为 generate_report 内部的数据需要重新计算）
        categorized, (all_installments, active_installments) = categorize_transactions(data['transactions'])
        
        # 9. 结果校验
        validation_result = validate_report(data, (all_installments, active_installments), report)
        
        # 9. 统计信息
        categorized, (all_installments, active_installments) = categorize_transactions(data['transactions'])
        total_spending = sum(t['amount'] for t in data['transactions'] if t['amount'] > 0)
        refund_count = sum(1 for t in data['transactions'] if t.get('is_refund'))
        
        print("\n" + "="*60)
        print("✅ 账单分析完成！")
        print(f"📊 报告位置: {output_path}")
        print(f"📈 交易笔数: {len(data['transactions'])}")
        print(f"💰 总消费: ¥ {total_spending:,.2f}")
        if active_installments:
            print(f"💳 分期交易: {len(active_installments)}笔")
        if refund_count > 0:
            print(f"🔄 退货/退款: {refund_count}笔")
        
        # 输出校验结果
        if validation_result['passed']:
            print("✅ 校验通过")
        else:
            print("⚠️ 校验警告:")
            for warn in validation_result['warnings']:
                print(f"   - {warn}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def validate_report(data: Dict, installments: Tuple[List[Dict], List[Dict]], report: str) -> Dict:
    """
    校验报告结果的正确性
    返回: {'passed': bool, 'warnings': List[str]}
    """
    warnings = []
    
    # 1. 校验合计金额与应还金额一致
    expected_balance = data.get('new_balance', 0)
    if expected_balance > 0:
        # 从报告中提取合计金额
        import re
        total_match = re.search(r'\*\*合计\*\*.*?¥\s*([\d,]+\.\d{2})', report)
        if total_match:
            actual_total = float(total_match.group(1).replace(',', ''))
            if abs(actual_total - expected_balance) > 0.01:
                warnings.append(f"合计金额 ¥{actual_total:,.2f} 与应还金额 ¥{expected_balance:,.2f} 不一致")
    
    # 2. 校验消费分类统计中的分期金额与实际有效分期一致
    all_installments, active_installments = installments
    active_amount = sum(i['amount'] for i in active_installments)
    
    # 从报告中的分期行提取金额
    installment_match = re.search(r'\| 分期 \| \d+ \| ¥ ([\d,]+\.\d{2})', report)
    if installment_match:
        report_amount = float(installment_match.group(1).replace(',', ''))
        if abs(report_amount - active_amount) > 0.01:
            warnings.append(f"消费分类中的分期金额 ¥{report_amount:,.2f} 与明细 ¥{active_amount:,.2f} 不一致")
    
    # 3. 校验消费分期明细笔数
    installment_detail_count = len(re.findall(r'\| \d{2}/\d{2} \| 消费分期', report))
    if installment_detail_count != len(active_installments):
        warnings.append(f"消费分期明细 {installment_detail_count} 笔与实际 {len(active_installments)} 笔不一致")
    
    passed = len(warnings) == 0
    return {'passed': passed, 'warnings': warnings}


if __name__ == "__main__":
    main()
