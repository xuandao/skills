#!/bin/bash
# 批量处理所有月结单 - 使用完整版分析

MONTHS=("202501" "202502" "202503" "202504" "202505" "202506" "202507" "202508" "202509" "202510" "202511" "202512" "202601")

echo "=== 长桥证券月结单批量完整分析 ==="
echo ""
echo "目标月份: ${MONTHS[@]}"
echo "⚠️  这将需要 30-40 分钟，请耐心等待..."
echo ""

# 临时修改月结单脚本，让它处理指定月份
for month in "${MONTHS[@]}"; do
    echo "[处理 $month]"
    
    # 修改 Gmail 查询，搜索特定月份
    python3 << PYTHON
import sys
sys.path.insert(0, '.')
exec(open('longbridge-monthly-analysis.py').read().replace(
    'maxResults": 1',
    'maxResults": 50'
).replace(
    'get_latest_statement()',
    'get_statement_by_month("$month")'
))
PYTHON
    
    if [ $? -eq 0 ]; then
        echo "  ✅ 成功"
    else
        echo "  ❌ 失败"
    fi
    echo ""
done

echo "✅ 批量处理完成！"
