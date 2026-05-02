import pandas as pd
from datetime import datetime, timedelta

def get_sorted_stock_list_v4():
    # 1. 获取当前环境日期
    try:
        target_date = context.current_dt.date()
    except NameError:
        target_date = datetime.now().date()

    # 2. 计算“一年前今日”
    try:
        one_year_ago = target_date.replace(year=target_date.year - 1)
    except ValueError:
        one_year_ago = target_date - timedelta(days=365)

    # 3. 获取所有股票基本信息
    df_all = get_all_securities(types=['stock'], date=target_date)
    df_all['start_date'] = pd.to_datetime(df_all['start_date']).dt.date

    # 4. 筛选：沪深主板
    # 加上了 '002'，这是 2000 年后深市主板（原中小板）的核心代码段
    main_board_prefixes = ('600', '601', '603', '605', '000', '001', '002', '003')
    main_board_condition = df_all.index.str.startswith(main_board_prefixes)
    not_new_condition = df_all['start_date'] <= one_year_ago
    
    candidate_df = df_all[main_board_condition & not_new_condition]
    candidate_stocks = candidate_df.index.tolist()

    # 5. 过滤 ST 股票
    st_data = get_extras('is_st', candidate_stocks, start_date=target_date, end_date=target_date)
    if not st_data.empty:
        non_st_stocks = [s for s in candidate_stocks if not st_data.iloc[0][s]]
    else:
        non_st_stocks = [s for s in candidate_stocks if 'ST' not in df_all.loc[s, 'display_name']]

    # 6. 过滤停牌股票
    price_df = get_price(non_st_stocks, end_date=target_date, count=1, fields=['paused'], panel=False)
    if not price_df.empty:
        final_codes = price_df[price_df['paused'] == 0]['code'].unique().tolist()
    else:
        final_codes = []

    # 7. 整理最终名单
    final_df = df_all.loc[final_codes, ['display_name', 'start_date']]
    final_df = final_df.sort_values(by='start_date', ascending=True)
    final_df.index.name = 'code'

    # === 【新增：保存 CSV 代码】 ===
    # 定义文件名，可以带上日期区分
    filename = f"main_board_stocks_{target_date}.csv"
    
    # encoding='utf_8_sig' 是关键，防止用 Excel 打开时中文变成乱码
    final_df.to_csv(filename, encoding='utf_8_sig')
    # ============================

    print("-" * 30)
    print(f"统计日期: {target_date}")
    print(f"符合条件股票总数: {len(final_df)} 支")
    print(f"结果已成功保存至: {filename}")
    print("-" * 30)
    
    return final_df

# 执行
res = get_sorted_stock_list_v4()