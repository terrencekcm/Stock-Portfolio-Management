import io
import urllib.request
import pandas as pd
import yfinance as yf

def get_russell2000_tickers():
    # 從 iShares IWM 官方開放數據抓取成分股列表
    url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?dataType=fund&fileName=IWM_holdings&fileType=csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        csv_data = urllib.request.urlopen(req).read()
        # 跳過前 9 行非表格 Header
        df = pd.read_csv(io.BytesIO(csv_data), skiprows=9)
        tickers = df['Ticker'].dropna().unique().tolist()
        # 過濾非個股 Ticker (如 USD 泥金或未上市公司)
        valid_tickers = [t for t in tickers if isinstance(t, str) and len(t) <= 5 and t.isalpha()]
        return valid_tickers
    except Exception as e:
        print(f"抓取 IWM 持股失敗: {e}，改用備用 API/清單")
        return []

def run_python2_smallcap(start_date, end_date):
    tickers = get_russell2000_tickers()
    if not tickers:
        print("無法取得 Russell 2000 股票清單。")
        return
        
    nh_set, nl_set = set(), set()
    
    print(f"[Python 2] 開始計算 Russell 2000 (共 {len(tickers)} 隻股票)...")
    
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
