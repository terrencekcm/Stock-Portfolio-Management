// js/main.js
import { state } from './store.js';
import { fetchInitData, executeGasAction } from './api.js';
import * as Render from './render.js'; 
import * as Calc from './calc.js';
import * as Charts from './charts.js';

// 初始化日期
document.getElementById('txDate').value = new Date().toISOString().split('T')[0];

// ==========================================
// 1. Google 登入驗證
// ==========================================
// 真正處理登入並切換畫面的邏輯
window.processGoogleLogin = async function(response) {
    state.userGoogleToken = response.credential; 
    document.getElementById('loginWall').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    await loadData();
};

// 如果使用者手速很快，在 main.js 載入前就按了登入，這裡會抓出暫存的 Token 進行登入
if (window._pendingGoogleToken) {
    window.processGoogleLogin(window._pendingGoogleToken);
    delete window._pendingGoogleToken;
}

// ==========================================
// 2. 核心主線加載邏輯
// ==========================================
async function loadData() {
    try {
        Render.updateStatus("🔄 讀取即時數據中...", "loading");
        const data = await fetchInitData();
        
        // 寫入 State
        state.transactions = data.transactions || []; 
        state.optionsTx = data.optionsTx || []; 
        state.prices = data.prices || {}; 
        state.exchangeRate = data.exchangeRate || 7.82;
        
        for (const key in state.assetLabels) {
            if (data.assetPlan && data.assetPlan[key] !== undefined) state.assetPlan[key] = data.assetPlan[key];
            state.assetHidden[key] = data.assetHidden && data.assetHidden[key] ? true : false;
        }
        
        state.stockPlan = data.stockPlan || [];
        state.pdfMap = data.pdfMap || {}; 
        state.earningsMap = data.earningsMap || {}; 
        state.perfConfig = data.perfConfig || {};
        state.tradingPlans = data.tradingPlans || []; 
        state.valuations = data.valuations || []; 
        state.weeklyStrategies = data.weeklyStrategies || []; 
        state.latestBenchmarks = data.benchmarks || { sp500: 0, nasdaq: 0 };
        state.userRole = data.userRole || "Visitor";
        
        // 設定 API Key
        let ak = data.avApiKey || "";
        if (ak.includes(',')) state.avKeysArray = ak.split(',').map(k => k.trim()).filter(k => k);
        else if (ak) state.avKeysArray = [ak.trim()];
        else state.avKeysArray = [];
        state.avKeyIndex = 0;

        Render.applyRoleUI();
        Render.renderDashboard();
        Render.updateStatus(`✅ 雲端同步完成`, "success");
    } catch (err) { 
        console.error(err); 
        Render.updateStatus("❌ 讀取失敗，請核對網址或權限", "error"); 
    }
}

// ==========================================
// 3. 全域 UI 綁定
// ==========================================
window.switchTab = function(tabId) {
    if (tabId === 'settings-tab' && state.userRole !== 'PM') { alert("❌ 權限被拒絕"); return; }
    
    ['dashboard-tab', 'trading-tab', 'valuation-tab', 'reports-tab', 'settings-tab'].forEach(id => {
        const tabEl = document.getElementById(`tab-${id.replace('-tab', '')}`);
        const btnEl = document.getElementById(`btn-${id}`);
        if(tabEl) tabEl.classList.add('hidden');
        if(btnEl) btnEl.className = "px-4 py-2 rounded-md text-gray-600 hover:text-gray-900 whitespace-nowrap transition";
    });

    const activeTab = document.getElementById(`tab-${tabId.replace('-tab', '')}`);
    const activeBtn = document.getElementById(`btn-${tabId}`);
    if(activeTab) activeTab.classList.remove('hidden');
    if(activeBtn) activeBtn.className = "px-4 py-2 rounded-md bg-white shadow-sm text-blue-600 whitespace-nowrap transition";

    if (tabId === 'dashboard-tab') Render.renderDashboard();
    if (tabId === 'settings-tab') Render.renderSettingsPage();
};

window.openTxModal = () => document.getElementById('txInputModal').classList.remove('hidden');
window.closeTxModal = () => document.getElementById('txInputModal').classList.add('hidden');

