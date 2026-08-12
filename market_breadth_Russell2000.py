import io
import urllib.request
import pandas as pd
import yfinance as yf

def get_clean_russell2000_tickers():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    
    # 使用 GitHub 乾淨的 Russell 2000 成分股資料源
    url_iwm = "https://raw.githubusercontent.com/anon-developer/russell-2000-tickers/main/russell_2000_tickers.csv"
    
    try:
        req = urllib.request.Request(url_iwm, headers=headers)
        content = urllib.request.urlopen(req).read()
        df = pd.read_csv(io.BytesIO(content))
        
        # 自動尋找包含 ticker / symbol 的欄位
        col_name = [c for c in df.columns if 'ticker' in c.lower() or 'symbol' in c.lower()][0]
        raw_tickers = df[col_name].dropna().tolist()
        
        cleaned_tickers = [str(t).strip().replace('.', '-') for t in raw_tickers if len(str(t).strip()) <= 5]
        print(f"成功取得 Russell 2000 純淨成分股: {len(cleaned_tickers)} 隻")
        return cleaned_tickers
    except Exception as e:
        print(f"主要來源失敗 ({e})，啟動備用極速來源...")
        # 備用來源
        url_backup = "https://raw.githubusercontent.com/datasets/investor-cli/master/russell2000.csv"
        try:
            req = urllib.request.Request(url_backup, headers=headers)
            df = pd.read_csv(urllib.request.urlopen(req))
            tickers = df.iloc[:, 0].dropna().tolist()
            print(f"備用來源成功取得 Russell 2000 成分股: {len(tickers)} 隻")
            return [str(t).strip().replace('.', '-') for t in tickers]
        except Exception as ex:
            print(f"備用來源亦失敗: {ex}")
            return []

def run_python2_smallcap(start_date, end_date):
    tickers = get_clean_russell2000_tickers()
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
