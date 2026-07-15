// js/calc.js
import { state } from './store.js'; 

export function calculatePortfolio() {
    let cashBalances = { "US": 0, "HK": 0, "BOND_L": 0, "BOND_S": 0, "GOLD": 0 };
    let positions = {};
    const chronological = [...state.transactions].reverse();
    
    chronological.forEach(t => {
        if (!t.code) return;
        const codeStr = String(t.code).trim().toUpperCase(); 
        const typeStr = String(t.type).trim().toUpperCase();
        const marketStr = String(t.market).trim().toUpperCase();
        const price = parseFloat(t.price) || 0; 
        const qty = parseFloat(t.qty) || 0; 
        const amt = price * qty;

        if (codeStr === 'CASH') {
            if (typeStr === 'DEPOSIT') cashBalances[marketStr] += qty;
            else if (typeStr === 'WITHDRAW') cashBalances[marketStr] -= qty;
        } else {
            if (!positions[codeStr]) {
                let yahooSymbol = codeStr;
                if (marketStr === 'HK') {
                    var pureCode = yahooSymbol.replace(".HK", "").trim();
                    if (/^\d+$/.test(pureCode)) { 
                        while (pureCode.length < 4) pureCode = "0" + pureCode; 
                        yahooSymbol = pureCode + ".HK"; 
                    }
                }
                positions[codeStr] = { code: codeStr, shares: 0, totalCost: 0, market: marketStr, yahooSymbol: yahooSymbol, firstBuyDate: t.date, isPlannedOnly: false };
            }
            const pos = positions[codeStr];
            if (typeStr === 'BUY') {
                pos.shares += qty; pos.totalCost += amt; cashBalances[marketStr] -= amt;
                if (!pos.firstBuyDate || new Date(t.date) < new Date(pos.firstBuyDate)) pos.firstBuyDate = t.date;
            } else if (typeStr === 'SELL') {
                pos.shares -= qty; cashBalances[marketStr] += amt;
                if (pos.shares <= 0) delete positions[codeStr];
                else pos.totalCost = pos.shares * (pos.totalCost / (pos.shares + qty));
            }
        }
    });

    state.stockPlan.forEach(s => {
        if (!positions[s.code]) {
            let yahooSymbol = s.code;
            if (s.market === 'HK') {
                var pureCode = yahooSymbol.replace(".HK", "").trim();
                if (/^\d+$/.test(pureCode)) { 
                    while (pureCode.length < 4) pureCode = "0" + pureCode; 
                    yahooSymbol = pureCode + ".HK"; 
                }
            }
            positions[s.code] = { code: s.code, shares: 0, totalCost: 0, market: s.market, yahooSymbol: yahooSymbol, firstBuyDate: '---', isPlannedOnly: true };
        }
    });

    let optionsLockedLC = 0; let optionsLockedSP = 0;
    state.optionsTx.forEach(opt => {
        let multiplier = 100 * Number(opt.qty);
        let openVal = Number(opt.open_premium) * multiplier;
        let closeVal = Number(opt.close_premium) * multiplier;
        let strikeVal = Number(opt.strike) * multiplier;

        if (opt.status === 'OPEN') {
            if (opt.strategy === 'Long Call') {
                cashBalances['US'] -= openVal; 
                optionsLockedLC += openVal;    
            } else if (opt.strategy === 'Short Put') {
                cashBalances['US'] += openVal; 
                optionsLockedSP += strikeVal;  
            }
        } else if (opt.status === 'CLOSED') {
            if (opt.strategy === 'Long Call') {
                cashBalances['US'] -= openVal; 
                cashBalances['US'] += closeVal; 
            } else if (opt.strategy === 'Short Put') {
                cashBalances['US'] += openVal; 
                cashBalances['US'] -= closeVal; 
            }
        }
    });

    return { cashBalances, positions, optionsLockedLC, optionsLockedSP };
}
