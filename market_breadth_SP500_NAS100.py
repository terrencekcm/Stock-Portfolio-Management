import os
import argparse
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

def parse_dates():
    parser = argparse.ArgumentParser(description="LargeCap & Tech Market Breadth Analyzer")
    parser.add_argument('--start', type=str, help="Start Date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, help="End Date (YYYY-MM-DD)")
    parser.add_argument('--mode', type=str, choices=['week', 'month'], default='week', help="Auto date mode if start/end not provided")
    args = parser.parse_args()

    if args.start and args.end:
        return args.start, args.end

    today = datetime.now()
    if args.mode == 'week':
        offset = (today.weekday() - 4) % 7
        if offset == 0:
            offset = 7
        last_friday = today - timedelta(days=offset)
        last_monday = last_friday - timedelta(days=4)
        return last_monday.strftime('%Y-%m-%d'), last_friday.strftime('%Y-%m-%d')
    else:
        first_this_month = today.replace(day=1)
        last_last_month = first_this_month - timedelta(days=1)
        first_last_month = last_last_month.replace(day=1)
        return first_last_month.strftime('%Y-%m-%d'), last_last_month.strftime('%Y-%m-%d')

def load_local_tickers(filepath):
    if not os.path.exists(filepath):
        print(f"❌ 找不到檔案: {filepath}")
        return []
    try:
        df = pd.read_csv(filepath)
        target_col = next((col for col in df.columns if 'ticker' in str(col).lower() or 'symbol' in str(col).lower()), df.columns[0])
        raw_tickers = df[target_col].dropna().astype(str).tolist()
        return [t.strip().upper().replace('.', '-') for t in raw_tickers if t.strip()]
    except Exception as e:
        print(f"❌ 讀取 {filepath} 失敗: {e}")
        return []

def get_combined_largecap_tickers():
    sp500_list = load_local_tickers(os.path.join('data', 'sp500.csv'))
    nasdaq100_list = load_local_tickers(os.path.join('data', 'nasdaq100.csv'))
    combined_set = set(sp500_list).union(set(nasdaq100_list))
    print(f"✅ 成功載入成分股 (S&P500: {len(sp500_list)} 隻, Nasdaq100: {len(nasdaq100_list)} 隻)")
    print(f"✅ 去重後計算總數: {len(combined_set)} 隻股票")
    return list(combined_set)

def get_index_return(symbol, start_date, end_date):
    try:
        idx_df = yf.Ticker(symbol).history(period='2y')
        period_df = idx_df.loc[start_date:end_date]
        if period_df.empty:
            return None
        return (period_df['Close'].iloc[-1] - period_df['Open'].iloc[0]) / period_df['Open'].iloc[0]
    except Exception:
        return None

def run_python1_largecap(start_date, end_date):
    tickers = get_combined_largecap_tickers()
    if not tickers:
        print("無法取得股票清單，程序終止。")
        return
        
    spx_ret = get_index_return('^GSPC', start_date, end_date)
    ndx_ret = get_index_return('^NDX', start_date, end_date)
    
    dynamic_nh_set, dynamic_nl_set = set(), set()
    close_nh_set, close_nl_set = set(), set()
    
    print(f"\n[Python 1] 開始掃描 S&P 500 + Nasdaq 100 ({start_date} ~ {end_date})...")
    
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period='2y')
            if df.empty: continue
                
            period_df = df.loc[start_date:end_date]
            if period_df.empty: continue
            
            p_high = period_df['High'].max()
            p_low = period_df['Low'].min()
            p_end_close = period_df['Close'].iloc[-1]
            
            prior_data = df[df.index < period_df.index[0]]
            if len(prior_data) < 20: continue
            
            prior_52w_high = prior_data['High'].tail(252).max()
            prior_52w_low = prior_data['Low'].tail(252).min()
            
            if p_high >= prior_52w_high:
                dynamic_nh_set.add(ticker)
            if p_low <= prior_52w_low:
                dynamic_nl_set.add(ticker)
                
            if p_end_close >= prior_52w_high:
                close_nh_set.add(ticker)
            if p_end_close <= prior_52w_low:
                close_nl_set.add(ticker)
        except Exception:
            continue
            
    d_nh, d_nl, c_nh = len(dynamic_nh_set), len(dynamic_nl_set), len(close_nh_set)
    net_nh = d_nh - d_nl
    nh_ratio = d_nh / (d_nh + d_nl) if (d_nh + d_nl) > 0 else 0.0
    retention_rate = (c_nh / d_nh * 100) if d_nh > 0 else 0.0
    
    spx_str = f"{spx_ret:+.2%}" if spx_ret is not None else "N/A"
    ndx_str = f"{ndx_ret:+.2%}" if ndx_ret is not None else "N/A"
    
    print("\n==================================================")
    print(" [Python 1: 大型股 + 科技股 (S&P 500 & Nasdaq 100)] 廣度報告")
    print("==================================================")
    print(f"範圍: {start_date} ~ {end_date}")
    print(f"S&P 500 指數當期漲跌幅: {spx_str}")
    print(f"NAS 指數當期漲跌幅: {ndx_str}")
    print("--------------------------------------------------")
    print(f"Dynamic NH (新高): {d_nh} | Dynamic NL (新低): {d_nl}")
    print(f"淨新高 (Net NH): {net_nh} | NH Ratio: {nh_ratio:.1%}")
    print("--------------------------------------------------")
    print(f"Dynamic NH (嘗試攻堅家數): {d_nh}")
    print(f"Close NH   (成功站穩家數): {c_nh}")
    print(f"突破留存率 (Retention Rate): {retention_rate:.1f}%")
    print("==================================================\n")

if __name__ == '__main__':
    s_date, e_date = parse_dates()
    run_python1_largecap(s_date, e_date)
