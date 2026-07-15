// js/api.js
import { state } from './store.js';

export async function fetchInitData() { 
    const fetchUrl = state.API_URL + "?token=" + encodeURIComponent(state.userGoogleToken);
    const response = await fetch(fetchUrl);
    const data = await response.json();
    if (data.result === 'error') throw new Error(data.error);
    return data;
}

export async function executeGasAction(action, payload) {
    const body = { action: action, token: state.userGoogleToken, ...payload };
    const response = await fetch(state.API_URL, { 
        method: "POST", 
        mode: "no-cors", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body) 
    });
    return response;
}
