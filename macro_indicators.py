import argparse
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
import os

# ==========================================
# 1. 解析命令列參數 (支援 GitHub UI 輸入)
# ==========================================
parser = argparse.ArgumentParser(description="Macro Indicators CLI")
parser.add_argument("--start_date", type=str, default="2026-01-01", help="Start Date YYYY-MM-DD")
parser.add_argument("--end_date", type=str, default="", help="End Date YYYY-MM-DD")
args = parser.parse_args()

# 設定 START_DATE (若輸入空白則使用預設值)
START_DATE = args.start_date if args.start_date.strip() else "2026-01-01"

# 設定 END_DATE (若輸入空白則自動取今天日期)
if args.end_date and args.end_date.strip():
    END_DATE = args.end_date.strip()
else:
    END_DATE = datetime.now().strftime("%Y-%m-%d")

print(f"📌 當前設定分析區間: {START_DATE} 至 {END_DATE}")

# ==========================================
# 2. 數據抓取模組
# ==========================================
def fetch_data():
    print(f"Fetching data from {START_DATE} to {END_DATE}...")
    
    # 1. YFinance 數據
    tickers = ["^MOVE", "^VIX", "^VIX3M", "^S5FI", "^S5TH", "SPHB", "SPLV"]
    yf_data = yf.download(tickers, start=START_DATE, end=END_DATE)['Close']
    
    # 2. FRED 數據 (美聯儲資產負債表與信貸利差)
    fred_tickers = ["BAMLH0A0HYM2", "WALCL", "WTREGEN", "RPTCW"]
    try:
        fred_data = web.DataReader(fred_tickers, 'fred', START_DATE, END_DATE)
    except Exception as e:
        print(f"FRED fetch warning: {e}")
        fred_data = pd.DataFrame()

    # 3. CBOE CPCE 數據 (直接從 CBOE 讀取最新數據)
    try:
        cpce_url = "https://cdn.cboe.com/resources/options/market_statistics/daily_gex/equitypc.csv"
        # 備用：若 CBOE 格式變更，可改抓 Yahoo 的 ^CPCE
        cpce_data = yf.download("^CPCE", start=START_DATE, end=END_DATE)['Close']
    except:
        cpce_data = pd.Series(dtype=float)

    return yf_data, fred_data, cpce_data

# ==========================================
# 3. 各指標邏輯判斷器
# ==========================================
def analyze_hy_spread(fred_df):
    if "BAMLH0A0HYM2" not in fred_df or fred_df["BAMLH0A0HYM2"].dropna().empty:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
    
    val = fred_df["BAMLH0A0HYM2"].dropna().iloc[-1]
    if val < 3.5:
        status, risk, strat = "🟢 安全/寬鬆", "企業融資環境健康，違約風險低。", "允許維持高倉位 (80-100%)"
    elif val <= 4.2:
        status, risk, strat = "🟡 中性/警惕", "信貸利差小幅擴張，資本市場邊際收緊。", "控制倉位在中性水平 (50-70%)"
    else:
        status, risk, strat = "🔴 嚴峻/預警", "信貸壓迫感上升，市場避險情緒顯著。", "降低風險 Exposure，提高現金比例"
        
    return {"value": f"{val:.2f}%", "status": status, "risk": risk, "strategy": strat}

def analyze_fed_liquidity(fred_df):
    cols = ["WALCL", "WTREGEN", "RPTCW"]
    if not all(c in fred_df for c in cols):
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
    
    df = fred_df[cols].ffill().dropna()
    net_liq = (df["WALCL"] - df["WTREGEN"] - df["RPTCW"]) / 1000  # 換算為 10 億美元 (Billion)
    if net_liq.empty:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
        
    val = net_liq.iloc[-1]
    change_4w = val - net_liq.iloc[-20] if len(net_liq) >= 20 else 0
    
    if change_4w >= 0:
        status, risk, strat = "🟢 流動性充沛", "美聯儲淨流動性近一月呈擴張或平穩狀態。", "資金面支持大盤向上"
    else:
        status, risk, strat = "🟡 流動性抽水", "淨流動性近一月呈現淨流出狀態。", "警惕估值承壓，防範無預警回調"
        
    return {"value": f"${val:,.0f}B (4週變化: ${change_4w:+,.0f}B)", "status": status, "risk": risk, "strategy": strat}

def analyze_move(yf_df):
    if "^MOVE" not in yf_df or yf_df["^MOVE"].dropna().empty:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
        
    val = yf_df["^MOVE"].dropna().iloc[-1]
    if val < 90:
        status, risk, strat = "🟢 債市平穩", "利率市場波幅處於低位，無流動性恐慌。", "跨資產環境良好"
    elif val <= 120:
        status, risk, strat = "🟡 波動上升", "債市不確定性增加，對美股估值產生干擾。", "密切觀察美債收益率走勢"
    else:
        status, risk, strat = "🔴 債市恐慌", "債券市場極度動盪，容易引發股市流動性擠壓。", "減倉避險，避免過度激進"
        
    return {"value": f"{val:.2f}", "status": status, "risk": risk, "strategy": strat}

