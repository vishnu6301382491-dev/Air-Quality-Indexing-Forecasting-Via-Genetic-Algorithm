export async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    let body;
    try {
        body = await response.json();
    } catch {
        throw new Error(`Server returned an invalid response (${response.status})`);
    }
    if (!response.ok) {
        const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`;
        throw new Error(detail);
    }
    if (!body || typeof body !== 'object') {
        throw new Error('Server returned an invalid response body');
    }
    return body;
}

export function isNumber(value) {
    return typeof value === 'number' && Number.isFinite(value);
}

export function formatNumber(value, digits = 1, fallback = '--') {
    return isNumber(Number(value)) ? Number(value).toFixed(digits) : fallback;
}
