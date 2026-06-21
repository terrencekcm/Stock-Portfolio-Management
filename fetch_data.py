import yfinance as yf
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def analyze_ai_market():
    print("正在啟動 HBM/記憶體基本面自動化抓取程序...")
    
    # ----------------------------------------------------
    # 1. 100% 自動化：利用 yfinance 計算 NVIDIA 與 ASIC 強度
    # ----------------------------------------------------
    # 抓取近 3 個月的日線數據
    nvda = yf.Ticker("NVDA").history(period="3mo")
    avgo = yf.Ticker("AVGO").history(period="3mo")
    
    # 計算 NVDA 的 50日移動平均線 (50MA)
    nvda['50MA'] = nvda['Close'].rolling(window=50).mean()
    
    latest_nvda_close = nvda['Close'].iloc[-1]
    latest_nvda_50ma = nvda['50MA'].iloc[-1]
    
    # 判斷 NVDA 是否跌破 50MA 風險線
    nvda_broken_50ma = latest_nvda_close < latest_nvda_50ma
    
    # 計算過去 5 個交易日（一週）的相對強度
    nvda_weekly_return = (nvda['Close'].iloc[-1] / nvda['Close'].iloc[-5]) - 1
    avgo_weekly_return = (avgo['Close'].iloc[-1] / avgo['Close'].iloc[-5]) - 1
    
    # 核心邏輯判定：若 NVDA 破線，但 ASIC 龍頭 AVGO 卻比它強，觸發背離警訊
    asic_status = "normal"
    if nvda_broken_50ma and (avgo_weekly_return > nvda_weekly_return):
        asic_status = "warning"
        
    print(f"美股技術面量化完成。NVDA 收盤: {latest_nvda_close:.2f}, 50MA: {latest_nvda_50ma:.2f}. ASIC狀態: {asic_status}")

    # ----------------------------------------------------
    # 2. 半自動化：免 API Key 抓取 Google News 供應鏈前瞻情報
    # ----------------------------------------------------
    def fetch_latest_tech_news(keyword):
        # 將關鍵字轉為 URL 編碼，向 Google News RSS 發起請求
        enc_keyword = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={enc_keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            response = urllib.request.urlopen(url)
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            # 只取最新的一條核心新聞標題與連結
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                return {"title": title, "link": link}
        except Exception as e:
            return {"title": f"暫時無法獲取 {keyword} 最新動態", "link": "#"}
        return {"title": "本週暫無重大產業更新", "link": "#"}

    print("正在爬取台灣及全球半導體供應鏈前瞻情報...")
    dram_news = fetch_latest_tech_news("DRAM 現貨價 合約價")
    cowos_news = fetch_latest_tech_news("CoWoS 產能利用率 台積電")
    equipment_news = fetch_latest_tech_news("半導體 設備交期 記憶體")

    # ----------------------------------------------------
    # 3. 彙整數據，輸出為網頁可讀取的 data.json 檔案
    # ----------------------------------------------------
    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stock_metrics": {
            "nvda_close": round(latest_nvda_close, 2),
            "nvda_50ma": round(latest_nvda_50ma, 2),
            "asic_strength": asic_status
        },
        "supply_chain_news": {
            "dram": dram_news,
            "cowos": cowos_news,
            "equipment": equipment_news
        }
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    print("data.json 數據庫更新成功！")

if __name__ == "__main__":
    analyze_ai_market()
