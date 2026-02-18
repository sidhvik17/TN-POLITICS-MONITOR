import { useState, useEffect } from 'react';
import api from '../lib/api';
import {
    Settings, Users, Key, Activity, Plus, X, Shield,
    Server, Database, Cpu, Wifi
} from 'lucide-react';

export default function Admin() {
    const [activeTab, setActiveTab] = useState('keywords');
    const [keywordsGrouped, setKeywordsGrouped] = useState({});
    const [keywordsTotal, setKeywordsTotal] = useState(0);
    const [users, setUsers] = useState([]);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [newKeyword, setNewKeyword] = useState('');
    const [newCategory, setNewCategory] = useState('political_parties');
    const [showUserModal, setShowUserModal] = useState(false);
    const [newUser, setNewUser] = useState({ username: '', email: '', password: '', full_name: '', role: 'analyst' });

    useEffect(() => {
        setLoading(true);
        if (activeTab === 'keywords') {
            api.get('/admin/keywords').then(res => {
                const data = res.data || {};
                setKeywordsGrouped(data.keywords || {});
                setKeywordsTotal(data.total || 0);
            }).catch(console.error).finally(() => setLoading(false));
        } else if (activeTab === 'users') {
            api.get('/admin/users').then(res => {
                setUsers(Array.isArray(res.data) ? res.data : []);
            }).catch(console.error).finally(() => setLoading(false));
        } else if (activeTab === 'health') {
            api.get('/admin/system/health').then(res => {
                setHealth(res.data);
            }).catch(console.error).finally(() => setLoading(false));
        }
    }, [activeTab]);

    const addKeyword = async () => {
        if (!newKeyword.trim()) return;
        try {
            await api.post('/admin/keywords', {
                word: newKeyword.trim(),
                category: newCategory,
                language: /[\u0B80-\u0BFF]/.test(newKeyword) ? 'ta' : 'en'
            });
            // Refresh keywords
            const res = await api.get('/admin/keywords');
            setKeywordsGrouped(res.data?.keywords || {});
            setKeywordsTotal(res.data?.total || 0);
            setNewKeyword('');
        } catch (err) { console.error(err); }
    };

    const deleteKeyword = async (id) => {
        try {
            await api.delete(`/admin/keywords/${id}`);
            // Refresh keywords
            const res = await api.get('/admin/keywords');
            setKeywordsGrouped(res.data?.keywords || {});
            setKeywordsTotal(res.data?.total || 0);
        } catch (err) { console.error(err); }
    };

    const createUser = async () => {
        try {
            await api.post('/admin/users', newUser);
            const res = await api.get('/admin/users');
            setUsers(Array.isArray(res.data) ? res.data : []);
            setShowUserModal(false);
            setNewUser({ username: '', email: '', password: '', full_name: '', role: 'analyst' });
        } catch (err) { console.error(err); }
    };

    const TABS = [
        { id: 'keywords', label: 'Keywords', icon: <Key size={16} /> },
        { id: 'users', label: 'Users', icon: <Users size={16} /> },
        { id: 'health', label: 'System Health', icon: <Activity size={16} /> },
    ];

    const metrics = health?.metrics || {};

    return (
        <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10 }}>
                <Settings size={24} /> Admin Panel
            </h2>

            <div className="admin-tabs">
                {TABS.map(tab => (
                    <button key={tab.id}
                        className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}>
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            {/* Keywords Tab */}
            {activeTab === 'keywords' && (
                <div>
                    <div style={{ display: 'flex', gap: 10, marginBottom: 24, alignItems: 'center' }}>
                        <select className="filter-select" value={newCategory}
                            onChange={(e) => setNewCategory(e.target.value)}>
                            <option value="political_parties">Political Parties</option>
                            <option value="politicians">Politicians</option>
                            <option value="issues">Issues</option>
                            <option value="locations">Locations</option>
                            <option value="threats">Threats</option>
                        </select>
                        <input type="text" className="filter-input" placeholder="Enter new keyword..."
                            value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addKeyword()} />
                        <button className="btn btn-primary" onClick={addKeyword}>
                            <Plus size={16} /> Add
                        </button>
                    </div>

                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                        Total keywords: {keywordsTotal}
                    </div>

                    {loading ? <div className="loading"><div className="spinner" /></div> : (
                        <div className="keywords-grid">
                            {Object.entries(keywordsGrouped).map(([category, kws]) => (
                                <div key={category} className="keyword-group">
                                    <div className="keyword-group-title">
                                        <Key size={14} /> {category.replace(/_/g, ' ')}
                                        <span className="keyword-group-count">({kws.length})</span>
                                    </div>
                                    <div className="keyword-tags">
                                        {kws.map(kw => (
                                            <span key={kw.id} className={`keyword-tag ${kw.is_active ? '' : 'inactive'}`}>
                                                {kw.word}
                                                {kw.language === 'ta' && (
                                                    <span style={{ fontSize: 10, opacity: 0.5, marginLeft: 2 }}>தமிழ்</span>
                                                )}
                                                <button className="remove-btn" onClick={() => deleteKeyword(kw.id)}>
                                                    <X size={12} />
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                        <button className="btn btn-primary" onClick={() => setShowUserModal(true)}>
                            <Plus size={16} /> Add User
                        </button>
                    </div>

                    {loading ? <div className="loading"><div className="spinner" /></div> : (
                        <div className="card">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Username</th>
                                        <th>Email</th>
                                        <th>Role</th>
                                        <th>Status</th>
                                        <th>Last Login</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map(u => (
                                        <tr key={u.id}>
                                            <td style={{ fontWeight: 500 }}>{u.full_name}</td>
                                            <td style={{ color: 'var(--ec-gold)' }}>@{u.username}</td>
                                            <td style={{ color: 'var(--text-muted)' }}>{u.email}</td>
                                            <td>
                                                <span className={`alert-severity ${u.role === 'admin' ? 'CRITICAL' :
                                                        u.role === 'senior_official' ? 'HIGH' :
                                                            u.role === 'duty_officer' ? 'MEDIUM' : 'LOW'
                                                    }`} style={{ fontSize: 11 }}>
                                                    {u.role?.replace(/_/g, ' ')}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`status-dot ${u.is_active ? 'connected' : 'disconnected'}`} />
                                                {u.is_active ? 'Active' : 'Inactive'}
                                            </td>
                                            <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                                {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Add User Modal */}
                    {showUserModal && (
                        <div className="modal-overlay" onClick={() => setShowUserModal(false)}>
                            <div className="modal" onClick={e => e.stopPropagation()}>
                                <h2><Users size={18} style={{ marginRight: 8 }} /> Add New User</h2>
                                <div className="form-group">
                                    <label className="form-label">Full Name</label>
                                    <input type="text" className="form-input" value={newUser.full_name}
                                        onChange={e => setNewUser(prev => ({ ...prev, full_name: e.target.value }))} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Username</label>
                                    <input type="text" className="form-input" value={newUser.username}
                                        onChange={e => setNewUser(prev => ({ ...prev, username: e.target.value }))} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Email</label>
                                    <input type="email" className="form-input" value={newUser.email}
                                        onChange={e => setNewUser(prev => ({ ...prev, email: e.target.value }))} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Password</label>
                                    <input type="password" className="form-input" value={newUser.password}
                                        onChange={e => setNewUser(prev => ({ ...prev, password: e.target.value }))} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Role</label>
                                    <select className="form-select" value={newUser.role}
                                        onChange={e => setNewUser(prev => ({ ...prev, role: e.target.value }))}>
                                        <option value="duty_officer">Duty Officer</option>
                                        <option value="analyst">Analyst</option>
                                        <option value="senior_official">Senior Official</option>
                                        <option value="admin">Admin</option>
                                        <option value="auditor">Auditor</option>
                                    </select>
                                </div>
                                <div className="modal-actions">
                                    <button className="btn btn-outline" onClick={() => setShowUserModal(false)}>Cancel</button>
                                    <button className="btn btn-primary" onClick={createUser}>Create User</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* System Health Tab */}
            {activeTab === 'health' && (
                <div>
                    {loading ? <div className="loading"><div className="spinner" /></div> : health ? (
                        <>
                            <div className="stats-grid" style={{ marginBottom: 24 }}>
                                <div className="stat-card">
                                    <div className="stat-icon low"><Server size={24} /></div>
                                    <div className="stat-info">
                                        <div className="stat-value" style={{ color: health.status === 'healthy' ? 'var(--low)' : 'var(--critical)' }}>
                                            {health.status?.toUpperCase()}
                                        </div>
                                        <div className="stat-label">System Status</div>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon blue"><Database size={24} /></div>
                                    <div className="stat-info">
                                        <div className="stat-value">{metrics.total_posts?.toLocaleString()}</div>
                                        <div className="stat-label">Total Posts</div>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon gold"><Shield size={24} /></div>
                                    <div className="stat-info">
                                        <div className="stat-value">{metrics.total_alerts?.toLocaleString()}</div>
                                        <div className="stat-label">Total Alerts</div>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon critical"><Cpu size={24} /></div>
                                    <div className="stat-info">
                                        <div className="stat-value">{metrics.processing_queue}</div>
                                        <div className="stat-label">Processing Queue</div>
                                    </div>
                                </div>
                            </div>

                            <div className="card" style={{ marginBottom: 16 }}>
                                <div className="card-header">
                                    <div className="card-title">System Metrics</div>
                                </div>
                                <div className="health-grid">
                                    <div className="health-item">
                                        <div className="health-label">Active Users</div>
                                        <div className="health-value">{metrics.active_users}</div>
                                    </div>
                                    <div className="health-item">
                                        <div className="health-label">Active Keywords</div>
                                        <div className="health-value">{metrics.active_keywords}</div>
                                    </div>
                                    <div className="health-item">
                                        <div className="health-label">Posts Analyzed</div>
                                        <div className="health-value">{metrics.total_analyzed?.toLocaleString()}</div>
                                    </div>
                                    <div className="health-item">
                                        <div className="health-label">CPU Usage</div>
                                        <div className="health-value" style={{ color: metrics.cpu_usage > 80 ? 'var(--critical)' : 'var(--low)' }}>
                                            {metrics.cpu_usage}%
                                        </div>
                                    </div>
                                    <div className="health-item">
                                        <div className="health-label">Memory Usage</div>
                                        <div className="health-value" style={{ color: metrics.memory_usage > 80 ? 'var(--critical)' : 'var(--low)' }}>
                                            {metrics.memory_usage}%
                                        </div>
                                    </div>
                                    <div className="health-item">
                                        <div className="health-label">DB Size</div>
                                        <div className="health-value">{metrics.database_size_mb} MB</div>
                                    </div>
                                </div>
                            </div>

                            {/* Platform Status */}
                            {metrics.api_status && (
                                <div className="card">
                                    <div className="card-header">
                                        <div className="card-title">Platform Monitoring Status</div>
                                    </div>
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Platform</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(metrics.api_status).map(([platform, status]) => (
                                                <tr key={platform}>
                                                    <td style={{ fontWeight: 500, textTransform: 'capitalize' }}>
                                                        {platform.replace(/_/g, ' ')}
                                                    </td>
                                                    <td>
                                                        <span className={`status-dot ${status === 'connected' ? 'connected' : 'disconnected'}`} />
                                                        <span style={{ color: status === 'connected' ? 'var(--low)' : 'var(--critical)', textTransform: 'capitalize' }}>
                                                            {status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            <div style={{ marginTop: 16, fontSize: 13, color: 'var(--text-muted)' }}>
                                Last collection: {health.last_collection ? new Date(health.last_collection).toLocaleString() : 'N/A'} •{' '}
                                Version: {health.version} •{' '}
                                Uptime: {health.uptime}
                            </div>
                        </>
                    ) : (
                        <div className="empty-state">Failed to load system health</div>
                    )}
                </div>
            )}
        </div>
    );
}