window.toggleFormFields = function() {
    const category = document.getElementById('txCategory').value;
    ['stockFields', 'cashFields', 'optionsFields', 'basicMarketFields'].forEach(id => document.getElementById(id).classList.add('hidden'));
    
    if (category === 'STOCK') {
        document.getElementById('stockFields').classList.remove('hidden');
        document.getElementById('basicMarketFields').classList.remove('hidden');
    } else if (category === 'CASH') {
        document.getElementById('cashFields').classList.remove('hidden');
        document.getElementById('basicMarketFields').classList.remove('hidden');
    } else if (category === 'OPTIONS') {
        document.getElementById('optionsFields').classList.remove('hidden');
    }
};

window.openCandlestickModal = function(ticker, market) {
    state.currentChartTicker = ticker.toUpperCase().trim();
    state.currentChartMarket = market;
    state.currentTimeframe = "D"; 
    document.getElementById('chartModalTitle').innerText = state.currentChartTicker;
    document.getElementById('candlestickModal').classList.remove('hidden');
    Charts.fetchAndRenderChart();
};

window.closeCandlestickModal = function() {
    document.getElementById('candlestickModal').classList.add('hidden');
    if (state.activeChartInstance) {
        state.activeChartInstance = null; state.activeSeriesInstance = null;
        document.getElementById('chartContainer').innerHTML = '';
    }
};

window.changeTimeframe = function(tf) {
    state.currentTimeframe = tf;
    Charts.fetchAndRenderChart();
};

// ==========================================
// 4. 表單發送與刪除動作
// ==========================================
window.deleteTx = async function(id) {
    if (state.userRole === 'Visitor') { alert("❌ 無權異動數據！"); return; }
    if (!confirm("確定要刪除嗎？")) return;
    
    Render.updateStatus("🗑️ 正在刪除交易...", "loading");
    try {
        await executeGasAction("DELETE", { id: id });
        state.transactions = state.transactions.filter(t => t.id.toString() !== id.toString());
        Render.renderDashboard();
        Render.updateStatus("✅ 刪除成功", "success"); 
    } catch (error) { Render.updateStatus("❌ 刪除失敗", "error"); }
};

document.getElementById('txForm').addEventListener('submit', async function(e) {
    e.preventDefault(); 
    if (state.userRole === 'Visitor') { alert("❌ 無權異動數據！"); return; }
    
    const submitBtn = document.getElementById('submitBtn'); 
    submitBtn.disabled = true;
    Render.updateStatus("🚀 正在寫入...", "loading");
    
    const category = document.getElementById('txCategory').value;
    
    try {
        if (category === 'OPTIONS') {
            const payload = {
                id: Date.now().toString(),
                date: document.getElementById('txDate').value,
                ticker: document.getElementById('optTicker').value.trim().toUpperCase(),
                strategy: document.getElementById('optStrategy').value,
                strike: document.getElementById('optStrike').value,
                expiry: document.getElementById('optExpiry').value,
                qty: document.getElementById('optQty').value,
                premium: document.getElementById('optPremium').value
            };
            await executeGasAction("ADD_OPTION_OPEN", payload);
            payload.open_date = payload.date; payload.expiry_date = payload.expiry; payload.open_premium = payload.premium; payload.status = 'OPEN';
            state.optionsTx.unshift(payload);
        } else {
            let tx = { id: Date.now().toString(), date: document.getElementById('txDate').value, market: document.getElementById('txMarket').value };
            if (category === 'STOCK') {
                tx.code = document.getElementById('stockCode').value.trim().toUpperCase(); tx.type = document.getElementById('stockType').value;
                tx.price = document.getElementById('txPrice').value; tx.qty = document.getElementById('txQty').value;
            } else { 
                tx.code = 'CASH'; tx.type = document.getElementById('cashType').value; tx.price = '1'; tx.qty = document.getElementById('cashAmount').value; 
            }
            await executeGasAction("ADD_TX", tx); 
            state.transactions.unshift(tx);
        }
        
        Render.renderDashboard();
        Render.updateStatus("✅ 交易寫入成功！", "success");
        document.getElementById('txForm').reset();
        window.closeTxModal();
    } catch (error) { 
        Render.updateStatus("❌ 寫入失敗", "error"); 
    } finally { 
        submitBtn.disabled = false; 
    }
});

