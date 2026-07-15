// js/charts.js
import { state } from './store.js';

export function parseIntradayTimestamp(str) {
    try {
        const t = str.split(' '); const d = t[0].split('-'); const h = t[1].split(':');
        return Math.floor(Date.UTC(parseInt(d[0], 10), parseInt(d[1], 10) - 1, parseInt(d[2], 10), parseInt(h[0], 10), parseInt(h[1], 10), parseInt(h[2], 10)) / 1000);
    } catch(e) {
        return Math.floor(new Date(str.replace(/-/g, '/')).getTime() / 1000);
    }
}

export async function fetchAndRenderChart(retryCount = 0) {
    const timeframes = ['4H', 'D', 'W', 'M'];
    timeframes.forEach(t => {
        const btn = document.getElementById(`tf-${t}`);
        if (t === state.currentTimeframe) btn.className = "px-4 py-1.5 rounded-md bg-blue-600 text-white shadow-md";
        else btn.className = "px-4 py-1.5 rounded-md text-gray-400 hover:text-gray-200";
    });

    const cacheKey = `${state.currentChartTicker}_${state.currentTimeframe}`;
    const container = document.getElementById('chartContainer');
    const loader = document.getElementById('chartLoadingIndicator');

    if (state.chartCache[cacheKey]) {
        loader.classList.add('hidden'); container.classList.remove('hidden');
        renderChartWithData(state.chartCache[cacheKey], state.currentTimeframe);
        return;
    }

    if (state.avKeysArray.length === 0) {
        container.innerHTML = `<div class="flex items-center justify-center h-full text-xs font-bold text-rose-400">⚠️ 未設定 API KEY！</div>`;
        return;
    }

    container.classList.add('hidden'); loader.classList.remove('hidden');

    let func = "TIME_SERIES_DAILY"; let intervalParam = "";
    if (state.currentTimeframe === 'D') func = "TIME_SERIES_DAILY";
    else if (state.currentTimeframe === 'W') func = "TIME_SERIES_WEEKLY";
    else if (state.currentTimeframe === 'M') func = "TIME_SERIES_MONTHLY";
    else if (state.currentTimeframe === '4H') { func = "TIME_SERIES_INTRADAY"; intervalParam = "&interval=60min"; }

    const currentKey = state.avKeysArray[state.avKeyIndex];
    const url = `https://www.alphavantage.co/query?function=${func}&symbol=${state.currentChartTicker}${intervalParam}&apikey=${currentKey}`;

    try {
        const response = await fetch(url);
        const json = await response.json();

        if (json["Note"] || json["Information"]) {
            if (state.avKeysArray.length > 1 && retryCount < state.avKeysArray.length - 1) {
                state.avKeyIndex = (state.avKeyIndex + 1) % state.avKeysArray.length;
                fetchAndRenderChart(retryCount + 1);
                return;
            }
            loader.classList.add('hidden'); container.classList.remove('hidden');
            container.innerHTML = `<div class="flex flex-col items-center justify-center h-full text-xs font-bold text-amber-400 p-6 text-center">⚠️ 觸發官方頻率或權限限制。請切換週期或稍後再試。</div>`;
            return;
        }

        const formattedData = parseAlphaVantageSeries(json, state.currentTimeframe);
        if (!formattedData || formattedData.length === 0) throw new Error("無數據");

        state.chartCache[cacheKey] = formattedData;
        loader.classList.add('hidden'); container.classList.remove('hidden');
        renderChartWithData(formattedData, state.currentTimeframe);
    } catch (err) {
        loader.classList.add('hidden'); container.classList.remove('hidden');
        container.innerHTML = `<div class="flex flex-col items-center justify-center h-full text-xs font-bold text-rose-400 p-6 text-center">❌ 圖表加載異常：${err.message}</div>`;
    }
}

function parseAlphaVantageSeries(json, timeframe) {
    let key = "Time Series (Daily)";
    if (timeframe === 'W') key = "Weekly Time Series";
    else if (timeframe === 'M') key = "Monthly Time Series";
    else if (timeframe === '4H') key = "Time Series (60min)";

    const rawData = json[key];
    if (!rawData) return null;

    if (timeframe === '4H') {
        let hourlyBars = [];
        for (let timestampStr in rawData) {
            let bar = rawData[timestampStr];
            hourlyBars.push({
                time: parseIntradayTimestamp(timestampStr),
                open: parseFloat(bar["1. open"]), high: parseFloat(bar["2. high"]),
                low: parseFloat(bar["3. low"]), close: parseFloat(bar["4. close"]),
                volume: parseFloat(bar["5. volume"] || 0)
            });
        }
        hourlyBars.sort((a, b) => a.time - b.time);
        let aggregated4H = [];
        for (let i = 0; i < hourlyBars.length; i += 4) {
            let group = hourlyBars.slice(i, i + 4);
            aggregated4H.push({
                time: group[0].time, open: group[0].open,
                high: Math.max(...group.map(g => g.high)), low: Math.min(...group.map(g => g.low)),
                close: group[group.length - 1].close, volume: group.reduce((sum, g) => sum + g.volume, 0)
            });
        }
        return aggregated4H;
    } else {
        let formatted = [];
        for (let dateStr in rawData) {
            let bar = rawData[dateStr];
            formatted.push({
                time: dateStr, open: parseFloat(bar["1. open"]),
                high: parseFloat(bar["2. high"]), low: parseFloat(bar["3. low"]),
                close: parseFloat(bar["4. close"]), volume: parseFloat(bar["5. volume"] || 0)
            });
        }
        formatted.sort((a, b) => new Date(a.time) - new Date(b.time));
        return formatted;
    }
}

function renderChartWithData(chartData, timeframe) {
    const container = document.getElementById('chartContainer');
    container.innerHTML = ''; 

    state.activeChartInstance = LightweightCharts.createChart(container, {
        width: container.clientWidth, height: 384,
        layout: { background: { type: 'solid', color: '#090d16' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#334155' },
        timeScale: { borderColor: '#334155', timeVisible: timeframe === '4H' },
    });

    state.activeSeriesInstance = state.activeChartInstance.addCandlestickSeries({
        upColor: '#10b981', downColor: '#ef4444', borderVisible: false,
        wickUpColor: '#10b981', wickDownColor: '#ef4444'
    });
    state.activeSeriesInstance.setData(chartData);

    const volumeSeries = state.activeChartInstance.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'volume' });
    state.activeChartInstance.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    const volumeData = chartData.map(d => ({ time: d.time, value: d.volume, color: d.close >= d.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)' }));
    volumeSeries.setData(volumeData);
    state.activeChartInstance.timeScale().fitContent();
}
