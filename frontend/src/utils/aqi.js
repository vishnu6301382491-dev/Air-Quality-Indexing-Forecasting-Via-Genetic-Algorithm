export const AQI_LEVELS = Object.freeze([
    { max: 50, className: 'good', label: 'Good', emoji: '😊', advice: 'Air quality is satisfactory. Enjoy outdoor activities!' },
    { max: 100, className: 'moderate', label: 'Moderate', emoji: '🙂', advice: 'Air quality is acceptable. Unusually sensitive people should reduce prolonged outdoor exertion.' },
    { max: 150, className: 'sensitive', label: 'Unhealthy for Sensitive Groups', emoji: '😐', advice: 'Sensitive groups should reduce prolonged outdoor exertion.' },
    { max: 200, className: 'unhealthy', label: 'Unhealthy', emoji: '😷', advice: 'Everyone may begin to experience health effects. Limit outdoor activities.' },
    { max: 300, className: 'very-unhealthy', label: 'Very Unhealthy', emoji: '🤢', advice: 'Health warnings. Everyone should avoid outdoor activities.' },
    { max: Number.POSITIVE_INFINITY, className: 'hazardous', label: 'Hazardous', emoji: '💀', advice: 'Emergency conditions! Stay indoors and keep windows closed.' }
]);

export function normalizeAQI(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 ? number : fallback;
}

export function getAQIInfo(value) {
    const aqi = normalizeAQI(value);
    return AQI_LEVELS.find((level) => aqi <= level.max) || AQI_LEVELS[AQI_LEVELS.length - 1];
}

export const getAQIClass = (value) => getAQIInfo(value).className;
export const getAQIEmoji = (value) => getAQIInfo(value).emoji;
export const getHealthAdvisory = (value) => getAQIInfo(value).advice;
