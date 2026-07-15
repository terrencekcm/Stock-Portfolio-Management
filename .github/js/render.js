// js/render.js
import { state } from './store.js';
import { calculatePortfolio } from './calc.js';

export function updateStatus(text, type) {
    const el = document.getElementById('statusIndicator');
    el.innerText = text;
    el.className = `text-xs px-3 py-2 rounded-full font-medium shadow-sm ${
        type === 'success' ? 'bg-green-100 text-green-800' :
        type === 'error' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
    }`;
}

export function applyRoleUI() {
    const badge = document.getElementById('roleBadge');
    badge.classList.remove('hidden');
    const btnAddTx = document.getElementById('btn-add-tx'); 
    
    if (state.userRole === 'PM') {
        badge.className = "text-xs px-3 py-1.5 rounded-full bg-purple-100 text-purple-800 font-extrabold shadow-sm";
        badge.innerText = "👑 PM 投資組合經理";
        document.getElementById('btn-settings-tab').classList.remove('hidden');
        document.getElementById('visitorBlockMessage').classList.add('hidden');
        document.getElementById('txFormFieldsWrap').classList.remove('hidden');
        document.getElementById('btn-add-weekly-strategy').classList.remove('hidden');
        if (btnAddTx) btnAddTx.classList.remove('hidden');
    } else if (state.userRole === 'Trader') {
        badge.className = "text-xs px-3 py-1.5 rounded-full bg-blue-100 text-blue-800 font-extrabold shadow-sm";
        badge.innerText = "⚡ Trader 交易員";
        document.getElementById('btn-settings-tab').classList.add('hidden');
        document.getElementById('visitorBlockMessage').classList.add('hidden');
        document.getElementById('txFormFieldsWrap').classList.remove('hidden');
        document.getElementById('btn-add-weekly-strategy').classList.remove('hidden');
        if (btnAddTx) btnAddTx.classList.remove('hidden');
    } else if (state.userRole === 'Analyst') {
        badge.className = "text-xs px-3 py-1.5 rounded-full bg-teal-100 text-teal-800 font-extrabold shadow-sm";
        badge.innerText = "🔎 Analyst 估值分析師";
        document.getElementById('btn-settings-tab').classList.add('hidden');
        document.getElementById('visitorBlockMessage').classList.remove('hidden'); 
        document.getElementById('txFormFieldsWrap').classList.add('hidden');
        if (btnAddTx) btnAddTx.classList.add('hidden');
    } else {
        badge.className = "text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 font-extrabold border border-gray-200 shadow-sm";
        badge.innerText = "👁️ Visitor 訪客 (唯讀)";
        document.getElementById('btn-settings-tab').classList.add('hidden');
        document.getElementById('visitorBlockMessage').classList.remove('hidden');
        document.getElementById('txFormFieldsWrap').classList.add('hidden');
        if (btnAddTx) btnAddTx.classList.add('hidden');
    }
}

