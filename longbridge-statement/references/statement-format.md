# Statement Format Reference

## Email Structure

**From**: `noreply@longbridge.hk`  
**Subject**: Contains "日结单" (Daily Statement)  
**Attachment**: `statement-daily-YYYYMMDD-H########.pdf` (password-protected)

## PDF Structure

### Page 1: Account Overview & Positions

#### Account Summary Section
```
账⼾总览 (HKD)
资⾦余额 | 市值 | 总资产 | 融资⾦额 | 初始保证⾦要求 | 维持保证⾦要求 | 融券平仓担保⾦ | 应追缴保证⾦ | 含贷权益价值
```

#### Cash Details Section
```
资⾦详情
币种 | 期初资⾦余额 | 变更⾦额 | 期末资⾦余额 | 已交收现⾦ | 待交收现⾦ | 应计利息 | 参考汇率 | 期末资⾦余额 (HKD)
```

#### Position Details Section
```
投资组合详情
项⽬ | 期初持仓 | 变更数量 | 期末持仓 | 价格 | 持仓市值 | 成本 | 浮动盈亏 | 维持保证⾦⽐例 | 维持保证⾦
```

**Stock Format**:
```
SYMBOL 公司名称 数量 变更 期末数量 价格 市值 成本 盈亏 保证金比例 保证金
```

Example:
```
AMZN 亚⻢逊 105.00 0.00 105.00 218.94 22,988.70 223.053 -431.87 25.00% 5,747.18
```

### Page 2: Transactions & Disclaimers

#### Transaction Details
```
其他资⾦出⼊明细
发⽣⽇期 | 类型 | 备注 | ⾦额
```

Transaction types:
- `现⾦分红` - Cash dividend
- `公司⾏动其他费⽤` - Corporate action fees
- `利息` - Interest
- `转账` - Transfer

## Data Extraction Patterns

### Account Summary
```regex
资⾦余额\s+([\d,\.]+)
市值\s+([\d,\.]+)
总资产\s+([\d,\.]+)
融资⾦额\s+([\d,\.]+)
含贷权益价值\s+([\d,\.]+)
```

### Stock Positions
```regex
([A-Z]+)\s+([^\d]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([-\d,\.]+)
```

Groups:
1. Symbol (e.g., AMZN)
2. Name (e.g., 亚⻢逊)
3. Quantity
4. Change
5. Final quantity
6. Price
7. Market value
8. Cost
9. P&L

### Fund Positions
```regex
(HK\d+)\s+([^\d]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([-\d,\.]+)
```

### Date Extraction
```regex
(\d{4})\.(\d{2})\.(\d{2})
```

## Risk Indicators

### Position Risk Levels
- **Low Risk (🟢)**: P&L > -10%
- **Medium Risk (🟡)**: -30% < P&L ≤ -10%
- **High Risk (🔴)**: P&L ≤ -30%

### Account Risk Levels
- **Cash Ratio**:
  - Healthy: ≥ 15%
  - Warning: 10-15%
  - Critical: < 10%

- **Margin Usage**:
  - Safe: < 30% of limit
  - Warning: 30-50%
  - Critical: > 50%

### Concentration Risk
- Single position > 30% of portfolio: High concentration
- Top 3 positions > 60%: Moderate concentration
- Sector concentration > 40%: Sector risk

## Currency Codes

- **HKD**: Hong Kong Dollar
- **USD**: US Dollar
- **CNY**: Chinese Yuan

## Market Codes

- **US**: US stocks (AMZN, GOOGL, etc.)
- **HK**: Hong Kong stocks (HK0000...)
- **CN**: China A-shares

## Common Symbols

### US Stocks
- AMZN - Amazon
- GOOGL - Google (Class A)
- BABA - Alibaba
- LI - Li Auto
- TSLA - Tesla

### ETFs
- QQQ - Invesco QQQ (Nasdaq 100)
- SPY - SPDR S&P 500
- PFF - iShares Preferred Stock
- TSLL - Direxion 2x Tesla

### Funds
- HK0000478872 - 高腾微财货币基金 (Money Market Fund HKD)
- HK0000584737 - 高腾微基金 (Money Market Fund USD)
- HK0000720752 - 中国平安精选投资基金 (Ping An Fund)

## Parsing Tips

1. **Handle Unicode**: Statement uses CJK characters (⾦, ⾏, etc.)
2. **Number Format**: Uses commas as thousands separator (1,234.56)
3. **Negative Numbers**: May use minus sign or parentheses
4. **Multi-line Entries**: Some names span multiple lines
5. **Table Detection**: Use pdfplumber's table extraction for structured data
