import csv
import io
import urllib.request
import pandas as pd
import yfinance as yf

def parse_ishares_csv_robust(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    req = urllib.request.Request(url, headers=headers)
    raw_bytes = urllib.request.urlopen(req).read()
    
    text_data = raw_bytes.decode('utf-8', errors='ignore')
    reader = csv.reader(io.StringIO(text_data))
    
    header_found = False
    ticker_idx = -1
    tickers = []
    
    for row in reader:
        if not row:
            continue
        
        if not header_found:
            if 'Ticker' in row:
                ticker_idx = row.index('Ticker')
                header_found = True
            continue
            
        if header_found and ticker_idx < len(row):
            symbol = str(row[ticker_idx]).strip()
            if symbol and len(symbol) <= 5 and symbol.isalpha():
                tickers.append(symbol)
                
    return list(set(tickers))

def get_russell2000_tickers():
    url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?dataType=fund&fileName=IWM_holdings&fileType=csv"
    try:
        iwm_tickers = parse_ishares_csv_robust(url)
        print(f"成功取得 Russell 2000 (IWM) 官方成分股: {len(iwm_tickers)} 隻")
        return iwm_tickers
    except Exception as e:
        print(f"抓取 IWM 持股失敗: {e}")
        return []

def run_python2_smallcap(start_date, end_date):
    tickers = get_russell2000_tickers()
    if not tickers:
        print("無法取得 Russell 2000 股票清單。")
        return
        
    nh_set, nl_set = set(), set()
    print(f"\n[Python 2] 開始計算 Russell 2000 (共 {len(tickers)} 隻股票)...")
    
    for ticker in tickers:
        symbol = ticker.replace('.', '-')
        try:
            df = yf.Ticker(symbol).history(period='1y')
            if df.empty: continue
                
            month_df = df.loc[start_date:end_date]
            if month_df.empty: continue
            
            month_high = month_df['High'].max()
            month_low = month_df['Low'].min()
            
            prior_data = df.loc[:start_date]
            prior_52w_high = prior_data['High'].tail(252).max()
            prior_52w_low = prior_data['Low'].tail(252).min()
            
            if month_high >= prior_52w_high:
                nh_set.add(symbol)
            if month_low <= prior_52w_low:
                nl_set.add(symbol)
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
