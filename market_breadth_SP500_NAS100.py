import os
import pandas as pd
import yfinance as yf

def load_local_tickers(filepath):
    if not os.path.exists(filepath):
        print(f"❌ 找不到檔案: {filepath}")
        return []
    
    try:
        df = pd.read_csv(filepath)
        # 自動搜尋包含 ticker 或 symbol 的欄位 (不區分大小寫)
        target_col = None
        for col in df.columns:
            if 'ticker' in str(col).lower() or 'symbol' in str(col).lower():
                target_col = col
                break
        
        if target_col is None:
            target_col = df.columns[0] # 若未匹配到，預設取第一欄
            
        raw_tickers = df[target_col].dropna().astype(str).tolist()
        
        # 清理字串，並替換點號為 Dash (如 BRK.B -> BRK-B)
        cleaned = [t.strip().upper().replace('.', '-') for t in raw_tickers if t.strip()]
        return cleaned
    except Exception as e:
        print(f"❌ 讀取 {filepath} 失敗: {e}")
        return []

def get_combined_largecap_tickers():
    sp500_file = os.path.join('data', 'sp500.csv')
    nasdaq100_file = os.path.join('data', 'nasdaq100.csv')
    
    sp500_list = load_local_tickers(sp500_file)
    nasdaq100_list = load_local_tickers(nasdaq100_file)
    
    print(f"✅ 成功載入 data/sp500.csv: {len(sp500_list)} 隻")
    print(f"✅ 成功載入 data/nasdaq100.csv: {len(nasdaq100_list)} 隻")
    
    combined_set = set(sp500_list).union(set(nasdaq100_list))
    print(f"✅ 合併並去重後總數: {len(combined_set)} 隻股票")
    return list(combined_set)

def run_python1_largecap(start_date, end_date):
    tickers = get_combined_largecap_tickers()
    if not tickers:
        print("無法取得股票清單，程序終止。")
        return
        
    nh_set, nl_set = set(), set()
    print(f"\n[Python 1] 開始計算 S&P 500 + Nasdaq 100 (共 {len(tickers)} 隻股票)...")
    
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period='1y')
            if df.empty: continue
                
            month_df = df.loc[start_date:end_date]
            if month_df.empty: continue
            
            month_high = month_df['High'].max()
            month_low = month_df['Low'].min()
            
            prior_data = df.loc[:start_date]
            prior_52w_high = prior_data['High'].tail(252).max()
            prior_52w_low = prior_data['Low'].tail(252).min()
            
            if month_high >= prior_52w_high:
                nh_set.add(ticker)
            if month_low <= prior_52w_low:
                nl_set.add(ticker)
        except Exception:
            continue
            
    nh_count, nl_count = len(nh_set), len(nl_set)
    net_nh = nh_count - nl_count
    nh_ratio = nh_count / (nh_count + nl_count) if (nh_count + nl_count) > 0 else 0
    
    print("\n========== [Python 1: 大型股+科技股] 月度報告 ==========")
    print(f"範圍: {start_date} ~ {end_date}")
    print(f"Dynamic NH (新高): {nh_count} | Dynamic NL (新低): {nl_count}")
    print(f"淨新高 (Net NH): {net_nh} | NH Ratio: {nh_ratio:.1%}")

if __name__ == '__main__':
    run_python1_largecap('2026-07-01', '2026-07-31')
