import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { Shield, BarChart3, FileText, Settings, Bell, LogOut } from 'lucide-react';

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const initials = user?.full_name?.split(' ').map(n => n[0]).join('') || 'U';

    return (
        <div className="app-layout">
            <nav className="navbar">
                <div className="navbar-brand">
                    <div className="navbar-logo">TN</div>
                    <div>
                        <div className="navbar-title">TN Politics Monitor</div>
                        <div className="navbar-subtitle">Election Commission</div>
                    </div>
                </div>

                <div className="navbar-links">
                    <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                        <Shield size={16} /> Alerts
                    </NavLink>
                    <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                        <BarChart3 size={16} /> Analytics
                    </NavLink>
                    <NavLink to="/reports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                        <FileText size={16} /> Reports
                    </NavLink>
                    {(user?.role === 'admin' || user?.role === 'senior_official') && (
                        <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                            <Settings size={16} /> Admin
                        </NavLink>
                    )}
                </div>

                <div className="navbar-right">
                    <button className="notification-bell" title="Notifications">
                        <Bell size={20} />
                        <span className="notification-badge">3</span>
                    </button>
                    <div className="user-menu" onClick={handleLogout} title="Click to logout">
                        <div className="user-avatar">{initials}</div>
                        <div className="user-info">
                            <div className="user-name">{user?.full_name}</div>
                            <div className="user-role">{user?.role?.replace('_', ' ')}</div>
                        </div>
                        <LogOut size={14} style={{ color: 'var(--text-muted)', marginLeft: 4 }} />
                    </div>
                </div>
            </nav>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
