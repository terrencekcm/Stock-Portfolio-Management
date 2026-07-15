// js/store.js
 
export const state = {
    API_URL: "https://script.google.com/macros/s/AKfycbzsDE79EEEn1EpdYYTg44A8HeXzIEXs1hpV4JSjQUXeWo8uzeucaKndIm-RWce_l3Gy/exec",
    assetLabels: {
        "US": "美股", "HK": "港股", "BOND_L": "US 長債", "BOND_S": "US 短債", "GOLD": "金", "OPTIONS": "期權", "CASH_TOTAL": "現金"
    },
    currentPosSort: 'default',
    userGoogleToken: "",
    userRole: "Visitor",
    transactions: [],
    prices: {},
    exchangeRate: 7.82,
    assetPlan: { "US": 70, "HK": 0, "BOND_L": 0, "BOND_S": 25, "GOLD": 5, "OPTIONS": 0, "CASH_TOTAL": 0 },
    assetHidden: { "US": false, "HK": false, "BOND_L": false, "BOND_S": false, "GOLD": false, "OPTIONS": false, "CASH_TOTAL": false },
    optionsTx: [],
    stockPlan: [],
    pdfMap: {},
    earningsMap: {},
    perfConfig: {},
    tradingPlans: [],
    valuations: [],
    weeklyStrategies: [],
    activePlanTarget: { code: "", market: "" },
    activeValTarget: { code: "", market: "" },
    latestBenchmarks: { sp500: 0, nasdaq: 0 },
    
    // Alpha Vantage 狀態
    alphaVantageApiKey: "",
    avKeysArray: [],
    avKeyIndex: 0,
    
    // 圖表狀態
    chartCache: {},
    currentChartTicker: "",
    currentChartMarket: "",
    currentTimeframe: "D",
    activeChartInstance: null,
    activeSeriesInstance: null
};
