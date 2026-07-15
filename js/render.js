// js/render.js
import { state } from './store.js';
import { calculatePortfolio } from './calc.js';

export function updateStatus(text, type) { 
    const el = document.getElementById('statusIndicator');
    if (!el) return;
    el.innerText = text;
    el.className = `text-xs px-3 py-2 rounded-full font-medium shadow-sm ${
        type === 'success' ? 'bg-green-100 text-green-800' :
        type === 'error' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
    }`;
}

export function applyRoleUI() {
    const badge = document.getElementById('roleBadge');
    if (badge) badge.classList.remove('hidden');
    const btnAddTx = document.getElementById('btn-add-tx'); 
    const visitorMsg = document.getElementById('visitorBlockMessage');
    const txWrap = document.getElementById('txFormFieldsWrap');
    const btnSettings = document.getElementById('btn-settings-tab');
    const btnStrategy = document.getElementById('btn-add-weekly-strategy');
    
    if (state.userRole === 'PM') {
        if(badge) { badge.className = "text-xs px-3 py-1.5 rounded-full bg-purple-100 text-purple-800 font-extrabold shadow-sm"; badge.innerText = "👑 PM 投資組合經理"; }
        if(btnSettings) btnSettings.classList.remove('hidden');
        if(visitorMsg) visitorMsg.classList.add('hidden');
        if(txWrap) txWrap.classList.remove('hidden');
        if(btnStrategy) btnStrategy.classList.remove('hidden');
        if(btnAddTx) btnAddTx.classList.remove('hidden');
    } else if (state.userRole === 'Trader') {
        if(badge) { badge.className = "text-xs px-3 py-1.5 rounded-full bg-blue-100 text-blue-800 font-extrabold shadow-sm"; badge.innerText = "⚡ Trader 交易員"; }
        if(btnSettings) btnSettings.classList.add('hidden');
        if(visitorMsg) visitorMsg.classList.add('hidden');
        if(txWrap) txWrap.classList.remove('hidden');
        if(btnStrategy) btnStrategy.classList.remove('hidden');
        if(btnAddTx) btnAddTx.classList.remove('hidden');
    } else if (state.userRole === 'Analyst') {
        if(badge) { badge.className = "text-xs px-3 py-1.5 rounded-full bg-teal-100 text-teal-800 font-extrabold shadow-sm"; badge.innerText = "🔎 Analyst 估值分析師"; }
        if(btnSettings) btnSettings.classList.add('hidden');
        if(visitorMsg) visitorMsg.classList.remove('hidden'); 
        if(txWrap) txWrap.classList.add('hidden');
        if(btnAddTx) btnAddTx.classList.add('hidden');
    } else {
        if(badge) { badge.className = "text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 font-extrabold border border-gray-200 shadow-sm"; badge.innerText = "👁️ Visitor 訪客 (唯讀)"; }
        if(btnSettings) btnSettings.classList.add('hidden');
        if(visitorMsg) visitorMsg.classList.remove('hidden');
        if(txWrap) txWrap.classList.add('hidden');
        if(btnAddTx) btnAddTx.classList.add('hidden');
    }
}

