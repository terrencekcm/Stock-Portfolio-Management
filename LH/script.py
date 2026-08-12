import pandas as pd
import yfinance as yf

def get_monthly_market_breadth(start_date, end_date):
    # 1. 取得 S&P 500 成分股清單 (可自行更換為其他股票池)
    sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = pd.read_html(sp500_url)[0]['Symbol'].tolist()
    
    monthly_nh_set = set() # 自動去重的 Set 結構
    monthly_nl_set = set()
    
    print(f"正在計算 {start_date} 至 {end_date} 的月度不重複新高/新低狀態...")
    
    for i, ticker in enumerate(tickers):
        symbol = ticker.replace('.', '-')
        try:
            # 拉取包含過去 1 年的每日 K 線數據
            df = yf.Ticker(symbol).history(period='1y')
            if df.empty:
                continue
                
            # 切出目標月份的數據
            month_df = df.loc[start_date:end_date]
            if month_df.empty:
                continue
            
            # 當月最高的價格與最低的價格
            month_max_high = month_df['High'].max()
            month_min_low = month_df['Low'].min()
            
            # 計算當月之前的 52 週最高價與最低價 (約 252 個交易日)
            prior_data = df.loc[:start_date]
            prior_52w_high = prior_data['High'].tail(252).max()
            prior_52w_low = prior_data['Low'].tail(252).min()
            
            # 判斷當月是否曾創過 52 週新高 / 新低
            if month_max_high >= prior_52w_high:
                monthly_nh_set.add(symbol)
            if month_min_low <= prior_52w_low:
                monthly_nl_set.add(symbol)
                
        except Exception as e:
            continue
            
    nh_count = len(monthly_nh_set)
    nl_count = len(monthly_nl_set)
    
    # 計算月度廣度指標
    net_nh = nh_count - nl_count
    nh_ratio = nh_count / (nh_count + nl_count) if (nh_count + nl_count) > 0 else 0
    
    # 輸出每月狀態評估結果
    print("\n========== 每月狀態評估報告 ==========")
    print(f"月份範圍: {start_date} ~ {end_date}")
    print(f"不重複 Monthly Dynamic NH (新高家數): {nh_count}")
    print(f"不重複 Monthly Dynamic NL (新低家數): {nl_count}")
    print(f"淨新高家數 (Net NH): {net_nh}")
    print(f"新高佔比 (NH Ratio): {nh_ratio:.1%}")
    
    # 自動給出月度狀態判定
    if nh_ratio >= 0.70:
        print("🟢 月度狀態：強勢多頭擴張 (Bullish Market Regime)")
    elif nh_ratio >= 0.45:
        print("🟡 月度狀態：結構分化 / 橫盤震盪 (Divergence / Consolidation)")
    else:
        print("🔴 月度狀態：弱勢空頭 / 頂部背馳警訊 (Bearish Warning)")

# ==================== 使用方法 ====================
# 每月月尾執行一次，填入當月的開頭與結尾日期：
get_monthly_market_breadth(start_date='2026-07-01', end_date='2026-07-31')script.py
