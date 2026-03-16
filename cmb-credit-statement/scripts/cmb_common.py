#!/usr/bin/env python3
"""
招商银行信用卡账单公共模块
提供消费分类、退款识别、分期识别等公共功能
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re

# ============ 消费分类关键词（基于描述智能匹配） ============
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
        "爱奇艺", "腾讯视频", "优酷", "芒果 TV", "B 站", "bilibili", "YouTube", "Netflix",
        # 游戏
        "游戏", "Steam", "Epic", "PlayStation", "Xbox", "Nintendo", "Switch", "腾讯游戏",
        "网易游戏", "米哈游",
        # 健身运动
        "健身", "瑜伽", "普拉提", "威尔士", "一兆韦德", "超级猩猩", "乐刻", "Keep",
        "体育", "游泳", "羽毛球", "网球", "乒乓球",
        # 音乐演出
        "音乐", "演唱会", "演出", "话剧", "歌剧", "音乐剧", "交响乐", "剧院",
        "网易云", "QQ 音乐", "酷狗", "酷我", "Apple Music", "Spotify",
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
        "支付宝 - 消费", "友宝", "家居", "顺丰", "京东快递", "菜鸟", "快递",
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

# 汇率配置（可定期更新）
EXCHANGE_RATES = {
    "CNY": 1.0,
    "USD": 7.25,  # 美元兑人民币
    "HKD": 0.93,  # 港币兑人民币
    "EUR": 7.85,  # 欧元兑人民币
    "JPY": 0.048, # 日元兑人民币
    "GBP": 9.15,  # 英镑兑人民币
}


def get_exchange_rate(currency: str) -> float:
    """获取货币汇率"""
    return EXCHANGE_RATES.get(currency.upper(), 1.0)


def convert_to_cny(amount: float, currency: str) -> float:
    """将外币金额转换为 CNY"""
    rate = get_exchange_rate(currency)
    return amount * rate


def identify_refund_status(description: str, amount: float) -> Tuple[bool, str]:
    """
    识别退货/退款状态
    返回：(是否退款，状态标签)
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
    返回：(是否分期，分期信息)
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

    # 提取期数信息 (如：第 1/3 期，第 19/24 期)
    period_match = re.search(r'第 (\d+)/(\d+) 期', description)
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


def categorize_transaction(description: str, amount: float) -> str:
    """
    对单笔交易进行分类
    返回：分类名称
    """
    # 负金额（还款/退款）归为"其他"
    if amount < 0:
        return "其他"

    # 投资理财类特殊处理：只匹配正向支出（购买理财），排除还款转账
    if amount > 0:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if category == "其他":
                continue
            if any(kw.lower() in description.lower() for kw in keywords):
                return category

    return "其他"


def categorize_transactions(transactions: List[Dict]) -> Tuple[Dict[str, List[Dict]], Tuple[List[Dict], List[Dict]]]:
    """
    对交易进行分类，并单独提取分期交易
    返回：(分类后的交易，(全部分期，有效分期))
    """
    categorized = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    installments = []

    for trans in transactions:
        desc = trans.get("description", trans.get("merchant", ""))
        amount = trans.get("amount", 0)

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

        # 分类处理
        category = categorize_transaction(desc, amount)
        categorized[category].append(trans)

    # 过滤掉存在退款的分期记录（原始分期 + 退款一起删除）
    active_installments = filter_cancelled_installments(installments)

    # 过滤普通交易中已退款的记录（支出 + 退款成对删除）
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
            if trans.get("is_refund") and trans.get("amount", 0) < 0:
                all_refunds.append(trans)

    # 建立退款索引：(名称关键词，金额绝对值)
    refund_index = {}
    for refund in all_refunds:
        desc = refund.get("description", refund.get("merchant", ""))
        amount_key = abs(refund.get("amount", 0))

        name_match = re.search(r'支付宝 [-]?(.+?)(?:\s|$)', desc)
        if name_match:
            name_key = name_match.group(1).strip()
        else:
            name_match = re.search(r'消费分期 [-] 支付宝 [-](.+?)(?:\s+本金|\s+退货|$)', desc)
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
            if trans.get("is_refund") and trans.get("amount", 0) < 0:
                continue

            # 检查正向消费是否有匹配的退款
            if trans.get("amount", 0) > 0:
                desc = trans.get("description", trans.get("merchant", ""))
                amount = trans.get("amount", 0)

                name_match = re.search(r'支付宝 [-]?(.+?)(?:\s|$)', desc)
                if name_match:
                    name_key = name_match.group(1).strip()
                else:
                    name_match = re.search(r'消费分期 [-] 支付宝 [-](.+?)(?:\s+本金|\s+退货|$)', desc)
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
        desc = inst.get("description", "")
        if "退货" in desc:
            refund_records.append(inst)
        else:
            principal_records.append(inst)

    # 建立退货索引：按 (商户名，金额绝对值)
    refund_by_key = {}
    for refund in refund_records:
        match = re.search(r'支付宝 [-](.+?)(?:\s+退货|$)', refund.get("description", ""))
        if match:
            merchant = match.group(1).strip()
            amount_key = abs(refund.get("amount", 0))
            refund_by_key[(merchant, amount_key)] = refund

    # 过滤本金记录：排除有对应退货的（商户 + 金额完全匹配）
    filtered = []
    for principal in principal_records:
        match = re.search(r'支付宝 [-](.+?)(?:\s+本金|\s+退货|$)', principal.get("description", ""))
        if match:
            merchant = match.group(1).strip()
            principal_amount = principal.get("amount", 0)

            # 检查是否有同商户同金额的退货记录
            if (merchant, principal_amount) in refund_by_key:
                continue
        filtered.append(principal)

    return filtered


def generate_dataview_sql(table_name: str, query_type: str) -> str:
    """
    生成 Dataview 查询 SQL
    table_name: 表名（如 'cmb_transactions'）
    query_type: 查询类型 ('summary', 'by_category', 'by_card')
    """
    if query_type == "summary":
        return f"""```dataview
TABLE
    sum(amount) as 总消费，
    sum(filter(amount, amount < 0)) as 总还款，
    sum(filter(amount, amount > 0)) as 净消费
FROM {table_name}
```"""

    elif query_type == "by_category":
        return f"""```dataview
TABLE
    rows.length as 笔数，
    sum(amount) as 金额
FROM {table_name}
GROUP BY category
SORT sum(amount) DESC
```"""

    elif query_type == "by_card":
        return f"""```dataview
TABLE
    rows.length as 交易笔数，
    sum(filter(amount, amount > 0)) as 消费金额，
    sum(filter(amount, amount < 0)) as 还款金额，
    sum(amount) as 净消费
FROM {table_name}
GROUP BY card
```"""

    return ""


def format_currency(amount: float, currency: str = "CNY") -> str:
    """格式化货币显示"""
    if currency == "CNY":
        return f"¥ {amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"
