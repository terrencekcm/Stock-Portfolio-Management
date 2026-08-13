import argparse
import io
import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 1. 解析命令列參數
# ==========================================
parser = argparse.ArgumentParser()
parser.add_argument("--start_date", type=str, default="2026-01-01")
parser.add_argument("--end_date", type=str, default="")
args = parser.parse_args()

START_DATE = args.start_date.strip() if args.start_date and args.start_date.strip() else "2026-01-01"
END_DATE = args.end_date.strip() if args.end_date and args.end_date.strip() else datetime.now().strftime("%Y-%m-%d")

# 自動墊高 90 天以計算 20D MA 及 4週變化量
try:
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    FETCH_START_DATE = (start_dt - timedelta(days=90)).strftime("%Y-%m-%d")
except Exception:
    FETCH_START_DATE = "2025-10-01"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ==========================================
# 2. 數據抓取助手 (帶 User-Agent 偽裝)
# ==========================================
def get_fred_series(series_id):
    """直接從 FRED 官網抓取 CSV，帶 Header 避開 403/404 封鎖"""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            df['DATE'] = pd.to_datetime(df['DATE'])
            df.set_index('DATE', inplace=True)
            df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
            return df[series_id].dropna()
    except Exception as e:
        print(f"⚠️ FRED [{series_id}] 抓取失敗: {e}")
    return pd.Series(dtype=float)

def get_cboe_cpce():
    """直接從 CBOE 官網抓取個股 Put/Call Ratio"""
    urls = [
        "https://cdn.cboe.com/resources/options/market_statistics/daily_gex/equitypc.csv",
        "https://www.cboe.com/publish/ScheduledTask/MktData/datahouse/equitypc.csv"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text), skiprows=2)
                # 自動搜尋包含 Ratio 或 P/C 的欄位
                ratio_col = [c for c in df.columns if 'Ratio' in c or 'P/C' in c]
                date_col = [c for c in df.columns if 'Date' in c]
                if ratio_col and date_col:
                    df[date_col[0]] = pd.to_datetime(df[date_col[0]])
                    df.set_index(date_col[0], inplace=True)
                    s = pd.to_numeric(df[ratio_col[0]], errors='coerce').dropna()
                    return s
        except Exception:
            continue
    return pd.Series(dtype=float)

def get_yf_ticker(ticker):
    """單獨抓取 Yahoo Finance Ticker，確保單一失敗不影響整體"""
    try:
        t = yf.Ticker(ticker)
        df = t.history(start=FETCH_START_DATE, end=END_DATE)
        if not df.empty and 'Close' in df:
            return df['Close']
    except Exception:
        pass
    return pd.Series(dtype=float)

# ==========================================
# 3. 各指標計算邏輯
# ==========================================
def calc_hy_spread():
    s = get_fred_series("BAMLH0A0HYM2")
    if s.empty: return "N/A", "⚪ 數據缺失", "FRED 連線受阻", "暫不參考"
    val = s.iloc[-1]
    if val < 3.5:
        return f"{val:.2f}%", "🟢 安全/寬鬆", "企業融資環境健康，違約風險低。", "維持高倉位 (80-100%)"
    elif val <= 4.2:
        return f"{val:.2f}%", "🟡 中性/警惕", "信貸利差小幅擴張，資本市場邊際收緊。", "控制倉位在中性 (50-70%)"
    else:
        return f"{val:.2f}%", "🔴 嚴峻/預警", "信貸壓迫感上升，避險情緒顯著。", "降低風險 Exposure"

def calc_fed_liquidity():
    walcl = get_fred_series("WALCL")
    tga = get_fred_series("WTREGEN")
    rrp = get_fred_series("RPTCW")
    
    if walcl.empty or tga.empty or rrp.empty:
        return "N/A", "⚪ 數據缺失", "FRED 流動性數據項不完整", "暫不參考"
    
    df = pd.concat([walcl, tga, rrp], axis=1).ffill().dropna()
    if df.empty: return "N/A", "⚪ 數據缺失", "無重疊有效數據", "暫不參考"
    
    net_liq = (df["WALCL"] - df["WTREGEN"] - df["RPTCW"]) / 1000  # 換算 10 億美元
    val = net_liq.iloc[-1]
    change_4w = val - net_liq.iloc[-20] if len(net_liq) >= 20 else 0
    
    val_str = f"${val:,.0f}B (4週: ${change_4w:+,.0f}B)"
    if change_4w >= 0:
        return val_str, "🟢 流動性充沛", "美聯儲淨流動性呈擴張或平穩。", "資金面支持大盤向上"
    else:
        return val_str, "🟡 流動性抽水", "淨流動性近一月呈現淨流出。", "警惕估值承壓，防範回調"

def calc_move():
    s = get_yf_ticker("^MOVE")
    if s.empty: return "N/A", "⚪ 數據缺失", "Yahoo 無 MOVE 數據", "暫不參考"
    val = s.iloc[-1]
    if val < 90:
        return f"{val:.2f}", "🟢 債市平穩", "利率波幅低，無流動性恐慌。", "跨資產環境良好"
    elif val <= 120:
        return f"{val:.2f}", "🟡 波動上升", "債市不確定性增加，干擾股市估值。", "觀察美債收益率走勢"
    else:
        return f"{val:.2f}", "🔴 債市恐慌", "債市極度動盪，易引發股市流動性擠壓。", "減倉避險"

