import csv
import io
import urllib.request
import pandas as pd
import yfinance as yf

def parse_ishares_csv_robust(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    req = urllib.request.Request(url, headers=headers)
    raw_bytes = urllib.request.urlopen(req).read()
    
    # 使用 utf-8 解碼成純文字流
    text_data = raw_bytes.decode('utf-8', errors='ignore')
    reader = csv.reader(io.StringIO(text_data))
    
    header_found = False
    ticker_idx = -1
    tickers = []
    
    for row in reader:
        if not row:
            continue
        
        # 尋找包含 Ticker 欄位的 Header 列
        if not header_found:
            if 'Ticker' in row:
                ticker_idx = row.index('Ticker')
                header_found = True
            continue
            
        # 找到 Header 後，提取對應欄位的 Ticker
        if header_found and ticker_idx < len(row):
            symbol = str(row[ticker_idx]).strip()
            # 嚴格過濾：必須是長度 <= 5 且全為英文字母的股票代碼 (排除底部免責聲明與非個股)
            if symbol and len(symbol) <= 5 and symbol.isalpha():
                tickers.append(symbol)
                
    return list(set(tickers))

def get_official_sp500_and_ndx_tickers():
    tickers_set = set()
    
    # 1. 抓取 S&P 500 (IVV ETF)
    url_ivv = "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax?dataType=fund&fileName=IVV_holdings&fileType=csv"
    try:
        sp500_tickers = parse_ishares_csv_robust(url_ivv)
        tickers_set.update(sp500_tickers)
        print(f"成功取得 S&P 500 (IVV) 官方成分股: {len(tickers_set)} 隻")
    except Exception as e:
        print(f"抓取 IVV 失敗: {e}")

    # 2. 抓取 Nasdaq 100 (IBND ETF)
    url_ndx = "https://www.ishares.com/us/products/239702/ishares-nasdaq-100-etf/1467271812596.ajax?dataType=fund&fileName=IBND_holdings&fileType=csv"
    try:
        ndx_tickers = parse_ishares_csv_robust(url_ndx)
        tickers_set.update(ndx_tickers)
        print(f"成功併入 Nasdaq 100 官方成分股，去重後總數: {len(tickers_set)} 隻")
    except Exception as e:
        print(f"抓取 Nasdaq 100 失敗: {e}")

    return list(tickers_set)

def run_python1_largecap(start_date, end_date):
    tickers = get_official_sp500_and_ndx_tickers()
    if not tickers:
        print("無法取得股票清單。")
        return
        
    nh_set, nl_set = set(), set()
    print(f"\n[Python 1] 開始計算 S&P 500 + Nasdaq 100 (去重後共 {len(tickers)} 隻股票)...")
    
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
    
    print("\n========== [Python 1: 大型股+科技股] 月度報告 ==========")
    print(f"範圍: {start_date} ~ {end_date}")
    print(f"Dynamic NH (新高): {nh_count} | Dynamic NL (新低): {nl_count}")
    print(f"淨新高 (Net NH): {net_nh} | NH Ratio: {nh_ratio:.1%}")

if __name__ == '__main__':
    run_python1_largecap('2026-07-01', '2026-07-31')
