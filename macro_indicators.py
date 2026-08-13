import argparse
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
import os

# ==========================================
# 1. 解析命令列參數
# ==========================================
parser = argparse.ArgumentParser(description="Macro Indicators CLI")
parser.add_argument("--start_date", type=str, default="2026-01-01", help="Start Date YYYY-MM-DD")
parser.add_argument("--end_date", type=str, default="", help="End Date YYYY-MM-DD")
args = parser.parse_args()

START_DATE = args.start_date.strip() if args.start_date and args.start_date.strip() else "2026-01-01"
END_DATE = args.end_date.strip() if args.end_date and args.end_date.strip() else datetime.now().strftime("%Y-%m-%d")

# 計算向前墊高 60 天的抓取日期，確保 20D/4週 均線有足夠歷史數據可算
try:
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    fetch_start_dt = start_dt - timedelta(days=90)
    FETCH_START_DATE = fetch_start_dt.strftime("%Y-%m-%d")
except Exception:
    FETCH_START_DATE = "2025-10-01"

print(f"📌 用戶指定區間: {START_DATE} 至 {END_DATE}")
print(f"🔄 內部數據抓取區間 (自動墊高 90 天以計算均線): {FETCH_START_DATE} 至 {END_DATE}")

# ==========================================
# 2. 安全輔助函數
# ==========================================
def get_latest_valid_value(series):
    """安全獲取 Series 最新一個非空數值，避免 IndexError"""
    if series is None or series.dropna().empty:
        return None
    return series.dropna().iloc[-1]

# ==========================================
# 3. 數據抓取模組
# ==========================================
def fetch_data():
    # 1. YFinance 數據
    tickers = ["^MOVE", "^VIX", "^VIX3M", "^S5FI", "^S5TH", "SPHB", "SPLV", "^CPCE"]
    yf_data = pd.DataFrame()
    try:
        yf_raw = yf.download(tickers, start=FETCH_START_DATE, end=END_DATE, progress=False)
        if 'Close' in yf_raw:
            yf_data = yf_raw['Close']
        else:
            yf_data = yf_raw
    except Exception as e:
        print(f"⚠️ YFinance 下載警告: {e}")
    
    # 2. FRED 數據
    fred_tickers = ["BAMLH0A0HYM2", "WALCL", "WTREGEN", "RPTCW"]
    fred_data = pd.DataFrame()
    try:
        fred_data = web.DataReader(fred_tickers, 'fred', FETCH_START_DATE, END_DATE)
    except Exception as e:
        print(f"⚠️ FRED 下載警告: {e}")

    return yf_data, fred_data

