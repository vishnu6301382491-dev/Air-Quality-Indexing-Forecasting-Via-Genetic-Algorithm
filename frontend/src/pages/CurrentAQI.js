import React, { useState, useEffect, useCallback } from 'react';
import { useLocationData } from '../App';
import './CurrentAQI.css';
import { fetchJson, formatNumber } from '../utils/api';
import { getAQIClass, getAQIEmoji, getHealthAdvisory } from '../utils/aqi';

function CurrentAQI() {
    const { userLocation, locationName, isLoadingLocation, API_URL } = useLocationData();
    const [data, setData] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchData = useCallback(async () => {
        if (!userLocation) return;
        setLoading(true);
        try {
            const [currentData, statsData] = await Promise.all([
                fetchJson(`${API_URL}/current?lat=${userLocation.lat}&lon=${userLocation.lon}`),
                fetchJson(`${API_URL}/stats`)
            ]);

            setData(currentData);
            setStats(statsData);
            setLastUpdate(new Date());
        } catch (err) {
            console.error('Error:', err);
        }
        setLoading(false);
    }, [API_URL, userLocation]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    if (isLoadingLocation || loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading current air quality data...</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="error-state">
                <h2>Unable to load data</h2>
                <button onClick={fetchData} className="btn btn-primary">Retry</button>
            </div>
        );
    }

    const aqiClass = getAQIClass(data.aqi);

    return (
        <div className="current-page fade-in">
            <div className="page-header">
                <h1 className="page-title">Current Air Quality</h1>
                <p className="page-subtitle">
                    📍 Real-time data for <strong>{locationName}</strong>
                </p>
                {lastUpdate && (
                    <p className="last-update">
                        Last updated: {lastUpdate.toLocaleTimeString()}
                        <button onClick={fetchData} className="refresh-btn">🔄 Refresh</button>
                    </p>
                )}
            </div>

            {/* Main AQI Card */}
            <div className={`main-aqi-card ${aqiClass}`}>
                <div className="aqi-visual">
                    <div className="aqi-emoji">{getAQIEmoji(data.aqi)}</div>
                    <div className="aqi-number">{data.aqi}</div>
                    <div className="aqi-label">Air Quality Index</div>
                </div>
                <div className="aqi-info">
                    <div className={`aqi-badge ${aqiClass}`}>{data.category}</div>
                    <div className="health-advice">
                        <h3>💡 Health Advisory</h3>
                        <p>{getHealthAdvisory(data.aqi)}</p>
                    </div>
                </div>
            </div>

            {/* Pollutants Grid */}
            <section className="section">
                <h2 className="section-title">🧪 Pollutant Levels</h2>
                <div className="pollutants-grid">
                    <div className="pollutant-card">
                        <div className="pollutant-name">PM2.5</div>
                        <div className="pollutant-value">{formatNumber(data.pm25)}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Fine particles</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">PM10</div>
                        <div className="pollutant-value">{formatNumber(data.pm10)}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Coarse particles</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">O₃</div>
                        <div className="pollutant-value">{formatNumber(data.o3)}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Ozone</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">NO₂</div>
                        <div className="pollutant-value">{formatNumber(data.no2)}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Nitrogen dioxide</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">SO₂</div>
                        <div className="pollutant-value">{formatNumber(data.so2)}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Sulfur dioxide</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">CO</div>
                        <div className="pollutant-value">{formatNumber(data.co, 2)}</div>
                        <div className="pollutant-unit">mg/m³</div>
                        <div className="pollutant-desc">Carbon monoxide</div>
                    </div>
                </div>
            </section>

            {/* Statistics */}
            {stats && stats.count > 0 && (
                <section className="section">
                    <h2 className="section-title">📊 24-Hour Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <div className="stat-icon">⬇️</div>
                            <div className="stat-value aqi-good">{stats.min}</div>
                            <div className="stat-label">Minimum AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">⬆️</div>
                            <div className="stat-value aqi-unhealthy">{stats.max}</div>
                            <div className="stat-label">Maximum AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">📈</div>
                            <div className="stat-value">{stats.avg}</div>
                            <div className="stat-label">Average AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">📝</div>
                            <div className="stat-value">{stats.count}</div>
                            <div className="stat-label">Data Points</div>
                        </div>
                    </div>
                </section>
            )}

            {/* Location Info */}
            <section className="section location-info">
                <h2 className="section-title">📍 Location Details</h2>
                <div className="location-grid">
                    <div className="location-item">
                        <strong>Latitude:</strong> {data.latitude}
                    </div>
                    <div className="location-item">
                        <strong>Longitude:</strong> {data.longitude}
                    </div>
                    <div className="location-item">
                        <strong>Data Source:</strong> {data.source}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default CurrentAQI;
