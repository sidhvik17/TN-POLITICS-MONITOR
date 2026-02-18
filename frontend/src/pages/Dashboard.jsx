import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import {
    AlertTriangle, Shield, Activity, MapPin, Search, Clock,
    AlertCircle, CheckCircle2, Eye, TrendingUp
} from 'lucide-react';

const SEVERITY_ICONS = {
    CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🟢'
};

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return `${Math.floor(diff)}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

export default function Dashboard() {
    const navigate = useNavigate();
    const [alerts, setAlerts] = useState([]);
    const [stats, setStats] = useState(null);
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [filters, setFilters] = useState({
        severity: '', status: '', search: ''
    });

    const fetchAlerts = async () => {
        try {
            const params = { page, limit: 20 };
            if (filters.severity) params.severity = filters.severity;
            if (filters.status) params.status = filters.status;
            if (filters.search) params.search = filters.search;
            const res = await api.get('/alerts', { params });
            setAlerts(res.data.data);
            setTotal(res.data.total);
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        }
    };

    const fetchStats = async () => {
        try {
            const [statsRes, overviewRes] = await Promise.all([
                api.get('/alerts/stats'),
                api.get('/analytics/overview')
            ]);
            setStats(statsRes.data);
            setOverview(overviewRes.data);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    };

    useEffect(() => {
        Promise.all([fetchAlerts(), fetchStats()]).finally(() => setLoading(false));
        const interval = setInterval(fetchAlerts, 30000);
        return () => clearInterval(interval);
    }, [page, filters.severity, filters.status]);

    useEffect(() => {
        const debounce = setTimeout(fetchAlerts, 500);
        return () => clearTimeout(debounce);
    }, [filters.search]);

    const criticalCount = stats?.by_severity?.CRITICAL || 0;
    const highCount = stats?.by_severity?.HIGH || 0;
    const mediumCount = stats?.by_severity?.MEDIUM || 0;
    const activeCount = (stats?.by_status?.NEW || 0) + (stats?.by_status?.IN_REVIEW || 0);

    if (loading) {
        return <div className="loading"><div className="spinner" /><span>Loading alerts...</span></div>;
    }

    return (
        <div>
            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card" onClick={() => setFilters(f => ({ ...f, severity: 'CRITICAL' }))}>
                    <div className="stat-icon critical"><AlertTriangle size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{criticalCount}</div>
                        <div className="stat-label">Critical Alerts</div>
                    </div>
                </div>
                <div className="stat-card" onClick={() => setFilters(f => ({ ...f, severity: 'HIGH' }))}>
                    <div className="stat-icon high"><AlertCircle size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{highCount}</div>
                        <div className="stat-label">High Priority</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue"><Activity size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{activeCount}</div>
                        <div className="stat-label">Active Alerts</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon gold"><TrendingUp size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{overview?.total_posts?.toLocaleString()}</div>
                        <div className="stat-label">Posts Monitored</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon low"><CheckCircle2 size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{overview?.resolved_today || 0}</div>
                        <div className="stat-label">Resolved Today</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon gold"><MapPin size={24} /></div>
                    <div className="stat-info">
                        <div className="stat-value">{overview?.districts_monitored}</div>
                        <div className="stat-label">Districts Monitored</div>
                    </div>
                </div>
            </div>

            {/* Critical Alert Banner */}
            {criticalCount > 0 && (
                <div className="alert-banner">
                    <span className="alert-banner-icon">⚠️</span>
                    <div className="alert-banner-text">
                        <strong>{criticalCount} CRITICAL</strong> alert{criticalCount > 1 ? 's' : ''} requiring immediate attention
                        {' | '}
                        <strong>{highCount} HIGH</strong> priority alert{highCount > 1 ? 's' : ''} pending review
                        {' | '}
                        <strong>{mediumCount}</strong> medium priority
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="filters-bar">
                <select
                    className="filter-select"
                    value={filters.severity}
                    onChange={(e) => { setFilters(f => ({ ...f, severity: e.target.value })); setPage(1); }}
                >
                    <option value="">All Severities</option>
                    <option value="CRITICAL">🔴 Critical</option>
                    <option value="HIGH">🟠 High</option>
                    <option value="MEDIUM">🟡 Medium</option>
                    <option value="LOW">🟢 Low</option>
                </select>

                <select
                    className="filter-select"
                    value={filters.status}
                    onChange={(e) => { setFilters(f => ({ ...f, status: e.target.value })); setPage(1); }}
                >
                    <option value="">All Statuses</option>
                    <option value="NEW">New</option>
                    <option value="IN_REVIEW">In Review</option>
                    <option value="ACTIONABLE">Actionable</option>
                    <option value="FALSE_POSITIVE">False Positive</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="ESCALATED">Escalated</option>
                </select>

                <div className="search-wrapper">
                    <Search size={16} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search alerts, authors, content..."
                        value={filters.search}
                        onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
                    />
                </div>
            </div>

            {/* Alert List */}
            <div className="alert-list">
                {alerts.map((alert) => (
                    <div
                        key={alert.id}
                        className={`alert-item severity-${alert.severity}`}
                        onClick={() => navigate(`/alerts/${alert.id}`)}
                    >
                        <span className={`alert-severity ${alert.severity}`}>
                            {SEVERITY_ICONS[alert.severity]} {alert.severity}
                        </span>

                        <div className="alert-content">
                            <div className="alert-title">
                                #{alert.id} — {alert.alert_type?.replace(/_/g, ' ')}
                            </div>
                            <div className="alert-text">
                                {alert.post?.translated_content || alert.post?.content || alert.description}
                            </div>
                            <div className="alert-meta">
                                <span className="alert-meta-item">
                                    <Eye size={12} /> {alert.post?.platform}
                                </span>
                                <span className="alert-meta-item">
                                    @{alert.post?.author_name}
                                </span>
                                {alert.post?.district && (
                                    <span className="alert-meta-item">
                                        <MapPin size={12} /> {alert.post.district}
                                    </span>
                                )}
                                {alert.analysis?.confidence_score && (
                                    <span className="alert-meta-item">
                                        Confidence: {Math.round(alert.analysis.confidence_score * 100)}%
                                    </span>
                                )}
                            </div>
                        </div>

                        <div className="alert-actions">
                            <div className="alert-time">
                                <Clock size={12} style={{ marginRight: 4 }} />
                                {timeAgo(alert.created_at)}
                            </div>
                            <span className={`alert-status ${alert.status}`}>
                                {alert.status?.replace('_', ' ')}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            {alerts.length === 0 && (
                <div className="empty-state">
                    <div className="empty-state-icon">🔍</div>
                    <p>No alerts match your filters</p>
                </div>
            )}

            {/* Pagination */}
            {total > 20 && (
                <div className="pagination">
                    <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>Previous</button>
                    <span className="pagination-info">
                        Page {page} of {Math.ceil(total / 20)} ({total} alerts)
                    </span>
                    <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}>Next</button>
                </div>
            )}
        </div>
    );
}
