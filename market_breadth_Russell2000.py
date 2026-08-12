import urllib.request
import re
import yfinance as yf

def get_bulletproof_russell2000():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    # 使用 iShares IWM 官方最新持股清單
    url_iwm = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?dataType=fund&fileName=IWM_holdings&fileType=csv"
    
    tickers = set()
    exclude_words = {"TICKER", "SYMBOL", "NAME", "USD", "CASH"}
    
    try:
        req = urllib.request.Request(url_iwm, headers=headers)
        raw_bytes = urllib.request.urlopen(req).read()
        
        # 暴力清除所有 NUL 空字元並解碼
        text_data = raw_bytes.decode('utf-8', errors='ignore').replace('\x00', '')
        
        # 逐行解析，無視任何 Header 與 Footer
        for line in text_data.splitlines():
            cols = line.split(',')
            if not cols: continue
            
            # 取第一欄 (通常是 Ticker)
            sym = cols[0].strip(' "\'')
            
            # 嚴格正則過濾：必須是 1~6 位的全大寫字母 (允許包含 1 個點或橫線)
            if re.match(r'^[A-Z\.\-]{1,6}$', sym) and sym not in exclude_words:
                # 轉化點號為橫線，符合 Yahoo Finance 格式
                tickers.add(sym.replace('.', '-'))
                
        print(f"✅ 成功透過官方 CSV 解析出 Russell 2000 成分股: {len(tickers)} 隻")
        return list(tickers)
        
    except Exception as e:
        print(f"❌ 抓取 Russell 2000 失敗: {e}")
        return []

def run_python2_smallcap(start_date, end_date):
    tickers = get_bulletproof_russell2000()
    if not tickers:
        print("無法取得 Russell 2000 股票清單。")
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
