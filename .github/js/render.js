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
