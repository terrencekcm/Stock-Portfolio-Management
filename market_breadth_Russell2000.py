import os
import pandas as pd
import yfinance as yf

def get_russell2000_tickers():
    russell_file = os.path.join('data', 'russell2000.csv')
    if not os.path.exists(russell_file):
        print(f"❌ 找不到檔案: {russell_file}")
        return []
        
    try:
        df = pd.read_csv(russell_file)
        target_col = None
        for col in df.columns:
            if 'ticker' in str(col).lower() or 'symbol' in str(col).lower():
                target_col = col
                break
                
        if target_col is None:
            target_col = df.columns[0]
            
        raw_tickers = df[target_col].dropna().astype(str).tolist()
        cleaned = [t.strip().upper().replace('.', '-') for t in raw_tickers if t.strip()]
        print(f"✅ 成功載入 data/russell2000.csv: {len(cleaned)} 隻股票")
        return cleaned
    except Exception as e:
        print(f"❌ 讀取 {russell_file} 失敗: {e}")
        return []

def run_python2_smallcap(start_date, end_date):
    tickers = get_russell2000_tickers()
    if not tickers:
        print("無法取得 Russell 2000 股票清單，程序終止。")
        return
        
    nh_set, nl_set = set(), set()
    print(f"\n[Python 2] 開始計算 Russell 2000 (共 {len(tickers)} 隻股票)...")
    
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
    
    print("\n========== [Python 2: Russell 2000 中小盤] 月度報告 ==========")
    print(f"範圍: {start_date} ~ {end_date}")
    print(f"Dynamic NH (新高): {nh_count} | Dynamic NL (新低): {nl_count}")
    print(f"淨新高 (Net NH): {net_nh} | NH Ratio: {nh_ratio:.1%}")

if __name__ == '__main__':
    run_python2_smallcap('2026-07-01', '2026-07-31')
