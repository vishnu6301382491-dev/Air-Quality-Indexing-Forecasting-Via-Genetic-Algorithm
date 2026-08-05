import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Area,
    ComposedChart
} from 'recharts';
import './Charts.css';

// Custom tooltip
function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;

    const data = payload[0].payload;
    return (
        <div className="chart-tooltip">
            <p className="tooltip-time">{label}</p>
            <p className="tooltip-value">AQI: {data.aqi}</p>
            <p className="tooltip-category">{data.category}</p>
        </div>
    );
}

function Charts({ history }) {
    // Format data for chart
    const chartData = history
        .slice()
        .reverse()
        .map((item, index) => {
            const time = item.timestamp
                ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : `T-${history.length - index}`;

            return {
                time,
                aqi: item.aqi || 0,
                pm25: item.pm25 || 0,
                category: item.category || 'Unknown'
            };
        });

    if (!history || history.length === 0) {
        return (
            <div className="card charts-container fade-in">
                <h3>📈 AQI Trend</h3>
                <div className="chart-empty">
                    <p>No historical data available yet.</p>
                    <p>Data will appear after a few readings are collected.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card charts-container fade-in">
            <div className="chart-header">
                <h3>📈 AQI Trend (24 Hours)</h3>
                <div className="chart-legend">
                    <span className="legend-item">
                        <span className="legend-dot good"></span> Good (0-50)
                    </span>
                    <span className="legend-item">
                        <span className="legend-dot moderate"></span> Moderate (51-100)
                    </span>
                    <span className="legend-item">
                        <span className="legend-dot unhealthy"></span> Unhealthy (150+)
                    </span>
                </div>
            </div>

            <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={350}>
                    <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                        <defs>
                            <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(148, 163, 184, 0.1)"
                            vertical={false}
                        />

                        <XAxis
                            dataKey="time"
                            stroke="#64748b"
                            fontSize={12}
                            tickLine={false}
                            axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                        />

                        <YAxis
                            stroke="#64748b"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            domain={[0, 'auto']}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        {/* AQI threshold reference lines */}
                        <ReferenceLine y={50} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={100} stroke="#eab308" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={150} stroke="#f97316" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={200} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />

                        <Area
                            type="monotone"
                            dataKey="aqi"
                            stroke="transparent"
                            fillOpacity={1}
                            fill="url(#colorAqi)"
                        />

                        <Line
                            type="monotone"
                            dataKey="aqi"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6, fill: '#3b82f6', stroke: '#1e293b', strokeWidth: 2 }}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-footer">
                <span>🧬 Data collected every 15 minutes • Model retrained every 24 hours</span>
            </div>
        </div>
    );
}

export default Charts;