def calc_breadth():
    s5fi = get_yf_ticker("^S5FI")
    s5th = get_yf_ticker("^S5TH")
    
    if s5fi.empty and s5th.empty:
        return "N/A", "⚪ 數據缺失", "Yahoo 廣度指標接口異動", "參考自建 NH/NL 數據"
    
    v1 = s5fi.iloc[-1] if not s5fi.empty else None
    v2 = s5th.iloc[-1] if not s5th.empty else None
    
    val_str = f"S5FI: {v1:.1f}%" if v1 else ""
    if v2: val_str += f" | S5TH: {v2:.1f}%"
    
    if v1 and v1 > 70:
        return val_str, "🟢 強勢多頭", "多數個股站上均線，廣度健全。", "積極參與主線行情"
    elif v1 and v1 < 30:
        return val_str, "🔴 超賣/弱勢", "市場個股普跌，中線動能微弱。", "等待止跌訊號，不接刀"
    else:
        return val_str, "🟡 震盪分化", "個股表現分化，攻堅品質視留存率而定。", "精選個股，不宜追高"

def calc_vix_ratio():
    vix = get_yf_ticker("^VIX")
    vix3m = get_yf_ticker("^VIX3M")
    
    if vix.empty or vix3m.empty:
        return "N/A", "⚪ 數據缺失", "缺少 VIX/VIX3M 數據", "暫不參考"
        
    v_val, v3_val = vix.iloc[-1], vix3m.iloc[-1]
    ratio = v_val / v3_val
    val_str = f"{ratio:.3f} (VIX: {v_val:.1f} / VIX3M: {v3_val:.1f})"
    
    if ratio < 0.95:
        return val_str, "🟢 正向結構 (Contango)", "市場情緒平靜，未見短期恐慌對沖。", "允許高 Exposure (70-100%)"
    elif ratio <= 1.00:
        return val_str, "🟡 結構趨平 (Flattening)", "避險情緒抬頭，情緒開始焦慮。", "停止擴大槓桿，收緊止損"
    else:
        return val_str, "🚨 倒掛 (Backwardation)", "避險需求爆發，進入系統性恐慌。", "觸發硬性風控，防守至倒掛解除"

def calc_cpce():
    s = get_cboe_cpce()
    if s.empty:
        # 備用：嘗試 Yahoo ^CPCE
        s = get_yf_ticker("^CPCE")
        
    if s.empty:
        return "N/A", "⚪ 數據缺失", "CBOE/Yahoo CPCE 數據讀取失敗", "暫不參考"
        
    sma20 = s.rolling(20).mean().dropna()
    if sma20.empty:
        return "N/A", "⚪ 數據不足", "數據不足 20 日無法算 SMA", "暫不參考"
        
    val = sma20.iloc[-1]
    if val < 0.52:
        return f"{val:.3f}", "🔴 極度自滿/過熱", "散戶極度追漲 Call，放棄 Put 防守 (反向訊號)。", "中線頂部風險高，逢高減倉"
    elif val > 0.75:
        return f"{val:.3f}", "🟢 極度恐慌/超賣", "散戶大量買 Put 避險割肉 (反向訊號)。", "籌碼清理充分，準備加倉"
    else:
        return f"{val:.3f}", "🟡 情緒中性", "投機情緒處於合理常態區間。", "順應主趨勢操作"

def calc_sphb_splv():
    sphb = get_yf_ticker("SPHB")
    splv = get_yf_ticker("SPLV")
    
    if sphb.empty or splv.empty:
        return "N/A", "⚪ 數據缺失", "缺少 SPHB 或 SPLV 數據", "暫不參考"
        
    ratio = (sphb / splv).dropna()
    if ratio.empty: return "N/A", "⚪ 數據缺失", "無法計算比率", "暫不參考"
    
    cur_val = ratio.iloc[-1]
    ma20 = ratio.rolling(20).mean().dropna().iloc[-1] if len(ratio) >= 20 else cur_val
    val_str = f"{cur_val:.3f} (20D MA: {ma20:.3f})"
    
    if cur_val > ma20:
        return val_str, "🟢 Risk-On (資金進攻)", "資金偏好高 Beta 股票，風險偏好強勁。", "適當提高進攻型持倉"
    else:
        return val_str, "🟡 Risk-Off (資金防守)", "資金流向低波動防禦股，偏好避險。", "倉位向防禦型或權重傾斜"

# ==========================================
# 4. 主執行與 Markdown 簡化輸出
# ==========================================
def main():
    indicators = [
        ("高收益債信用利差", calc_hy_spread()),
        ("美聯儲淨流動性", calc_fed_liquidity()),
        ("債券市場波動率 (MOVE)", calc_move()),
        ("市場廣度 (S5FI / S5TH)", calc_breadth()),
        ("VIX / VIX3M 比率", calc_vix_ratio()),
        ("個股認沽/認購比率 (CPCE 20D)", calc_cpce()),
        ("高 Beta vs 低波動 (SPHB/SPLV)", calc_sphb_splv())
    ]
    
    summary_md = f"# 📊 Macro Indicators 宏觀大市風控儀表板\n"
    summary_md += f"**基準日:** `{END_DATE}` | **區間:** `{START_DATE}` ~ `{END_DATE}`\n\n"
    summary_md += "| 指標 | 當前數值 | 數值狀態 | 風險解釋 | 建議策略 |\n"
    summary_md += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for name, (val, status, risk, strat) in indicators:
        summary_md += f"| **{name}** | `{val}` | {status} | {risk} | {strat} |\n"
        
    print(summary_md)
    
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary_md)

if __name__ == "__main__":
    main()
