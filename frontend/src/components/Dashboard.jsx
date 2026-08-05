import React, { useState, useEffect, useCallback } from 'react';
import Charts from './Charts';
import './Dashboard.css';
import { fetchJson, formatNumber } from '../utils/api';
import { getAQIClass, getAQIEmoji, getHealthAdvisory, normalizeAQI } from '../utils/aqi';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Dashboard() {
    const [currentData, setCurrentData] = useState(null);
    const [prediction, setPrediction] = useState(null);
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchAllData = useCallback(async () => {
        try {
            setError(null);

            const [current, predictionData, historyData, statsData] = await Promise.all([
                fetchJson(`${API_URL}/current`),
                fetchJson(`${API_URL}/predict`),
                fetchJson(`${API_URL}/history?limit=24`),
                fetchJson(`${API_URL}/stats`)
            ]);
            setCurrentData(current);
            setPrediction(predictionData);
            setHistory(Array.isArray(historyData.data) ? historyData.data : []);
            setStats(statsData);

            setLastUpdate(new Date());

        } catch (err) {
            console.error('Fetch error:', err);
            setError('Failed to connect to server. Is the backend running?');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAllData();
        const interval = setInterval(fetchAllData, 60000);
        return () => clearInterval(interval);
    }, [fetchAllData]);

    const handleRefresh = async () => {
        setLoading(true);
        try {
            await fetch(`${API_URL}/update`);
            await fetchAllData();
        } catch (err) {
            setError('Failed to update data');
        }
    };

    if (loading && !currentData) {
        return (
            <div className="dashboard container">
                <div className="loading">
                    <div className="spinner"></div>
                </div>
            </div>
        );
    }

    const aqi = normalizeAQI(currentData?.aqi ?? prediction?.AQI_Prediction ?? 0);
    const category = currentData?.category || prediction?.category || 'Unknown';
    const aqiClass = getAQIClass(aqi);

    return (
        <div className="dashboard container">
            {error && (
                <div className="error-banner">
                    ⚠️ {error}
                </div>
            )}

            <div className="dashboard-header">
                <div>
                    <h2>Real-Time AQI Dashboard</h2>
                    {lastUpdate && (
                        <p className="last-update">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </p>
                    )}
                </div>
                <button className="btn btn-primary" onClick={handleRefresh} disabled={loading}>
                    {loading ? '⏳ Updating...' : '🔄 Refresh'}
                </button>
            </div>

            <div className="dashboard-grid">
                <div className={`card aqi-card bg-${aqiClass} fade-in`}>
                    <div className="aqi-header">
                        <span className="location">📍 Current Location</span>
                        <span className={`aqi-badge aqi-${aqiClass}`}>{category}</span>
                    </div>

                    <div className="aqi-display">
                        <span className="aqi-emoji">{getAQIEmoji(aqi)}</span>
                        <span className={`aqi-value aqi-${aqiClass}`}>{Math.round(aqi)}</span>
                        <span className="aqi-label">Air Quality Index</span>
                    </div>

                    <div className="health-advisory">
                        <strong>💡 Health Advisory:</strong>
                        <p>{getHealthAdvisory(aqi)}</p>
                    </div>
                </div>

                <div className="card prediction-card fade-in">
                    <h3>🧬 GA-KELM Prediction</h3>
                    <div className="prediction-display">
                        <span className={`prediction-value aqi-${getAQIClass(prediction?.AQI_Prediction || aqi)}`}>
                            {Math.round(prediction?.AQI_Prediction || aqi)}
                        </span>
                        <span className="prediction-label">Predicted AQI</span>
                    </div>
                    <p className="prediction-note">
                        Powered by Genetic Algorithm optimized Kernel Extreme Learning Machine
                    </p>
                </div>

                <div className="card pollutants-card fade-in">
                    <h3>🌫️ Pollutant Levels</h3>
                    <div className="pollutants-grid">
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.pm25)}</span>
                            <span className="pollutant-label">PM2.5</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.pm10)}</span>
                            <span className="pollutant-label">PM10</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.o3)}</span>
                            <span className="pollutant-label">O₃</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.no2)}</span>
                            <span className="pollutant-label">NO₂</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.so2)}</span>
                            <span className="pollutant-label">SO₂</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{formatNumber(currentData?.co, 2)}</span>
                            <span className="pollutant-label">CO</span>
                            <span className="pollutant-unit">mg/m³</span>
                        </div>
                    </div>
                </div>

                <div className="card stats-card fade-in">
                    <h3>📊 Statistics (24h)</h3>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <span className="stat-value aqi-good">{stats?.min != null ? stats.min : '--'}</span>
                            <span className="stat-label">Min AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value aqi-unhealthy">{stats?.max != null ? stats.max : '--'}</span>
                            <span className="stat-label">Max AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value">{stats?.avg != null ? stats.avg : '--'}</span>
                            <span className="stat-label">Avg AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value">{stats?.count != null ? stats.count : '--'}</span>
                            <span className="stat-label">Readings</span>
                        </div>
                    </div>
                </div>
            </div>

            <Charts history={history} />
        </div>
    );
}

export default Dashboard;