// 🔥 完整修復版的 renderDashboard
export function renderDashboard() {
    const { cashBalances, positions, optionsLockedLC, optionsLockedSP } = calculatePortfolio();

    let totalStockMarketValueUsd = 0; let totalCashUsd = 0;
    let assetActualUsd = { "US": 0, "HK": 0, "BOND_L": 0, "BOND_S": 0, "GOLD": 0 };
    let sectorUsd = {};

    for (const mkt in cashBalances) {
        let cashUsd = cashBalances[mkt] * ((mkt === 'HK') ? (1 / state.exchangeRate) : 1);
        totalCashUsd += cashUsd;
    }
    assetActualUsd["CASH_TOTAL"] = totalCashUsd; 

    let positionsArray = [];

    // 計算每一檔股票的市值與損益
    for (const code in positions) {
        const p = positions[code];
        const livePrice = state.prices[p.yahooSymbol] || 0;
        const mktValUsd = p.market === 'HK' ? ((p.shares * livePrice) / state.exchangeRate) : (p.shares * livePrice);

        p.livePrice = livePrice;
        p.mktValUsd = mktValUsd;
        p.unrealizedPl = mktValUsd - (p.market === 'HK' ? p.totalCost / state.exchangeRate : p.totalCost);

        if (!p.isPlannedOnly && p.shares > 0) {
            totalStockMarketValueUsd += mktValUsd;
            if(assetActualUsd[p.market] !== undefined) {
                assetActualUsd[p.market] += mktValUsd;
            }
        }

        // 對應計畫表裡的屬性
        let planItem = state.stockPlan.find(s => s.code === p.code);
        p.sector = planItem ? planItem.sector : "未分類";
        p.strategy = planItem ? planItem.strategy : "未分類";
        p.industry_etf = planItem ? planItem.industry_etf : ""; // 🔥 抓取行業 ETF 資料

        if (!p.isPlannedOnly && p.shares > 0 && p.market === 'US') {
            sectorUsd[p.sector] = (sectorUsd[p.sector] || 0) + mktValUsd;
        }

        positionsArray.push(p);
    }

    const totalPortfolioUsd = totalCashUsd + totalStockMarketValueUsd;

    // 渲染上方四大數據卡
    const elCash = document.getElementById('headerCashUsd');
    const elAlloc = document.getElementById('headerAllocationUsd');
    const elAsset = document.getElementById('headerTotalAsset');
    if(elCash) elCash.innerText = `USD $${totalCashUsd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    if(elAlloc) elAlloc.innerText = `USD $${totalStockMarketValueUsd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}`;
    if(elAsset) elAsset.innerText = `總資產淨值: USD $${totalPortfolioUsd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}`;

    // 1. 渲染宏觀大類資產表 (assetPlanTable)
    const assetTbody = document.getElementById('assetPlanTable');
    if(assetTbody) {
        assetTbody.innerHTML = '';
        for (const key in state.assetPlan) {
            if (state.assetHidden[key]) continue;
            const targetPct = Number(state.assetPlan[key]) || 0;
            const actualUsd = assetActualUsd[key] || 0;
            const actualPct = totalPortfolioUsd > 0 ? (actualUsd / totalPortfolioUsd) * 100 : 0;
            const diff = actualPct - targetPct;

            let diffColor = diff > 0 ? 'text-rose-500' : (diff < 0 ? 'text-blue-500' : 'text-gray-500');

            assetTbody.innerHTML += `
                <tr>
                    <td class="px-4 py-2.5 font-bold">${state.assetLabels[key] || key}</td>
                    <td class="px-4 py-2.5 text-gray-500">${targetPct.toFixed(1)}%</td>
                    <td class="px-4 py-2.5 font-bold">${actualPct.toFixed(1)}%</td>
                    <td class="px-4 py-2.5 font-bold ${diffColor}">${diff > 0 ? '+'+diff.toFixed(1) : diff.toFixed(1)}%</td>
                    <td class="px-4 py-2.5 text-blue-600 font-semibold">$${actualUsd.toLocaleString(undefined, {maximumFractionDigits:0})}</td>
                </tr>
            `;
        }
    }

    // 2. 渲染板塊集中度表 (sectorBreakdownTable)
    const sectorTbody = document.getElementById('sectorBreakdownTable');
    if(sectorTbody) {
        sectorTbody.innerHTML = '';
        const usTargetPct = Number(state.assetPlan['US']) || 0;
        const usTargetUsd = totalPortfolioUsd * (usTargetPct / 100);

        let sectorPlanWeight = {};
        state.stockPlan.forEach(s => {
            if(s.market === 'US') {
                sectorPlanWeight[s.sector] = (sectorPlanWeight[s.sector] || 0) + (Number(s.target_weight) || 0);
            }
        });

        let allSectors = new Set([...Object.keys(sectorUsd), ...Object.keys(sectorPlanWeight)]);
        let sectorRows = [];
        allSectors.forEach(sec => {
            const actualVal = sectorUsd[sec] || 0;
            const actualPct = usTargetUsd > 0 ? (actualVal / usTargetUsd) * 100 : 0;
            const targetPct = sectorPlanWeight[sec] || 0;
            sectorRows.push({ sec, actualVal, actualPct, targetPct });
        });

        sectorRows.sort((a,b) => b.actualPct - a.actualPct).forEach(r => {
            sectorTbody.innerHTML += `
                <tr>
                    <td class="px-4 py-2.5 font-bold">${r.sec}</td>
                    <td class="px-4 py-2.5 text-blue-600 font-bold">${r.targetPct.toFixed(1)}%</td>
                    <td class="px-4 py-2.5 text-indigo-600 font-bold">${r.actualPct.toFixed(1)}%</td>
                    <td class="px-4 py-2.5 text-gray-700 font-semibold">$${r.actualVal.toLocaleString(undefined, {maximumFractionDigits:0})}</td>
                </tr>
            `;
        });
    }

    // 3. 渲染個股持倉表 (positionTable)
    const posTbody = document.getElementById('positionTable');
    if(posTbody) {
        posTbody.innerHTML = '';

        // 應用排序功能
        const sortMode = state.currentPosSort || 'default';
        if (sortMode === 'shares') positionsArray.sort((a, b) => b.shares - a.shares);
        else if (sortMode === 'code') positionsArray.sort((a, b) => a.code.localeCompare(b.code));
        else if (sortMode === 'sector') positionsArray.sort((a, b) => a.sector.localeCompare(b.sector));
        
        positionsArray.forEach(p => {
            if (p.code === 'CASH') return;
            const isPlan = p.isPlannedOnly || p.shares <= 0;

            let planItem = state.stockPlan.find(s => s.code === p.code);
            let targetWeight = planItem ? Number(planItem.target_weight) : 0;

            const assetClassPct = Number(state.assetPlan[p.market]) || 0;
            const assetClassTargetUsd = totalPortfolioUsd * (assetClassPct / 100);
            const assetRealPct = assetClassTargetUsd > 0 ? (p.mktValUsd / assetClassTargetUsd) * 100 : 0;
            const totalRealPct = totalPortfolioUsd > 0 ? (p.mktValUsd / totalPortfolioUsd) * 100 : 0;

            let unPlStr = isPlan ? '-' : p.unrealizedPl.toFixed(2);
            let unPlColor = p.unrealizedPl > 0 ? 'text-emerald-600' : (p.unrealizedPl < 0 ? 'text-rose-600' : 'text-gray-500');
            let days = isPlan ? '-' : Math.floor((new Date() - new Date(p.firstBuyDate)) / (1000 * 60 * 60 * 24));
            let trClass = isPlan ? 'bg-gray-50/50 opacity-70' : 'hover:bg-blue-50 transition';

            posTbody.innerHTML += `
                <tr class="${trClass}">
                    <td class="px-2 py-3 font-bold text-blue-700 cursor-pointer" onclick="openCandlestickModal('${p.code}', '${p.market}')">${p.code}</td>
                    <td class="px-2 py-3">${p.market}</td>
                    <td class="px-2 py-3 font-bold text-purple-700">${p.strategy}</td>
                    <!-- 🔥 這裡加入了 p.industry_etf 的小標籤 -->
                    <td class="px-2 py-3 text-amber-700 font-medium">${p.sector} ${p.industry_etf ? `<span class="bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded text-[10px] ml-1 font-bold">${p.industry_etf}</span>` : ''}</td>
                    <td class="px-2 py-3 font-bold">${isPlan ? '計畫' : p.shares.toFixed(2)}</td>
                    <td class="px-2 py-3">${isPlan ? '-' : (p.totalCost / p.shares).toFixed(3)}</td>
                    <td class="px-2 py-3 font-bold bg-yellow-50/50">${p.livePrice.toFixed(3)}</td>
                    <td class="px-2 py-3 text-blue-600 font-bold">$${p.mktValUsd.toLocaleString(undefined, {maximumFractionDigits:2})}</td>
                    <td class="px-1 py-3 font-bold text-gray-500">${targetWeight.toFixed(1)}%</td>
                    <td class="px-1 py-3 font-bold text-indigo-600">${assetRealPct.toFixed(1)}%</td>
                    <td class="px-1 py-3 font-bold text-emerald-600">${totalRealPct.toFixed(1)}%</td>
                    <td class="px-2 py-3 font-bold ${unPlColor}">${unPlStr}</td>
                    <td class="px-1 py-3 text-gray-400 text-[10px]">${days}</td>
                </tr>
            `;
        });
    }
    
    // 4. 渲染歷史流水帳 (historyTable)
    const histTbody = document.getElementById('historyTable');
    if(histTbody) {
        histTbody.innerHTML = '';
        const recentTx = [...state.transactions].slice(0, 50); 
        recentTx.forEach(t => {
            let actColor = t.type === 'BUY' || t.type === 'DEPOSIT' ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50';
            histTbody.innerHTML += `
                <tr class="hover:bg-gray-100 transition">
                    <td class="px-3 py-2 text-gray-500">${t.date}</td>
                    <td class="px-3 py-2 font-bold">${t.code}</td>
                    <td class="px-3 py-2 text-gray-400">${t.market}</td>
                    <td class="px-3 py-2"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${actColor}">${t.type}</span></td>
                    <td class="px-3 py-2">${Number(t.price).toFixed(3)}</td>
                    <td class="px-3 py-2">${t.qty}</td>
                    <td class="px-3 py-2">
                        ${state.userRole !== 'Visitor' ? `<button onclick="deleteTx('${t.id}')" class="text-rose-500 hover:text-rose-700 font-bold p-1">刪除</button>` : '-'}
                    </td>
                </tr>
            `;
        });
    }
}

export function renderOptionsTable() {
    // 預留期權表渲染空間
}

// 🔥 新增的設定頁面渲染 (包含行業 ETF 輸入框)
export function renderSettingsPage() {
    const assetContainer = document.getElementById('assetSettingInputs');
    if(!assetContainer) return; 
    
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
    
    const assetCheckEl = document.getElementById('assetTotalCheck');
    if (assetCheckEl) {
        assetCheckEl.innerText = `總計: ${totalAssetWeight.toFixed(2)}%`;
        if (totalAssetWeight !== 100) {
            assetCheckEl.classList.replace('bg-blue-100', 'bg-rose-100');
            assetCheckEl.classList.replace('text-blue-600', 'text-rose-600');
        } else {
            assetCheckEl.classList.replace('bg-rose-100', 'bg-blue-100');
            assetCheckEl.classList.replace('text-rose-600', 'text-blue-600');
        }
    }

    const stockBody = document.getElementById('stockPlanSettingRows');
    if(stockBody) {
        stockBody.innerHTML = '';
        state.stockPlan.forEach((s, idx) => {
            stockBody.insertAdjacentHTML('beforeend', createStockPlanRowHTML(s, idx));
        });
    }

    const inputHistStart = document.getElementById('inputHistStartYear');
    if(inputHistStart) inputHistStart.value = state.perfConfig['histStartYear'] || '';
    
    const perfContainer = document.getElementById('perfYearRowsContainer');
    if(perfContainer) {
        perfContainer.innerHTML = '';
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
