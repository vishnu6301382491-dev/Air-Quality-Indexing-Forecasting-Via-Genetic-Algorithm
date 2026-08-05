import React, { useState, useEffect, useCallback } from 'react';
import { useLocationData } from '../App';
import './HomePage.css';
import { fetchJson } from '../utils/api';

// Popular Indian Cities
const POPULAR_CITIES = [
    { name: 'Delhi', lat: 28.6139, lon: 77.2090 },
    { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
    { name: 'Bangalore', lat: 12.9716, lon: 77.5946 },
    { name: 'Hyderabad', lat: 17.3850, lon: 78.4867 },
    { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
    { name: 'Kolkata', lat: 22.5726, lon: 88.3639 },
    { name: 'Pune', lat: 18.5204, lon: 73.8567 },
    { name: 'Ahmedabad', lat: 23.0225, lon: 72.5714 },
    { name: 'Jaipur', lat: 26.9124, lon: 75.7873 },
    { name: 'Lucknow', lat: 26.8467, lon: 80.9462 },
];

// AQI Info Helper (no emojis)
const getAQIInfo = (aqi) => {
    if (aqi <= 50) return { level: 'good', color: '#00e400', bg: 'rgba(0,228,0,0.15)', label: 'Good' };
    if (aqi <= 100) return { level: 'moderate', color: '#ffff00', bg: 'rgba(255,255,0,0.12)', label: 'Moderate' };
    if (aqi <= 150) return { level: 'sensitive', color: '#ff7e00', bg: 'rgba(255,126,0,0.12)', label: 'Unhealthy for Sensitive' };
    if (aqi <= 200) return { level: 'unhealthy', color: '#ff0000', bg: 'rgba(255,0,0,0.12)', label: 'Unhealthy' };
    if (aqi <= 300) return { level: 'very-unhealthy', color: '#8f3f97', bg: 'rgba(143,63,151,0.12)', label: 'Very Unhealthy' };
    return { level: 'hazardous', color: '#7e0023', bg: 'rgba(126,0,35,0.12)', label: 'Hazardous' };
};

// Professional Trend Chart with Threshold Lines
const TrendChart = ({ data }) => {
    if (!data || data.length === 0) return <div className="no-data">No trend data available</div>;

    const maxVal = Math.max(250, Math.max(...data) + 20);
    const minVal = 0;

    // Threshold levels
    const thresholds = [
        { value: 50, label: 'Good', color: '#00e400' },
        { value: 100, label: 'Moderate', color: '#ffff00' },
        { value: 150, label: 'Sensitive', color: '#ff7e00' },
        { value: 200, label: 'Unhealthy', color: '#ff0000' },
    ];

    const getY = (val) => ((maxVal - val) / (maxVal - minVal)) * 180;

    // Create smooth curve points
    const pathPoints = data.map((val, i) => {
        const x = 50 + (i / (data.length - 1)) * 700;
        const y = 20 + getY(val);
        return { x, y };
    });

    // Create smooth bezier curve
    let pathD = `M ${pathPoints[0].x} ${pathPoints[0].y}`;
    for (let i = 1; i < pathPoints.length; i++) {
        const prev = pathPoints[i - 1];
        const curr = pathPoints[i];
        const cpx = (prev.x + curr.x) / 2;
        pathD += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
    }

    // Area fill path
    const areaD = pathD + ` L ${pathPoints[pathPoints.length - 1].x} 200 L ${pathPoints[0].x} 200 Z`;

    return (
        <svg viewBox="0 0 800 220" className="trend-chart-svg">
            <defs>
                <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
                </linearGradient>
            </defs>

            {/* Threshold lines */}
            {thresholds.map((t) => (
                <g key={t.value}>
                    <line
                        x1="50" y1={20 + getY(t.value)}
                        x2="750" y2={20 + getY(t.value)}
                        stroke={t.color}
                        strokeWidth="1"
                        strokeDasharray="5,5"
                        opacity="0.6"
                    />
                    <text x="755" y={24 + getY(t.value)} fill={t.color} fontSize="11" fontWeight="500">
                        {t.label}
                    </text>
                </g>
            ))}

            {/* Y-axis labels */}
            {[0, 50, 100, 150, 200].map((val) => (
                <text key={val} x="40" y={24 + getY(val)} fill="#64748b" fontSize="11" textAnchor="end">
                    {val}
                </text>
            ))}

            {/* Area fill */}
            <path d={areaD} fill="url(#areaGradient)" />

            {/* Main line */}
            <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

            {/* Data points */}
            {pathPoints.map((p, i) => (
                <circle key={i} cx={p.x} cy={p.y} r="4" fill="#3b82f6" stroke="#fff" strokeWidth="2" />
            ))}
        </svg>
    );
};

function HomePage() {
    const { userLocation, locationName, API_URL, requestLocation } = useLocationData();
    const [currentData, setCurrentData] = useState(null);
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedCity, setSelectedCity] = useState(null);
    const [citySearch, setCitySearch] = useState('');
    const [savedCities, setSavedCities] = useState([]);
    const [cityData, setCityData] = useState({});
    const [showCityPanel, setShowCityPanel] = useState(false);
    const [trendData, setTrendData] = useState([]);

    // Fetch data for a location
    const fetchLocationData = useCallback(async (lat, lon, isMain = false) => {
        try {
            const [currentJson, predJson, trendJson] = await Promise.all([
                fetchJson(`${API_URL}/current?lat=${lat}&lon=${lon}`),
                fetchJson(`${API_URL}/predict?lat=${lat}&lon=${lon}`),
                fetchJson(`${API_URL}/trend?lat=${lat}&lon=${lon}&hours=24`)
            ]);

            if (isMain) {
                setCurrentData(currentJson);
                setPrediction(predJson);
                setTrendData(Array.isArray(trendJson.trend) ? trendJson.trend : []);
            }

            return { current: currentJson, prediction: predJson, trend: trendJson };
        } catch (err) {
            console.error('Fetch error:', err);
            return null;
        }
    }, [API_URL]);

    // Initial load
    useEffect(() => {
        if (userLocation) {
            setLoading(true);
            fetchLocationData(userLocation.lat, userLocation.lon, true)
                .finally(() => setLoading(false));
        }
    }, [userLocation, fetchLocationData]);

    // Fetch saved cities data
    useEffect(() => {
        savedCities.forEach(async (city) => {
            if (!cityData[city.name]) {
                const data = await fetchLocationData(city.lat, city.lon);
                if (data) {
                    setCityData(prev => ({ ...prev, [city.name]: data }));
                }
            }
        });
    }, [savedCities, fetchLocationData, cityData]);

    const addCity = (city) => {
        if (!savedCities.find(c => c.name === city.name)) {
            setSavedCities(prev => [...prev, city]);
        }
        setCitySearch('');
    };

    const removeCity = (cityName) => {
        setSavedCities(prev => prev.filter(c => c.name !== cityName));
        setCityData(prev => { const d = { ...prev }; delete d[cityName]; return d; });
    };

    const selectCity = async (city) => {
        setSelectedCity(city);
        setLoading(true);
        await fetchLocationData(city.lat, city.lon, true);
        setLoading(false);
    };

    const backToMyLocation = async () => {
        setSelectedCity(null);
        if (userLocation) {
            setLoading(true);
            await fetchLocationData(userLocation.lat, userLocation.lon, true);
            setLoading(false);
        }
    };

    const filteredCities = POPULAR_CITIES.filter(city =>
        city.name.toLowerCase().includes(citySearch.toLowerCase()) &&
        !savedCities.find(c => c.name === city.name)
    );

    const aqi = currentData?.aqi || 0;
    const aqiInfo = getAQIInfo(aqi);
    const weather = currentData?.weather || {};
    const displayName = selectedCity ? selectedCity.name : locationName;

    if (loading && !currentData) {
        return (
            <div className="home-page">
                <div className="loading-screen">
                    <div className="loader"></div>
                    <p>Detecting your location...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="home-page">
            {/* Sidebar */}
            <aside className={`city-sidebar ${showCityPanel ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <h3>Locations</h3>
                    <button className="close-btn" onClick={() => setShowCityPanel(false)}>×</button>
                </div>

                <div
                    className={`city-item my-location ${!selectedCity ? 'active' : ''}`}
                    onClick={backToMyLocation}
                >
                    <div className="city-info">
                        <div className="city-icon home-icon"></div>
                        <div>
                            <span className="city-name">{locationName}</span>
                            <span className="city-label">My Location</span>
                        </div>
                    </div>
                    <span className="city-aqi" style={{ color: getAQIInfo(currentData?.aqi || 0).color }}>
                        {currentData?.aqi || '--'}
                    </span>
                </div>

                {savedCities.map(city => {
                    const data = cityData[city.name];
                    const cityAqi = data?.current?.aqi || 0;
                    const info = getAQIInfo(cityAqi);
                    return (
                        <div
                            key={city.name}
                            className={`city-item ${selectedCity?.name === city.name ? 'active' : ''}`}
                            onClick={() => selectCity(city)}
                        >
                            <div className="city-info">
                                <div className="city-icon"></div>
                                <div>
                                    <span className="city-name">{city.name}</span>
                                    <span className="city-label">{info.label}</span>
                                </div>
                            </div>
                            <div className="city-aqi-wrap">
                                <span className="city-aqi" style={{ color: info.color }}>{cityAqi || '--'}</span>
                                <button className="remove-btn" onClick={(e) => { e.stopPropagation(); removeCity(city.name); }}>×</button>
                            </div>
                        </div>
                    );
                })}

                <div className="add-city-section">
                    <input
                        type="text"
                        placeholder="Search city..."
                        value={citySearch}
                        onChange={(e) => setCitySearch(e.target.value)}
                        className="city-search"
                    />
                    {citySearch && (
                        <div className="city-suggestions">
                            {filteredCities.map(city => (
                                <div key={city.name} className="suggestion-item" onClick={() => addCity(city)}>
                                    <span>{city.name}</span>
                                    <span className="add-icon">+</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </aside>

            <button className="mobile-city-toggle" onClick={() => setShowCityPanel(true)}>
                Cities
            </button>

            {/* Main Content */}
            <main className="main-content">
                {/* Header */}
                <header className="page-header">
                    <div className="header-left">
                        <div className="live-badge">
                            <span className="pulse"></span>
                            LIVE
                        </div>
                        <div className="location-info">
                            <h1>{displayName}</h1>
                            <p className="station-name">Data from: {currentData?.station || 'Nearest Station'}</p>
                        </div>
                    </div>
                    <div className="header-right">
                        <button className="btn-secondary" onClick={requestLocation}>Locate Me</button>
                        <button className="btn-primary" onClick={() => fetchLocationData(
                            selectedCity?.lat || userLocation?.lat,
                            selectedCity?.lon || userLocation?.lon,
                            true
                        )}>Refresh</button>
                    </div>
                </header>

                {/* AQI Main Display */}
                <section className="aqi-main-display">
                    <div className="aqi-card-large" style={{ borderColor: aqiInfo.color }}>
                        <div className="aqi-value-section">
                            <span className="aqi-value" style={{ color: aqiInfo.color }}>{aqi}</span>
                            <span className="aqi-unit">AQI (US)</span>
                        </div>
                        <div className="aqi-info-section">
                            <div className="aqi-category" style={{ background: aqiInfo.color, color: aqi > 100 ? '#fff' : '#000' }}>
                                {aqiInfo.label}
                            </div>
                            <div className="pollutant-row">
                                <div className="pollutant-item">
                                    <span className="poll-label">PM2.5</span>
                                    <span className="poll-value">{currentData?.pm25 || 0} µg/m³</span>
                                </div>
                                <div className="pollutant-item">
                                    <span className="poll-label">PM10</span>
                                    <span className="poll-value">{currentData?.pm10 || 0} µg/m³</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="weather-card">
                        <div className="weather-temp">{weather.temperature || 25}°C</div>
                        <div className="weather-condition">{weather.weather || 'Clear'}</div>
                        <div className="weather-details">
                            <span>Humidity: {weather.humidity || 60}%</span>
                            <span>Wind: {weather.wind_speed || 10} km/h</span>
                            <span>UV: {weather.uv_index || 0}</span>
                        </div>
                    </div>

                    <div className="prediction-card" style={{ borderColor: getAQIInfo(prediction?.AQI_Prediction || aqi).color }}>
                        <div className="pred-label">Next Hour Prediction</div>
                        <div className="pred-value" style={{ color: getAQIInfo(prediction?.AQI_Prediction || aqi).color }}>
                            {prediction?.AQI_Prediction || aqi}
                        </div>
                        <div className="pred-category">{prediction?.category || aqiInfo.label}</div>
                        <div className="pred-model">
                            {prediction?.model_trained ? 'GA-KELM Model' : 'EPA Formula'}
                        </div>
                    </div>
                </section>

                {/* Trend Chart */}
                <section className="trend-section">
                    <h3>AQI Trend (Last 24 Readings)</h3>
                    <div className="trend-chart-container">
                        <TrendChart data={trendData} />
                    </div>
                    <div className="trend-stats-row">
                        <div className="trend-stat">
                            <span className="stat-label">Current</span>
                            <span className="stat-value">{aqi}</span>
                        </div>
                        <div className="trend-stat">
                            <span className="stat-label">Average</span>
                            <span className="stat-value">{trendData.length ? Math.round(trendData.reduce((a, b) => a + b, 0) / trendData.length) : aqi}</span>
                        </div>
                        <div className="trend-stat">
                            <span className="stat-label">Max</span>
                            <span className="stat-value">{trendData.length ? Math.max(...trendData) : aqi}</span>
                        </div>
                        <div className="trend-stat">
                            <span className="stat-label">Min</span>
                            <span className="stat-value">{trendData.length ? Math.min(...trendData) : aqi}</span>
                        </div>
                    </div>
                </section>

                {/* Pollutants Grid */}
                <section className="pollutants-section">
                    <h3>Pollutant Levels</h3>
                    <div className="pollutants-grid">
                        {[
                            { name: 'PM2.5', value: currentData?.pm25, unit: 'µg/m³', color: '#ef4444' },
                            { name: 'PM10', value: currentData?.pm10, unit: 'µg/m³', color: '#f97316' },
                            { name: 'NO₂', value: currentData?.no2, unit: 'µg/m³', color: '#eab308' },
                            { name: 'O₃', value: currentData?.o3, unit: 'µg/m³', color: '#22c55e' },
                            { name: 'SO₂', value: currentData?.so2, unit: 'µg/m³', color: '#3b82f6' },
                            { name: 'CO', value: currentData?.co, unit: 'mg/m³', color: '#8b5cf6' },
                        ].map(poll => (
                            <div key={poll.name} className="pollutant-card">
                                <div className="poll-indicator" style={{ background: poll.color }}></div>
                                <span className="poll-name">{poll.name}</span>
                                <span className="poll-value">{poll.value || 0}</span>
                                <span className="poll-unit">{poll.unit}</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* City Comparison */}
                {savedCities.length > 0 && (
                    <section className="comparison-section">
                        <h3>City Comparison</h3>
                        <div className="comparison-grid">
                            <div className="comp-card">
                                <span className="comp-name">{locationName}</span>
                                <span className="comp-aqi" style={{ color: getAQIInfo(currentData?.aqi || 0).color }}>
                                    {currentData?.aqi || '--'}
                                </span>
                                <span className="comp-label">{getAQIInfo(currentData?.aqi || 0).label}</span>
                            </div>
                            {savedCities.slice(0, 4).map(city => {
                                const data = cityData[city.name];
                                const cityAqi = data?.current?.aqi || 0;
                                const info = getAQIInfo(cityAqi);
                                return (
                                    <div key={city.name} className="comp-card" onClick={() => selectCity(city)}>
                                        <span className="comp-name">{city.name}</span>
                                        <span className="comp-aqi" style={{ color: info.color }}>{cityAqi || '--'}</span>
                                        <span className="comp-label">{info.label}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                )}

                <footer className="home-footer">
                    <p>Powered by GA-KELM Machine Learning | Data: {currentData?.source || 'WAQI'}</p>
                </footer>
            </main>
        </div>
    );
}

export default HomePage;