// ==========================================
// 5. 設定頁面與排序控制邏輯
// ==========================================
window.applyPositionSort = function() {
    const sortSelect = document.getElementById('positionSortSelect');
    if (sortSelect) {
        state.currentPosSort = sortSelect.value;
        Render.renderDashboard();
    }
};

window.addStockPlanRow = function() {
    const stockBody = document.getElementById('stockPlanSettingRows');
    if (stockBody) stockBody.insertAdjacentHTML('afterbegin', Render.createStockPlanRowHTML({}));
};

window.addPerfYearRow = function() {
    const perfContainer = document.getElementById('perfYearRowsContainer');
    if (perfContainer) {
        perfContainer.insertAdjacentHTML('afterbegin', `
            <div class="perf-year-row flex gap-2 items-center mb-2">
                <input type="number" class="py-year w-24 p-1.5 border rounded text-xs text-center font-bold" placeholder="年份">
                <input type="number" step="any" class="py-cap w-full p-1.5 border rounded text-xs font-bold text-emerald-600" placeholder="起步本金 (USD)">
                <button type="button" onclick="this.parentElement.remove()" class="text-rose-500 hover:text-rose-700 font-bold p-1">✕</button>
            </div>
        `);
    }
};

window.saveAllSettings = async function() {
    if (state.userRole !== 'PM') { alert("❌ 無權異動設定！"); return; }
    
    const saveBtn = document.querySelector("button[onclick='saveAllSettings()']");
    if(saveBtn) saveBtn.disabled = true;
    Render.updateStatus("💾 儲存設定至雲端...", "loading");

    try {
        const newAssetPlan = {}; 
        const newAssetHidden = {};
        
        document.querySelectorAll('.asset-weight-input').forEach(el => {
            newAssetPlan[el.dataset.key] = Number(el.value) || 0;
        });
        document.querySelectorAll('.asset-hide-checkbox').forEach(el => {
            newAssetHidden[el.dataset.key] = el.checked;
        });

        const newStockPlan = [];
        document.querySelectorAll('.stock-plan-row').forEach(row => {
            const code = row.querySelector('.sp-code').value.trim().toUpperCase();
            if (code) {
                // 🔥 這裡有抓取 .sp-industry-etf
                newStockPlan.push({
                    code: code,
                    market: row.querySelector('.sp-market').value,
                    leverage: Number(row.querySelector('.sp-leverage').value) || 1,
                    target_weight: Number(row.querySelector('.sp-weight').value) || 0,
                    sector: row.querySelector('.sp-sector').value.trim(),
                    industry_etf: row.querySelector('.sp-industry-etf') ? row.querySelector('.sp-industry-etf').value.trim().toUpperCase() : '',
                    strategy: row.querySelector('.sp-strategy').value,
                    date_type: row.querySelector('.sp-datetype').value,
                    earnings_date: row.querySelector('.sp-earnings').value
                });
            }
        });

        const newPerfConfig = {};
        const startYearEl = document.getElementById('inputHistStartYear');
        if (startYearEl) {
            const startYear = startYearEl.value.trim();
            if (startYear) newPerfConfig['histStartYear'] = startYear;
        }
        
        document.querySelectorAll('.perf-year-row').forEach(row => {
            const year = row.querySelector('.py-year').value.trim();
            const cap = row.querySelector('.py-cap').value.trim();
            if (year && cap) {
                newPerfConfig[`year_${year}`] = Number(cap);
            }
        });

        await executeGasAction("SAVE_SETTINGS", {
            assetPlan: newAssetPlan,
            assetHidden: newAssetHidden,
            stockPlan: newStockPlan,
            perfConfig: newPerfConfig
        });
        
        state.assetPlan = newAssetPlan; 
        state.assetHidden = newAssetHidden; 
        state.stockPlan = newStockPlan; 
        state.perfConfig = newPerfConfig;
        
        Render.updateStatus("✅ 設定儲存成功！", "success");
        Render.renderSettingsPage(); 
        
    } catch (error) {
        console.error(error);
        Render.updateStatus("❌ 儲存失敗", "error");
    } finally {
        if(saveBtn) saveBtn.disabled = false;
    }
};
