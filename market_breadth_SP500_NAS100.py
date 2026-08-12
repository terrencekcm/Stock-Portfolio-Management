import io
import urllib.request
import pandas as pd
import yfinance as yf

def get_clean_sp500_and_ndx_tickers():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'}
    tickers_set = set()
    
    # 1. 取得 S&P 500 (來自高度穩定的 datasets 庫，已確認成功)
    url_sp500 = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
    try:
        req = urllib.request.Request(url_sp500, headers=headers)
        df_sp500 = pd.read_csv(urllib.request.urlopen(req))
        sp500_list = df_sp500['Symbol'].dropna().tolist()
        tickers_set.update(sp500_list)
        print(f"✅ 成功取得 S&P 500 成分股: {len(sp500_list)} 隻")
    except Exception as e:
        print(f"❌ 抓取 S&P 500 失敗: {e}")

    # 2. 取得 Nasdaq 100 (改用最穩定的維基百科，避開 404)
    url_ndx = "https://en.wikipedia.org/wiki/Nasdaq-100"
    try:
        req = urllib.request.Request(url_ndx, headers=headers)
        html = urllib.request.urlopen(req).read()
        tables = pd.read_html(io.BytesIO(html))
        for df in tables:
            if 'Ticker' in df.columns:
                ndx_list = df['Ticker'].dropna().tolist()
                tickers_set.update(ndx_list)
                print(f"✅ 成功取得 Nasdaq 100 成分股，去重後總數: {len(tickers_set)} 隻")
                break
    except Exception as e:
        print(f"❌ 抓取 Nasdaq 100 失敗: {e}")

    # 清洗代碼格式以符合 Yahoo Finance (例如 BRK.B -> BRK-B)
    cleaned_tickers = [str(t).strip().replace('.', '-') for t in tickers_set if isinstance(t, str)]
    return list(set(cleaned_tickers))

def run_python1_largecap(start_date, end_date):
    tickers = get_clean_sp500_and_ndx_tickers()
    if not tickers:
        print("無法取得股票清單。")
        return
        
    nh_set, nl_set = set(), set()
    print(f"\n[Python 1] 開始計算 S&P 500 + Nasdaq 100 (去重後共 {len(tickers)} 隻股票)...")
    
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