# ==========================================
# 4. 各指標邏輯判斷器 (帶全套安全檢查)
# ==========================================
def analyze_hy_spread(fred_df):
    try:
        if "BAMLH0A0HYM2" not in fred_df:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "未能獲取 FRED 數據", "strategy": "暫不參考"}
        
        val = get_latest_valid_value(fred_df["BAMLH0A0HYM2"])
        if val is None:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "歷史區間無有效數據", "strategy": "暫不參考"}

        if val < 3.5:
            status, risk, strat = "🟢 安全/寬鬆", "企業融資環境健康，違約風險低。", "允許維持高倉位 (80-100%)"
        elif val <= 4.2:
            status, risk, strat = "🟡 中性/警惕", "信貸利差小幅擴張，資本市場邊際收緊。", "控制倉位在中性水平 (50-70%)"
        else:
            status, risk, strat = "🔴 嚴峻/預警", "信貸壓迫感上升，市場避險情緒顯著。", "降低風險 Exposure，提高現金比例"
            
        return {"value": f"{val:.2f}%", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_fed_liquidity(fred_df):
    try:
        cols = ["WALCL", "WTREGEN", "RPTCW"]
        if not all(c in fred_df for c in cols):
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "FRED 數據項不完整", "strategy": "暫不參考"}
        
        df = fred_df[cols].ffill().dropna()
        if df.empty:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "無重疊有效數據", "strategy": "暫不參考"}

        net_liq = (df["WALCL"] - df["WTREGEN"] - df["RPTCW"]) / 1000  # 換算為 10 億美元
        val = get_latest_valid_value(net_liq)
        if val is None:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "無法計算淨流動性", "strategy": "暫不參考"}

        change_4w = val - net_liq.iloc[-20] if len(net_liq) >= 20 else 0
        
        if change_4w >= 0:
            status, risk, strat = "🟢 流動性充沛", "美聯儲淨流動性近一月呈擴張或平穩狀態。", "資金面支持大盤向上"
        else:
            status, risk, strat = "🟡 流動性抽水", "淨流動性近一月呈現淨流出狀態。", "警惕估值承壓，防範無預警回調"
            
        return {"value": f"${val:,.0f}B (4週變化: ${change_4w:+,.0f}B)", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_move(yf_df):
    try:
        if "^MOVE" not in yf_df:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "Yahoo 無 MOVE 數據", "strategy": "暫不參考"}
            
        val = get_latest_valid_value(yf_df["^MOVE"])
        if val is None:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "該區間無 MOVE 價格", "strategy": "暫不參考"}

        if val < 90:
            status, risk, strat = "🟢 債市平穩", "利率市場波幅處於低位，無流動性恐慌。", "跨資產環境良好"
        elif val <= 120:
            status, risk, strat = "🟡 波動上升", "債市不確定性增加，對美股估值產生干擾。", "密切觀察美債收益率走勢"
        else:
            status, risk, strat = "🔴 債市恐慌", "債券市場極度動盪，容易引發股市流動性擠壓。", "減倉避險，避免過度激進"
            
        return {"value": f"{val:.2f}", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_breadth(yf_df):
    try:
        s5fi = get_latest_valid_value(yf_df["^S5FI"]) if "^S5FI" in yf_df else None
        s5th = get_latest_valid_value(yf_df["^S5TH"]) if "^S5TH" in yf_df else None
        
        if s5fi is None and s5th is None:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "Yahoo 廣度指標未回應", "strategy": "參考自建 NH/NL 數據"}

        val_str = f"S5FI(50D): {s5fi:.1f}%" if s5fi else ""
        if s5th:
            val_str += f" | S5TH(200D): {s5th:.1f}%"
        
        if s5fi and s5fi > 70:
            status, risk, strat = "🟢 強勢多頭", "多數個股站上中長期均線，市場廣度健全。", "積極參與主線行情"
        elif s5fi and s5fi < 30:
            status, risk, strat = "🔴 超賣/弱勢", "市場個股普跌，中線動能極度微弱。", "等待止跌訊號，不盲目接刀"
        else:
            status, risk, strat = "🟡 震盪分化", "個股表現分化，攻堅品質視留存率而定。", "精選個股，不宜重倉追高"
            
        return {"value": val_str, "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_vix_ratio(yf_df):
    try:
        if "^VIX" not in yf_df or "^VIX3M" not in yf_df:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "缺少 VIX 或 VIX3M 數據", "strategy": "暫不參考"}
            
        vix = get_latest_valid_value(yf_df["^VIX"])
        vix3m = get_latest_valid_value(yf_df["^VIX3M"])
        
        if vix is None or vix3m is None or vix3m == 0:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "VIX 區間數據不足", "strategy": "暫不參考"}

        ratio = vix / vix3m
        
        if ratio < 0.95:
            status, risk, strat = "🟢 正向結構 (Contango)", "市場情緒平靜，未見短期恐慌對沖。", "允許高 Exposure (70-100%)"
        elif ratio <= 1.00:
            status, risk, strat = "🟡 結構趨平 (Flattening)", "短期風險防範情緒抬頭，情緒開始焦慮。", "停止擴大槓桿，收緊止損"
        else:
            status, risk, strat = "🚨 倒掛 (Backwardation)", "短期避險需求爆發，市場進入系統性恐慌。", "觸發硬性風控，防守至倒掛解除"
            
        return {"value": f"{ratio:.3f} (VIX: {vix:.1f} / VIX3M: {vix3m:.1f})", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_cpce(yf_df):
    try:
        if "^CPCE" not in yf_df:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "Yahoo 無 CPCE 數據", "strategy": "暫不參考"}
            
        s = yf_df["^CPCE"].dropna()
        if s.empty:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "CPCE 無歷史記錄", "strategy": "暫不參考"}

        sma20 = s.rolling(20).mean()
        val = get_latest_valid_value(sma20)
        
        if val is None:
            return {"value": "N/A", "status": "⚪ 數據不足", "risk": "交易日數不足 20 天無法算 SMA", "strategy": "暫不參考"}

        if val < 0.52:
            status, risk, strat = "🔴 極度自滿/過熱", "散戶極度追漲 Call，完全放棄 Put 防守（反向訊號）。", "中線頂部風險高，建議逢高減倉"
        elif val > 0.75:
            status, risk, strat = "🟢 極度恐慌/超賣", "散戶大量買入 Put 避險割肉（反向訊號）。", "籌碼清理充分，準備右側建倉/加倉"
        else:
            status, risk, strat = "🟡 情緒中性", "投機情緒處於歷史合理常態區間。", "順應主趨勢操作"
            
        return {"value": f"{val:.3f}", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

def analyze_sphb_splv(yf_df):
    try:
        if "SPHB" not in yf_df or "SPLV" not in yf_df:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "缺少 SPHB 或 SPLV ETF 數據", "strategy": "暫不參考"}
            
        ratio = (yf_df["SPHB"] / yf_df["SPLV"]).dropna()
        if ratio.empty:
            return {"value": "N/A", "status": "⚪ 數據缺失", "risk": "無法計算 SPHB/SPLV 比率", "strategy": "暫不參考"}

        current_val = get_latest_valid_value(ratio)
        ma20_series = ratio.rolling(20).mean()
        ma20 = get_latest_valid_value(ma20_series)
        
        if current_val is None or ma20 is None:
            return {"value": "N/A", "status": "⚪ 數據不足", "risk": "數據不足以計算 20D MA", "strategy": "暫不參考"}

        if current_val > ma20:
            status, risk, strat = "🟢 Risk-On (資金進攻)", "資金持續偏好高 Beta 股票，市場風險偏好強勁。", "適當提高進攻型/成長型持倉"
        else:
            status, risk, strat = "🟡 Risk-Off (資金防守)", "資金流向低波動防禦股，市場偏好避險。", "倉位向防禦型或大盤權重傾斜"
            
        return {"value": f"{current_val:.3f} (20D MA: {ma20:.3f})", "status": status, "risk": risk, "strategy": strat}
    except Exception as e:
        return {"value": "Error", "status": "⚠️ 計算異常", "risk": str(e), "strategy": "-"}