def analyze_breadth(yf_df):
    s5fi = yf_df["^S5FI"].dropna().iloc[-1] if "^S5FI" in yf_df and not yf_df["^S5FI"].dropna().empty else None
    s5th = yf_df["^S5TH"].dropna().iloc[-1] if "^S5TH" in yf_df and not yf_df["^S5TH"].dropna().empty else None
    
    val_str = f"S5FI(50D): {s5fi:.1f}% | S5TH(200D): {s5th:.1f}%" if s5fi and s5th else "部分數據缺失"
    
    if s5fi and s5fi > 70:
        status, risk, strat = "🟢 強勢多頭", "多數個股站上中長期均線，市場廣度健全。", "積極參與主線行情"
    elif s5fi and s5fi < 30:
        status, risk, strat = "🔴 超賣/弱勢", "市場個股普跌，中線動能極度微弱。", "等待止跌訊號，不盲目接刀"
    else:
        status, risk, strat = "🟡 震盪分化", "個股表現分化，市場攻堅品質需視突破留存率而定。", "精選個股，不宜重倉追高"
        
    return {"value": val_str, "status": status, "risk": risk, "strategy": strat}

def analyze_vix_ratio(yf_df):
    if "^VIX" not in yf_df or "^VIX3M" not in yf_df:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
        
    vix = yf_df["^VIX"].dropna().iloc[-1]
    vix3m = yf_df["^VIX3M"].dropna().iloc[-1]
    ratio = vix / vix3m
    
    if ratio < 0.95:
        status, risk, strat = "🟢 正向結構 (Contango)", "市場情緒平靜，未見短期恐慌對沖。", "允許高 Exposure"
    elif ratio <= 1.00:
        status, risk, strat = "🟡 結構趨平 (Flattening)", "短期風險防範情緒抬頭，情緒開始焦慮。", "停止擴大槓桿，收緊止損"
    else:
        status, risk, strat = "🚨 倒掛 (Backwardation)", "短期避險需求爆發，市場進入系統性恐慌。", "觸發硬性風控，防守至倒掛解除"
        
    return {"value": f"{ratio:.3f} (VIX: {vix:.1f} / VIX3M: {vix3m:.1f})", "status": status, "risk": risk, "strategy": strat}

def analyze_cpce(cpce_series):
    if cpce_series.dropna().empty:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
        
    s = cpce_series.dropna()
    sma20 = s.rolling(20).mean().iloc[-1] if len(s) >= 20 else s.iloc[-1]
    
    if sma20 < 0.52:
        status, risk, strat = "🔴 極度自滿/過熱", "散戶極度追漲 Call，完全放棄 Put 防守（反向訊號）。", "中線頂部風險高，建議逢高減倉"
    elif sma20 > 0.75:
        status, risk, strat = "🟢 極度恐慌/超賣", "散戶大量買入 Put 避險割肉（反向訊號）。", "籌碼清理充分，準備右側建倉/加倉"
    else:
        status, risk, strat = "🟡 情緒中性", "投機情緒處於歷史合理常態區間。", "順應主趨勢操作"
        
    return {"value": f"{sma20:.3f}", "status": status, "risk": risk, "strategy": strat}

def analyze_sphb_splv(yf_df):
    if "SPHB" not in yf_df or "SPLV" not in yf_df:
        return {"value": "N/A", "status": "無數據", "risk": "-", "strategy": "-"}
        
    ratio = yf_df["SPHB"] / yf_df["SPLV"]
    ratio = ratio.dropna()
    
    current_val = ratio.iloc[-1]
    ma20 = ratio.rolling(20).mean().iloc[-1]
    
    if current_val > ma20:
        status, risk, strat = "🟢 Risk-On (資金進攻)", "資金持續偏好高 Beta 股票，市場風險偏好強勁。", "適當提高進攻型/成長型持倉"
    else:
        status, risk, strat = "🟡 Risk-Off (資金防守)", "資金流向低波動防禦股，市場偏好避險。", "倉位向防禦型或大盤權重傾斜"
        
    return {"value": f"{current_val:.3f} (20D MA: {ma20:.3f})", "status": status, "risk": risk, "strategy": strat}

# ==========================================
# 4. 主執行與 Markdown 輸出
# ==========================================
def main():
    yf_df, fred_df, cpce_series = fetch_data()
    
    indicators = {
        "高收益債信用利差": analyze_hy_spread(fred_df),
        "美聯儲淨流動性": analyze_fed_liquidity(fred_df),
        "債券市場波動率 (MOVE)": analyze_move(yf_df),
        "市場廣度 (S5FI / S5TH)": analyze_breadth(yf_df),
        "VIX / VIX3M 比率": analyze_vix_ratio(yf_df),
        "個股認沽/認購比率 (CPCE 20D)": analyze_cpce(cpce_series),
        "高 Beta vs 低波動 (SPHB/SPLV)": analyze_sphb_splv(yf_df)
    }
    
    # 輸出至 GitHub Action Summary (Markdown)
    summary_md = f"# 📊 Macro Indicators 宏觀大市風控儀表板\n"
    summary_md += f"**執行日期:** `{END_DATE}` | **分析數據區間:** `{START_DATE}` ~ `{END_DATE}`\n\n"
    summary_md += "| 指標 | 當前數值 | 數值狀態 | 風險解釋 | 建議策略 |\n"
    summary_md += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for name, item in indicators.items():
        summary_md += f"| **{name}** | `{item['value']}` | {item['status']} | {item['risk']} | {item['strategy']} |\n"
        
    print(summary_md)
    
    # 若在 GitHub Actions 環境中，將結果寫入 $GITHUB_STEP_SUMMARY
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary_md)

if __name__ == "__main__":
    main()
