import { useState, useEffect } from 'react';
import api from '../lib/api';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
    LineChart, Line, CartesianGrid, Legend, AreaChart, Area
} from 'recharts';
import { TrendingUp, MapPin, MessageSquare, BarChart3, PieChart as PieIcon } from 'lucide-react';

const COLORS = ['#DC3545', '#FD7E14', '#FFC107', '#28A745', '#2A5FAA', '#D4AF37',
    '#C084FC', '#60A5FA', '#FB923C', '#34D399'];

export default function Analytics() {
    const [overview, setOverview] = useState(null);
    const [trends, setTrends] = useState(null);
    const [sentiment, setSentiment] = useState(null);
    const [geographic, setGeographic] = useState(null);
    const [platforms, setPlatforms] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        Promise.all([
            api.get('/analytics/overview'),
            api.get('/analytics/trends?days=30'),
            api.get('/analytics/sentiment'),
            api.get('/analytics/geographic'),
            api.get('/analytics/platforms')
        ]).then(([overviewRes, trendsRes, sentimentRes, geoRes, platRes]) => {
            setOverview(overviewRes.data);
            setTrends(trendsRes.data);
            setSentiment(sentimentRes.data);
            setGeographic(geoRes.data);
            setPlatforms(platRes.data);
        }).catch(err => {
            console.error('Analytics load error:', err);
            setError(err.message);
        }).finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading"><div className="spinner" /><span>Loading analytics...</span></div>;
    if (error) return <div className="empty-state"><p>Failed to load analytics: {error}</p></div>;

    // Platform distribution pie data from /platforms endpoint
    const platformData = platforms?.data?.map(p => ({ name: p.platform, value: p.count })) || [];

    // Sentiment time series from /sentiment endpoint
    const sentimentTimeline = sentiment?.data || [];

    // Aggregate sentiment totals
    const sentimentTotals = sentimentTimeline.reduce((acc, d) => {
        acc.positive = (acc.positive || 0) + (d.positive || 0);
        acc.negative = (acc.negative || 0) + (d.negative || 0);
        acc.neutral = (acc.neutral || 0) + (d.neutral || 0);
        acc.mixed = (acc.mixed || 0) + (d.mixed || 0);
        return acc;
    }, {});
    const sentimentPieData = Object.entries(sentimentTotals)
        .filter(([_, v]) => v > 0)
        .map(([name, value]) => ({ name, value }));

    // Trends data from /trends endpoint
    const trendItems = trends?.trends || [];
    const wordCloud = trends?.word_cloud || [];

    // Geographic data from /geographic endpoint
    const topDistricts = geographic?.top_districts || [];
    const districtMap = geographic?.districts || {};

    // Sentiment chart data
    const sentimentChartData = sentimentTimeline.map(d => ({
        date: d.date?.slice(5) || '',
        positive: d.positive || 0,
        negative: d.negative || 0,
        neutral: d.neutral || 0
    }));

    return (
        <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10 }}>
                <BarChart3 size={24} /> Analytics Dashboard
            </h2>

            {/* Summary Stats */}
            {overview && (
                <div className="stats-grid" style={{ marginBottom: 24 }}>
                    <div className="stat-card">
                        <div className="stat-info">
                            <div className="stat-value">{overview.total_posts?.toLocaleString()}</div>
                            <div className="stat-label">Total Posts</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-info">
                            <div className="stat-value">{overview.total_alerts?.toLocaleString()}</div>
                            <div className="stat-label">Total Alerts</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-info">
                            <div className="stat-value">{overview.critical_alerts?.toLocaleString()}</div>
                            <div className="stat-label">Critical Alerts</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-info">
                            <div className="stat-value">{overview.platforms_active}</div>
                            <div className="stat-label">Active Platforms</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="analytics-grid">
                {/* Sentiment Timeline */}
                {sentimentChartData.length > 0 && (
                    <div className="chart-container full-width">
                        <div className="chart-title">
                            <TrendingUp size={16} /> Sentiment Over Time (30 Days)
                        </div>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={sentimentChartData}>
                                <defs>
                                    <linearGradient id="gradNeg" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#DC3545" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#DC3545" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="gradPos" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#28A745" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#28A745" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2A3544" />
                                <XAxis dataKey="date" stroke="#64748B" fontSize={11} />
                                <YAxis stroke="#64748B" fontSize={11} />
                                <Tooltip
                                    contentStyle={{ background: '#1A2332', border: '1px solid #2A3544', borderRadius: 8 }}
                                    labelStyle={{ color: '#F1F5F9' }}
                                />
                                <Legend />
                                <Area type="monotone" dataKey="negative" stroke="#DC3545" fill="url(#gradNeg)" strokeWidth={2} name="Negative" />
                                <Area type="monotone" dataKey="positive" stroke="#28A745" fill="url(#gradPos)" strokeWidth={2} name="Positive" />
                                <Line type="monotone" dataKey="neutral" stroke="#64748B" strokeWidth={1.5} dot={false} name="Neutral" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Platform Distribution */}
                {platformData.length > 0 && (
                    <div className="chart-container">
                        <div className="chart-title">
                            <PieIcon size={16} /> Platform Distribution
                        </div>
                        <ResponsiveContainer width="100%" height={260}>
                            <PieChart>
                                <Pie data={platformData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                                    innerRadius={50} outerRadius={90}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    labelLine={false}
                                >
                                    {platformData.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1A2332', border: '1px solid #2A3544', borderRadius: 8 }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Sentiment Pie */}
                {sentimentPieData.length > 0 && (
                    <div className="chart-container">
                        <div className="chart-title"><MessageSquare size={16} /> Sentiment Breakdown</div>
                        <ResponsiveContainer width="100%" height={260}>
                            <PieChart>
                                <Pie data={sentimentPieData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                                    outerRadius={90}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                >
                                    {sentimentPieData.map((entry, i) => (
                                        <Cell key={i} fill={
                                            entry.name === 'negative' ? '#DC3545' :
                                                entry.name === 'positive' ? '#28A745' :
                                                    entry.name === 'neutral' ? '#64748B' : '#FFC107'
                                        } />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1A2332', border: '1px solid #2A3544', borderRadius: 8 }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Top Districts */}
                {topDistricts.length > 0 && (
                    <div className="chart-container">
                        <div className="chart-title"><MapPin size={16} /> Top Districts by Alerts</div>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={topDistricts} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="#2A3544" />
                                <XAxis type="number" stroke="#64748B" fontSize={11} />
                                <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={11} width={100} />
                                <Tooltip contentStyle={{ background: '#1A2332', border: '1px solid #2A3544', borderRadius: 8 }} />
                                <Bar dataKey="count" barSize={20} radius={[0, 6, 6, 0]} fill="#2A5FAA" name="Alerts" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Trending Topics */}
                {trendItems.length > 0 && (
                    <div className="chart-container">
                        <div className="chart-title"><TrendingUp size={16} /> Trending Topics</div>
                        <div className="top-list">
                            {trendItems.map((item, i) => (
                                <div key={i} className="top-list-item">
                                    <span className="top-list-rank">{i + 1}</span>
                                    <span className="top-list-name">{item.topic}</span>
                                    <span className="top-list-count">{item.count} mentions</span>
                                    <span className={`top-list-change ${item.direction}`}>
                                        {item.direction === 'up' ? '↑' : item.direction === 'down' ? '↓' : '—'}
                                        {Math.abs(item.change_percent)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Geographic Heat Grid */}
                {Object.keys(districtMap).length > 0 && (
                    <div className="chart-container full-width">
                        <div className="chart-title"><MapPin size={16} /> District-wise Alert Distribution</div>
                        <div className="map-overlay">
                            {Object.entries(districtMap)
                                .sort(([, a], [, b]) => b - a)
                                .map(([district, count]) => {
                                    const intensity = count > 15 ? 0.8 : count > 10 ? 0.5 : count > 5 ? 0.3 : count > 0 ? 0.15 : 0.05;
                                    const bgColor = count > 10
                                        ? `rgba(220, 53, 69, ${intensity})`
                                        : count > 5
                                            ? `rgba(253, 126, 20, ${intensity})`
                                            : `rgba(31, 71, 136, ${intensity})`;
                                    return (
                                        <div key={district} className="district-cell" style={{ background: bgColor }}>
                                            <div>{district}</div>
                                            <div className="district-count">{count}</div>
                                        </div>
                                    );
                                })}
                        </div>
                    </div>
                )}

                {/* Word Cloud */}
                {wordCloud.length > 0 && (
                    <div className="chart-container full-width">
                        <div className="chart-title"><TrendingUp size={16} /> Entity Word Cloud</div>
                        <div className="word-cloud">
                            {wordCloud.map((item, i) => (
                                <span key={i} className="word-cloud-item"
                                    style={{ fontSize: `${Math.max(12, Math.min(28, 10 + item.value * 2))}px` }}>
                                    {item.text}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