export function renderDashboard() {
    const { cashBalances, positions, optionsLockedLC, optionsLockedSP } = calculatePortfolio();
    
    // 計算總市值與渲染邏輯 (與原 index.html 完全一致，為省版面，核心概念如上)
    let totalStockMarketValueUsd = 0; let totalCashUsd = 0;
    
    for (const mkt in cashBalances) { 
        totalCashUsd += (cashBalances[mkt] * ((mkt === 'HK') ? (1 / state.exchangeRate) : 1)); 
    }
    
    for (const code in positions) {
        const p = positions[code];
        const livePrice = state.prices[p.yahooSymbol] || 0;
        const mktValUsd = p.market === 'HK' ? ((p.shares * livePrice) / state.exchangeRate) : (p.shares * livePrice);
        if (!p.isPlannedOnly && p.shares > 0) totalStockMarketValueUsd += mktValUsd;
    }
    
    document.getElementById('headerCashUsd').innerText = `USD $${totalCashUsd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('headerAllocationUsd').innerText = `USD $${totalStockMarketValueUsd.toLocaleString(undefined, {maximumFractionDigits:2})}`;
    
    // (後續表格繪製維持原邏輯，透過引入 `state` 抓取資料渲染)
}

export function renderOptionsTable() {
    // 渲染期權表邏輯 (將 transactions 換成 state.optionsTx 即可)
}
// ... 其他 renderTradingPlanPage, renderPerformanceReport 皆套用相同模式

// 在 js/render.js 檔案底部加入以下函數

export function renderSettingsPage() {
    // 1. 宏觀資產大類渲染
    const assetContainer = document.getElementById('assetSettingInputs');
    assetContainer.innerHTML = '';
    let totalAssetWeight = 0;
    
    for (const key in state.assetPlan) {
        const weight = state.assetPlan[key];
        const isHidden = state.assetHidden[key];
        const label = state.assetLabels[key] || key;
        totalAssetWeight += Number(weight) || 0;

        assetContainer.innerHTML += `
            <div class="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-100 shadow-sm hover:shadow transition">
                <div class="flex flex-col gap-1.5 w-full mr-2">
                    <label class="font-bold text-gray-700 text-xs">${label} <span class="text-gray-400 font-normal">(${key})</span></label>
                    <div class="flex items-center gap-2">
                        <input type="number" step="any" class="asset-weight-input w-20 p-1.5 text-sm font-bold text-blue-600 border border-gray-300 rounded focus:outline-blue-500 bg-gray-50" data-key="${key}" value="${weight}">
                        <span class="text-xs text-gray-500 font-bold">%</span>
                    </div>
                </div>
                <div class="flex flex-col items-center justify-center gap-1 shrink-0 bg-gray-50 p-2 rounded border border-gray-100">
                    <input type="checkbox" class="asset-hide-checkbox w-4 h-4 cursor-pointer accent-rose-500" data-key="${key}" ${isHidden ? 'checked' : ''}>
                    <label class="text-[10px] text-gray-500 font-bold cursor-pointer">隱藏</label>
                </div>
            </div>
        `;
    }
    
    document.getElementById('assetTotalCheck').innerText = `總計: ${totalAssetWeight.toFixed(2)}%`;
    if (totalAssetWeight !== 100) {
        document.getElementById('assetTotalCheck').classList.replace('bg-blue-100', 'bg-rose-100');
        document.getElementById('assetTotalCheck').classList.replace('text-blue-600', 'text-rose-600');
    } else {
        document.getElementById('assetTotalCheck').classList.replace('bg-rose-100', 'bg-blue-100');
        document.getElementById('assetTotalCheck').classList.replace('text-rose-600', 'text-blue-600');
    }

    // 2. 個股計劃設定渲染
    const stockBody = document.getElementById('stockPlanSettingRows');
    stockBody.innerHTML = '';
    state.stockPlan.forEach((s, idx) => {
        stockBody.insertAdjacentHTML('beforeend', createStockPlanRowHTML(s, idx));
    });

    // 3. 全倉績效基準設定渲染
    document.getElementById('inputHistStartYear').value = state.perfConfig['histStartYear'] || '';
    const perfContainer = document.getElementById('perfYearRowsContainer');
    perfContainer.innerHTML = '';
    
    // 假設 perfConfig 存儲如 { "year_2024": 100000, "year_2025": 150000 }
    Object.keys(state.perfConfig).forEach(key => {
        if (key.startsWith('year_')) {
            const year = key.replace('year_', '');
            const cap = state.perfConfig[key];
            perfContainer.insertAdjacentHTML('beforeend', `
                <div class="perf-year-row flex gap-2 items-center mb-2">
                    <input type="number" class="py-year w-24 p-1.5 border rounded text-xs text-center font-bold" value="${year}" placeholder="年份">
                    <input type="number" step="any" class="py-cap w-full p-1.5 border rounded text-xs font-bold text-emerald-600" value="${cap}" placeholder="起步本金 (USD)">
                    <button type="button" onclick="this.parentElement.remove()" class="text-rose-500 hover:text-rose-700 font-bold p-1">✕</button>
                </div>
            `);
        }
    });
}

export function createStockPlanRowHTML(s, idx = Date.now()) {
    return `
        <tr class="stock-plan-row hover:bg-gray-50 transition" data-idx="${idx}">
            <td class="px-2 py-2"><input type="text" class="sp-code w-full p-1.5 border border-gray-300 rounded uppercase font-bold text-xs" value="${s.code || ''}" placeholder="AAPL"></td>
            <td class="px-2 py-2">
                <select class="sp-market w-full p-1.5 border border-gray-300 rounded text-xs bg-white font-medium">
                    <option value="US" ${s.market === 'US' ? 'selected' : ''}>US</option>
                    <option value="HK" ${s.market === 'HK' ? 'selected' : ''}>HK</option>
                    <option value="BOND_L" ${s.market === 'BOND_L' ? 'selected' : ''}>BOND_L</option>
                    <option value="BOND_S" ${s.market === 'BOND_S' ? 'selected' : ''}>BOND_S</option>
                    <option value="GOLD" ${s.market === 'GOLD' ? 'selected' : ''}>GOLD</option>
                </select>
            </td>
            <td class="px-2 py-2"><input type="number" step="any" class="sp-leverage w-full p-1.5 border border-gray-300 rounded text-xs text-indigo-700 font-bold bg-indigo-50" value="${s.leverage || 1}"></td>
            <td class="px-2 py-2"><input type="number" step="any" class="sp-weight w-full p-1.5 border border-gray-300 rounded text-xs font-bold" value="${s.target_weight || 0}"></td>
            <td class="px-2 py-2"><input type="text" class="sp-sector w-full p-1.5 border border-gray-300 rounded text-xs text-amber-700 font-medium bg-amber-50" value="${s.sector || '未分類'}" placeholder="例如: 科技"></td>
            <!-- 🔥 新增的行業 ETF 欄位 -->
            <td class="px-2 py-2"><input type="text" class="sp-industry-etf w-full p-1.5 border border-gray-300 rounded text-xs text-sky-700 font-bold uppercase bg-sky-50" value="${s.industry_etf || ''}" placeholder="例如: SMH"></td>
            <td class="px-2 py-2">
                <select class="sp-strategy w-full p-1.5 border border-gray-300 rounded text-xs bg-purple-50 text-purple-700 font-bold">
                    <option value="攻擊" ${s.strategy === '攻擊' ? 'selected' : ''}>⚔️ 攻擊</option>
                    <option value="防守" ${s.strategy === '防守' ? 'selected' : ''}>🛡️ 防守</option>
                    <option value="核心" ${s.strategy === '核心' ? 'selected' : ''}>💎 核心</option>
                </select>
            </td>
            <td class="px-2 py-2">
                <div class="flex gap-1">
                    <select class="sp-datetype w-14 p-1.5 border border-gray-300 rounded text-[10px] bg-white">
                        <option value="手動" ${s.date_type === '手動' ? 'selected' : ''}>手動</option>
                        <option value="自動" ${s.date_type === '自動' ? 'selected' : ''}>自動</option>
                    </select>
                    <input type="date" class="sp-earnings w-full p-1 border border-gray-300 rounded text-[10px] text-rose-700 font-medium" value="${s.earnings_date || ''}">
                </div>
            </td>
            <td class="px-2 py-2 text-center">
                <button type="button" onclick="this.closest('tr').remove()" class="text-rose-500 hover:bg-rose-100 rounded font-bold text-xs p-1.5 transition">✕</button>
            </td>
        </tr>
    `;
}
