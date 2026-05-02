#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from datetime import datetime

# ================= 配置区 =================
TARGET_DATE = '2026-04-30'  
WEIGHT_125 = 0.65
WEIGHT_250 = 0.35
THRESHOLD = 0.7
# ==========================================

def get_trend_score(stock, end_date):
    """计算单个股票的趋势加权得分"""
    # 取数据，多取55天用于计算MA55
    hist = get_price(stock, end_date=end_date, count=250 + 55, fields=['close'])
    if len(hist) < 305:
        return None
    
    ma55 = hist['close'].rolling(window=55).mean()
    closes = hist['close'].iloc[-250:]
    ma_values = ma55.iloc[-250:]
    
    below_mask = closes < ma_values
    ratio_125 = below_mask.iloc[-125:].mean()
    ratio_250 = below_mask.mean()
    
    score = (ratio_125 * WEIGHT_125) + (ratio_250 * WEIGHT_250)
    return score

# 1. 获取初步名单
all_stocks = get_all_securities(['stock'], date=TARGET_DATE).index.tolist()

results = []
print(f"开始分析，原始总数：{len(all_stocks)} 只")

for stock in all_stocks:
    try:
        # --- 过滤逻辑 A: 板块过滤 (排除创业板和科创板) ---
        # 300, 301 为创业板；688 为科创板
        if stock.startswith(('300', '301', '688')):
            continue

        # 获取股票详细信息
        info = get_security_info(stock)
        name = info.display_name
        
        # --- 过滤逻辑 B: 过滤 ST 股 ---
        if 'ST' in name or '*' in name:
            continue

        # --- 过滤逻辑 C: 过滤新股 (上市需满1年，否则数据不够算 MA55) ---
        # 计算上市天数
        target_dt = datetime.strptime(TARGET_DATE, '%Y-%m-%d').date()
        if (target_dt - info.start_date).days < 365:
            continue

        # --- 过滤逻辑 D: 过滤停牌 ---
        # 获取当天行情，看是否停牌
        paused_info = get_price(stock, end_date=TARGET_DATE, count=1, fields=['paused'])
        if paused_info['paused'][0] == 1:
            continue

        # --- 执行评分逻辑 ---
        score = get_trend_score(stock, TARGET_DATE)
        
        if score and score > THRESHOLD:
            results.append({
                '股票代码': stock,
                '股票名称': name,
                '趋势得分': round(score, 4),
                '当前价格': get_price(stock, end_date=TARGET_DATE, count=1, fields=['close']).close[0]
            })
            
    except Exception as e:
        # 遇到报错自动跳过，保证程序不中断
        continue

# 2. 转换并排序
df_res = pd.DataFrame(results).sort_values(by='趋势得分', ascending=False)

# 3. 输出与保存
print(f"\n--- 筛选完成：符合条件的“弱势主板股”共 {len(df_res)} 只 ---")
print(df_res.head(20))

# 建议：云端环境如果 to_excel 报错，请优先使用 to_csv
try:
    df_res.to_csv('合兆量化_选股结果.csv', encoding='utf_8_sig')
    print("\n文件已保存为：合兆量化_选股结果.csv")
except:
    print("\n文件保存失败，请检查环境权限。")


# In[2]:


import pandas as pd
from datetime import datetime

# ================= 配置区 =================
TARGET_DATE = '2026-04-30'  # 选股目标日期
SHORT_WINDOW = 60           # 短期均线
LONG_WINDOW = 200           # 长期均线
# ==========================================

def is_downward_trend(stock, end_date):
    """判断股票是否处于下跌趋势（MA60 < MA200）"""
    # 为了算出200日均线，我们需要取至少200天的数据
    # 建议多取一天以防万一
    hist = get_price(stock, end_date=end_date, count=LONG_WINDOW, fields=['close'])
    
    # 如果上市时间太短，数据量不足200条，直接返回False（剔除新股）
    if len(hist) < LONG_WINDOW:
        return False
    
    # 计算当前时刻的均线值
    ma60 = hist['close'].iloc[-SHORT_WINDOW:].mean()
    ma200 = hist['close'].mean() # 因为刚好取了200天，mean()就是MA200
    
    # 判断逻辑：短线在长线之下
    return ma60 < ma200

# 1. 获取全市场股票名单
all_stocks = get_all_securities(['stock'], date=TARGET_DATE).index.tolist()

results = []
print(f"开始扫描主板股票趋势 ({TARGET_DATE})...")

for stock in all_stocks:
    try:
        # --- 过滤逻辑：只选主板 ---
        # 排除创业板(300, 301)和科创板(688)
        if stock.startswith(('300', '301', '688')):
            continue
            
        # 获取信息用于过滤 ST 和 停牌
        info = get_security_info(stock)
        
        # 过滤 ST
        if 'ST' in info.display_name or '*' in info.display_name:
            continue
            
        # 过滤停牌
        paused_info = get_price(stock, end_date=TARGET_DATE, count=1, fields=['paused'])
        if paused_info['paused'][0] == 1:
            continue
            
        # --- 策略核心判断 ---
        if is_downward_trend(stock, TARGET_DATE):
            # 获取当前价格
            current_price = get_price(stock, end_date=TARGET_DATE, count=1, fields=['close']).close[0]
            
            results.append({
                '股票代码': stock,
                '股票名称': info.display_name,
                '当前价格': current_price,
                '判定日期': TARGET_DATE,
                '趋势状态': 'MA60 < MA200 (下跌趋势)'
            })
            
    except:
        continue

# 2. 生成结果表格
df_res = pd.DataFrame(results)

# 3. 导出为 CSV
filename = f'main_board_downward_trend_{TARGET_DATE}.csv'
df_res.to_csv(filename, encoding='utf_8_sig', index=False)

print(f"\n--- 任务完成 ---")
print(f"共发现 {len(df_res)} 只符合主板下跌趋势的股票。")
print(f"结果已保存至: {filename}")


# In[ ]:




