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

def get_index_return(symbol, start_date, end_date):
    try:
        idx_df = yf.Ticker(symbol).history(period='2y')
        period_df = idx_df.loc[start_date:end_date]
        if period_df.empty:
            return None
        open_price = period_df['Open'].iloc[0]
        close_price = period_df['Close'].iloc[-1]
        return (close_price - open_price) / open_price
    except Exception:
        return None

def run_python2_smallcap(start_date, end_date):
    tickers = get_russell2000_tickers()
    if not tickers:
        print("無法取得 Russell 2000 股票清單，程序終止。")
        return
        
    # 計算 Russell 2000 指數當期漲跌幅
    rut_ret = get_index_return('^RUT', start_date, end_date)
    
    dynamic_nh_set = set()
    dynamic_nl_set = set()
    close_nh_set = set()
    close_nl_set = set()
    
    print(f"\n[Python 2] 開始掃描 Russell 2000 ({start_date} ~ {end_date})...")
    
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period='2y')
            if df.empty: continue
                
            month_df = df.loc[start_date:end_date]
            if month_df.empty: continue
            
            # 1. 取得當期最高價、最低價與期末收盤價
            month_high = month_df['High'].max()
            month_low = month_df['Low'].min()
            month_end_close = month_df['Close'].iloc[-1]
            
            # 2. 取得評估期之前的 52 週 (252 個交易日) 高低點
            prior_data = df[df.index < month_df.index[0]]
            if len(prior_data) < 20: continue
            
            prior_52w_high = prior_data['High'].tail(252).max()
            prior_52w_low = prior_data['Low'].tail(252).min()
            
            # 3. 判定 Dynamic (嘗試攻堅)
            if month_high >= prior_52w_high:
                dynamic_nh_set.add(ticker)
            if month_low <= prior_52w_low:
                dynamic_nl_set.add(ticker)
                
            # 4. 判定 Close (成功站穩)
            if month_end_close >= prior_52w_high:
                close_nh_set.add(ticker)
            if month_end_close <= prior_52w_low:
                close_nl_set.add(ticker)
                
        except Exception:
            continue
            
    # 統計數量
    d_nh = len(dynamic_nh_set)
    d_nl = len(dynamic_nl_set)
    c_nh = len(close_nh_set)
    
    net_nh = d_nh - d_nl
    nh_ratio = d_nh / (d_nh + d_nl) if (d_nh + d_nl) > 0 else 0.0
    retention_rate = (c_nh / d_nh * 100) if d_nh > 0 else 0.0
    
    rut_str = f"{rut_ret:+.2%}" if rut_ret is not None else "N/A"
    
    # 格式化輸出報告
    print("\n==================================================")
    print(" [Python 2: 中小盤股 (Russell 2000)] 廣度報告")
    print("==================================================")
    print(f"範圍: {start_date} ~ {end_date}")
    print(f"Russell 2000當月漲跌幅: {rut_str}")
    print("--------------------------------------------------")
    print(f"Dynamic NH (新高): {d_nh} | Dynamic NL (新低): {d_nl}")
    print(f"淨新高 (Net NH): {net_nh} | NH Ratio: {nh_ratio:.1%}")
    print("--------------------------------------------------")
    print(f"Dynamic NH (嘗試攻堅家數): {d_nh}")
    print(f"Close NH   (成功站穩家數): {c_nh}")
    print(f"突破留存率 (Retention Rate): {retention_rate:.1f}%")
    print("==================================================\n")

if __name__ == '__main__':
    run_python2_smallcap('2026-08-10', '2026-08-14')