# ==========================================
# 5. 主執行與 Markdown 輸出
# ==========================================
def main():
    yf_df, fred_df = fetch_data()
    
    indicators = {
        "高收益債信用利差": analyze_hy_spread(fred_df),
        "美聯儲淨流動性": analyze_fed_liquidity(fred_df),
        "債券市場波動率 (MOVE)": analyze_move(yf_df),
        "市場廣度 (S5FI / S5TH)": analyze_breadth(yf_df),
        "VIX / VIX3M 比率": analyze_vix_ratio(yf_df),
        "個股認沽/認購比率 (CPCE 20D)": analyze_cpce(yf_df),
        "高 Beta vs 低波動 (SPHB/SPLV)": analyze_sphb_splv(yf_df)
    }
    
    summary_md = f"# 📊 Macro Indicators 宏觀大市風控儀表板\n"
    summary_md += f"**執行基準日:** `{END_DATE}` | **用戶查詢區間:** `{START_DATE}` ~ `{END_DATE}`\n\n"
    summary_md += "| 指標 | 當前數值 | 數值狀態 | 風險解釋 | 建議策略 |\n"
    summary_md += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for name, item in indicators.items():
        summary_md += f"| **{name}** | `{item['value']}` | {item['status']} | {item['risk']} | {item['strategy']} |\n"
        
    print(summary_md)
    
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary_md)

if __name__ == "__main__":
    main()
