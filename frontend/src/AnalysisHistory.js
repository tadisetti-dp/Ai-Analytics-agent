import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

function AnalysisHistory() {
    const [history, setHistory] = useState([]);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('token');
        const userId = localStorage.getItem('user_id');

        if (!token || !userId) {
            navigate('/login');
            return;
        }

        const fetchHistory = async () => {
            try {
                const response = await axios.get(`http://localhost:5000/analysis-history/${userId}`, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
                setHistory(response.data.history);
            } catch (err) {
                if (err.response?.status === 401 || err.response?.status === 403) {
                    localStorage.removeItem('token');
                    navigate('/login');
                } else {
                    setError('Failed to fetch analysis history.');
                }
            }
        };

        fetchHistory();
    }, [navigate]);

    return (
        <div className="history-container" style={{ padding: '20px', maxWidth: '1400px', margin: '40px auto' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <h2 className="history-title">Analysis History</h2>
                <Link to="/dashboard" className="cta-button" style={{ textDecoration: 'none' }}>Back to Dashboard</Link>
            </header>

            {error ? (
                <p className="error">{error}</p>
            ) : (
                <div className="table-container glass-panel" style={{ padding: '0', overflowX: 'auto', background: 'rgba(30, 41, 59, 0.7)', backdropFilter: 'blur(16px)', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)', width: '100%' }}>
                    <table className="history-table">
                        <thead>
                            <tr style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
                                <th style={{ whiteSpace: 'nowrap' }}>Dataset</th>
                                <th style={{ whiteSpace: 'nowrap' }}>Target</th>
                                <th style={{ whiteSpace: 'nowrap' }}>Model</th>
                                <th style={{ whiteSpace: 'nowrap' }}>Problem Type</th>
                                <th style={{ whiteSpace: 'nowrap' }}>Performance Metrics</th>
                                <th style={{ whiteSpace: 'nowrap' }}>Date & Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.length > 0 ? (
                                history.map((log, index) => (
                                    <tr key={index} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', transition: 'background 0.3s' }}>
                                        <td style={{ fontWeight: 600, color: '#F8FAFC', whiteSpace: 'nowrap' }}>{log.dataset}</td>
                                        <td style={{ color: '#94A3B8', whiteSpace: 'nowrap' }}>{log.target || 'N/A'}</td>
                                        <td style={{ whiteSpace: 'nowrap' }}>
                                            <span style={{ background: 'rgba(79, 70, 229, 0.2)', color: '#818CF8', padding: '4px 8px', borderRadius: '4px', fontSize: '0.9rem', display: 'inline-block' }}>
                                                {log.model || 'N/A'}
                                            </span>
                                        </td>
                                        <td style={{ whiteSpace: 'nowrap' }}>
                                            <span style={{ background: log.problem_type === 'Classification' ? 'rgba(236, 72, 153, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: log.problem_type === 'Classification' ? '#F472B6' : '#6EE7B7', padding: '4px 8px', borderRadius: '4px', fontSize: '0.9rem', display: 'inline-block' }}>
                                                {log.problem_type || '-'}
                                            </span>
                                        </td>
                                        <td style={{ whiteSpace: 'nowrap', fontWeight: 'bold', color: log.problem_type === 'Classification' ? '#10B981' : log.problem_type === 'Regression' ? '#F59E0B' : '#64748B' }}>
                                            {log.metrics && log.metrics !== '-' ? log.metrics : 'N/A'}
                                        </td>
                                        <td style={{ whiteSpace: 'nowrap', color: '#94A3B8', fontSize: '0.9rem' }}>
                                            {new Date(log.date).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true })}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" style={{ padding: '30px', textAlign: 'center', color: '#94A3B8' }}>No analysis history found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default AnalysisHistory;
