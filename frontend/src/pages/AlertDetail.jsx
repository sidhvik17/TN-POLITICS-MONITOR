import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../lib/auth';
import {
    ArrowLeft, ExternalLink, MapPin, Clock, User as UserIcon,
    MessageSquare, Heart, Share2, Hash, Brain, Shield, Flag
} from 'lucide-react';

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

const STATUS_OPTIONS = ['NEW', 'IN_REVIEW', 'ACTIONABLE', 'FALSE_POSITIVE', 'RESOLVED', 'ESCALATED'];

export default function AlertDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [alert, setAlert] = useState(null);
    const [loading, setLoading] = useState(true);
    const [note, setNote] = useState('');
    const [updating, setUpdating] = useState(false);

    useEffect(() => {
        api.get(`/alerts/${id}`).then(res => { setAlert(res.data); setLoading(false); })
            .catch(() => { setLoading(false); navigate('/'); });
    }, [id]);

    const updateStatus = async (newStatus) => {
        setUpdating(true);
        try {
            const res = await api.patch(`/alerts/${id}/status`, {
                status: newStatus, notes: note || undefined
            });
            setAlert(res.data);
            setNote('');
        } catch (err) {
            console.error('Failed to update status:', err);
        } finally { setUpdating(false); }
    };

    if (loading) return <div className="loading"><div className="spinner" /><span>Loading alert...</span></div>;
    if (!alert) return <div className="empty-state">Alert not found</div>;

    const post = alert.post || {};
    const analysis = alert.analysis || {};
    const confidencePct = Math.round((analysis.confidence_score || 0) * 100);
    const severityPct = Math.round((analysis.severity_score || 0) * 100);

    const confidenceColor = confidencePct >= 90 ? 'var(--low)' :
        confidencePct >= 70 ? 'var(--medium)' : 'var(--critical)';

    return (
        <div>
            <div className="detail-header">
                <button className="back-btn" onClick={() => navigate(-1)}>
                    <ArrowLeft size={18} /> Back to Alerts
                </button>
                <span className={`alert-severity ${alert.severity}`} style={{ fontSize: 13 }}>
                    {alert.severity}
                </span>
                <span className={`alert-status ${alert.status}`} style={{ fontSize: 12 }}>
                    {alert.status?.replace('_', ' ')}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                    Alert #{alert.id} • {timeAgo(alert.created_at)}
                </span>
            </div>

            <div className="detail-grid">
                {/* Left Column */}
                <div>
                    {/* Original Post */}
                    <div className="detail-section">
                        <h3><MessageSquare size={14} style={{ marginRight: 6 }} /> Original Post</h3>
                        <div className="detail-content tamil" style={{ marginBottom: 12 }}>
                            {post.content}
                        </div>
                        {post.translated_content && (
                            <>
                                <h3 style={{ marginTop: 16 }}>English Translation</h3>
                                <div className="detail-content">
                                    {post.translated_content}
                                </div>
                            </>
                        )}
                        <div style={{ display: 'flex', gap: 16, marginTop: 16, flexWrap: 'wrap' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <UserIcon size={14} /> @{post.author_name}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <Hash size={14} /> {post.platform}
                            </span>
                            {post.district && (
                                <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                    <MapPin size={14} /> {post.district}
                                </span>
                            )}
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <Clock size={14} /> {new Date(post.timestamp).toLocaleString()}
                            </span>
                        </div>
                        {/* Engagement */}
                        <div style={{ display: 'flex', gap: 20, marginTop: 12 }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <Heart size={14} /> {post.likes?.toLocaleString() || 0}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <Share2 size={14} /> {post.shares?.toLocaleString() || 0}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 13 }}>
                                <MessageSquare size={14} /> {post.comments_count?.toLocaleString() || 0}
                            </span>
                        </div>

                        {post.url && (
                            <a href={post.url} target="_blank" rel="noopener noreferrer"
                                className="btn btn-outline btn-sm" style={{ marginTop: 12 }}>
                                <ExternalLink size={14} /> View Original Post
                            </a>
                        )}
                    </div>

                    {/* AI Analysis */}
                    <div className="detail-section">
                        <h3><Brain size={14} style={{ marginRight: 6 }} /> AI Analysis</h3>

                        <div style={{ marginBottom: 16 }}>
                            <div className="detail-label">Severity Explanation</div>
                            <div className="detail-content" style={{ fontSize: 14 }}>
                                {analysis.explanation || alert.description}
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                            <div>
                                <div className="detail-label">Sentiment</div>
                                <div className="detail-value" style={{
                                    color: analysis.sentiment === 'negative' ? 'var(--critical)' :
                                        analysis.sentiment === 'positive' ? 'var(--low)' : 'var(--medium)',
                                    textTransform: 'capitalize'
                                }}>
                                    {analysis.sentiment || 'N/A'} ({Math.round((analysis.sentiment_score || 0) * 100)}%)
                                </div>
                            </div>
                            <div>
                                <div className="detail-label">Language</div>
                                <div className="detail-value">
                                    {post.language === 'ta' ? 'Tamil (தமிழ்)' : post.language === 'en' ? 'English' : post.language || 'N/A'}
                                </div>
                            </div>
                        </div>

                        {/* Confidence Bar */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                            <div>
                                <div className="detail-label">Confidence Score</div>
                                <div className="confidence-bar" style={{ width: '100%', marginTop: 6 }}>
                                    <div className="confidence-fill" style={{
                                        width: `${confidencePct}%`, background: confidenceColor
                                    }} />
                                </div>
                                <div style={{ fontSize: 12, color: confidenceColor, marginTop: 4 }}>{confidencePct}%</div>
                            </div>
                            <div>
                                <div className="detail-label">Severity Score</div>
                                <div className="confidence-bar" style={{ width: '100%', marginTop: 6 }}>
                                    <div className="confidence-fill" style={{
                                        width: `${severityPct}%`,
                                        background: alert.severity === 'CRITICAL' ? 'var(--critical)' :
                                            alert.severity === 'HIGH' ? 'var(--high)' : 'var(--medium)'
                                    }} />
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{severityPct}%</div>
                            </div>
                        </div>

                        {/* Detected Issues */}
                        {analysis.detected_issues?.length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                                <div className="detail-label">Detected Issues</div>
                                <div style={{ marginTop: 6 }}>
                                    {analysis.detected_issues.map((issue, i) => (
                                        <span key={i} className="issue-tag">
                                            <Flag size={10} /> {issue.replace(/_/g, ' ')}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Topics */}
                        {analysis.topics?.length > 0 && (
                            <div>
                                <div className="detail-label">Topics</div>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                                    {analysis.topics.map((topic, i) => (
                                        <span key={i} style={{
                                            padding: '4px 10px', borderRadius: 6, fontSize: 12,
                                            background: 'rgba(31,71,136,0.15)', color: 'var(--ec-blue-light)'
                                        }}>
                                            {topic}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column */}
                <div>
                    {/* Update Status */}
                    <div className="detail-section">
                        <h3><Shield size={14} style={{ marginRight: 6 }} /> Update Status</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {STATUS_OPTIONS.map(s => (
                                <button
                                    key={s}
                                    className={`btn btn-sm ${alert.status === s ? 'btn-primary' : 'btn-outline'}`}
                                    onClick={() => updateStatus(s)}
                                    disabled={updating || alert.status === s}
                                    style={{ justifyContent: 'flex-start' }}
                                >
                                    <span className={`alert-status ${s}`} style={{ marginRight: 6 }}>
                                        {s.replace('_', ' ')}
                                    </span>
                                </button>
                            ))}
                        </div>

                        <div style={{ marginTop: 16 }}>
                            <textarea
                                className="form-textarea"
                                placeholder="Add note (required for Actionable/False Positive)..."
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                                rows={3}
                            />
                        </div>
                    </div>

                    {/* Entities */}
                    {analysis.entities && Object.keys(analysis.entities).length > 0 && (
                        <div className="detail-section">
                            <h3>Entities Detected</h3>
                            {Object.entries(analysis.entities).map(([type, items]) => (
                                <div key={type} style={{ marginBottom: 10 }}>
                                    <div className="detail-label" style={{ textTransform: 'capitalize' }}>{type}</div>
                                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                                        {(Array.isArray(items) ? items : [items]).map((item, i) => (
                                            <span key={i} style={{
                                                padding: '3px 8px', borderRadius: 4, fontSize: 12,
                                                background: 'rgba(212,175,55,0.15)', color: 'var(--ec-gold)'
                                            }}>
                                                {item}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Alert Info */}
                    <div className="detail-section">
                        <h3>Alert Details</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <div>
                                <div className="detail-label">Alert Type</div>
                                <div className="detail-value">{alert.alert_type?.replace(/_/g, ' ')}</div>
                            </div>
                            <div>
                                <div className="detail-label">Assigned To</div>
                                <div className="detail-value">
                                    {alert.assigned_to ? `User #${alert.assigned_to}` : 'Unassigned'}
                                </div>
                            </div>
                            <div>
                                <div className="detail-label">Created</div>
                                <div className="detail-value">{new Date(alert.created_at).toLocaleString()}</div>
                            </div>
                            {alert.resolved_at && (
                                <div>
                                    <div className="detail-label">Resolved</div>
                                    <div className="detail-value">{new Date(alert.resolved_at).toLocaleString()}</div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
