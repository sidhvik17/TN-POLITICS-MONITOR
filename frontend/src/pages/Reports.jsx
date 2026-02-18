import { useState, useEffect } from 'react';
import api from '../lib/api';
import { FileText, Download, Calendar, RefreshCw } from 'lucide-react';

export default function Reports() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [reportType, setReportType] = useState('executive_summary');
    const [dateRange, setDateRange] = useState({
        start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
    });

    useEffect(() => {
        api.get('/reports').then(res => {
            const data = res.data?.data || res.data || [];
            setReports(Array.isArray(data) ? data : []);
        }).catch(console.error).finally(() => setLoading(false));
    }, []);

    const generateReport = async () => {
        setGenerating(true);
        try {
            const res = await api.post('/reports/generate', {
                type: reportType,
                date_from: dateRange.start,
                date_to: dateRange.end,
                format: 'pdf'
            });
            setReports(prev => [res.data, ...prev]);
        } catch (err) {
            console.error('Failed to generate report:', err);
        } finally { setGenerating(false); }
    };

    const REPORT_TYPES = [
        { value: 'executive_summary', label: 'Executive Summary', desc: 'High-level overview for EC leadership' },
        { value: 'district_analysis', label: 'District Analysis', desc: 'District-wise alert distribution and hotspots' },
        { value: 'topic_deep_dive', label: 'Topic Deep Dive', desc: 'In-depth analysis of specific trending topics' },
        { value: 'alert_audit', label: 'Alert Response Audit', desc: 'Review of alert handling and response times' },
        { value: 'party_comparison', label: 'Party Comparison', desc: 'Social media platform comparison and metrics' },
        { value: 'evidence_package', label: 'Evidence Package', desc: 'Court-ready evidence compilation for selected alerts' },
    ];

    return (
        <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10 }}>
                <FileText size={24} /> Report Generator
            </h2>

            {/* Report Generator Form */}
            <div className="report-form">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                    <div>
                        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Report Type</h3>
                        <div className="radio-group">
                            {REPORT_TYPES.map(rt => (
                                <div key={rt.value} className="radio-item"
                                    onClick={() => setReportType(rt.value)}
                                    style={{
                                        background: reportType === rt.value ? 'rgba(212,175,55,0.08)' : 'transparent',
                                        border: `1px solid ${reportType === rt.value ? 'var(--ec-gold)' : 'transparent'}`,
                                        borderRadius: 8, padding: '10px 12px', cursor: 'pointer'
                                    }}>
                                    <input type="radio" name="reportType" value={rt.value}
                                        checked={reportType === rt.value} readOnly />
                                    <div>
                                        <label style={{ fontWeight: 500, cursor: 'pointer' }}>{rt.label}</label>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{rt.desc}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div>
                        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>
                            <Calendar size={14} style={{ marginRight: 6 }} /> Date Range
                        </h3>
                        <div className="form-group">
                            <label className="form-label">Start Date</label>
                            <input type="date" className="form-input" value={dateRange.start}
                                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">End Date</label>
                            <input type="date" className="form-input" value={dateRange.end}
                                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))} />
                        </div>

                        <button className="btn btn-gold" onClick={generateReport} disabled={generating}
                            style={{ width: '100%', marginTop: 16, justifyContent: 'center' }}>
                            {generating ? (
                                <><RefreshCw size={16} /> Generating...</>
                            ) : (
                                <><FileText size={16} /> Generate Report</>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Recent Reports */}
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recent Reports</h3>
            {loading ? (
                <div className="loading"><div className="spinner" /></div>
            ) : reports.length === 0 ? (
                <div className="empty-state">
                    <p>No reports generated yet.</p>
                </div>
            ) : (
                <div className="reports-list">
                    {reports.map((report, i) => (
                        <div key={report.id || i} className="report-item">
                            <div className={`report-icon ${report.format || 'pdf'}`}>
                                <FileText size={20} />
                            </div>
                            <div className="report-info">
                                <div className="report-title">{report.title || report.type?.replace(/_/g, ' ')}</div>
                                <div className="report-meta">
                                    {report.type?.replace(/_/g, ' ')} •{' '}
                                    {new Date(report.generated_at).toLocaleDateString()} •{' '}
                                    {report.format?.toUpperCase()} •{' '}
                                    {report.size_kb ? `${report.size_kb}KB` : ''} •{' '}
                                    {report.status || 'completed'}
                                </div>
                            </div>
                            <button className="btn btn-outline btn-sm" onClick={() => window.open(report.download_url || '#', '_blank')}>
                                <Download size={14} /> Download
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
