import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useNavigate, Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, LineChart, Line, ZAxis
} from 'recharts';
import './App.css';

function Dashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login');
    }
  }, [navigate]);

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [apiKey, setApiKey] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setChartData(null);
    setInsights(null);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setData(response.data);

      // Fetch chart data immediately after upload
      try {
        const chartRes = await axios.get('http://localhost:5000/dashboard_data', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        setChartData(chartRes.data);
      } catch (err) {
        console.warn("Could not load charts", err);
      }

      // Auto-generate insights if API key exists
      if (apiKey) {
        setLoadingInsights(true);
        try {
          const insightsRes = await axios.post('http://localhost:5000/generate_insights', { apiKey }, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          });
          setInsights(insightsRes.data.insights);
        } catch (err) {
          console.error("Auto insight generation failed:", err);
        }
        setLoadingInsights(false);
      }

      setLoading(false);
    } catch (err) {
      console.error(err);
      setError("Upload failed. Please ensure the backend is running.");
      setLoading(false);
    }
  };

  const [insights, setInsights] = useState(null);
  const [loadingInsights, setLoadingInsights] = useState(false);

  const handleGenerateInsights = async () => {
    setLoadingInsights(true);
    try {
      const response = await axios.post('http://localhost:5000/generate_insights', { apiKey }, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setInsights(response.data.insights);
    } catch (err) {
      console.error(err);
      alert("Failed to generate insights. Ensure the backend is running and you have entered a valid Google API Key.");
    }
    setLoadingInsights(false);
  };

  // Helper to render correlation heatmap
  const renderHeatmap = () => {
    if (!chartData || !chartData.correlation_heatmap || chartData.correlation_heatmap.length === 0) return null;

    // Get unique keys
    const xLabels = [...new Set(chartData.correlation_heatmap.map(d => d.x))];
    const yLabels = [...new Set(chartData.correlation_heatmap.map(d => d.y))];

    return (
      <div className="heatmap-container" style={{ overflowX: 'auto' }}>
        <table className="heatmap-table">
          <thead>
            <tr>
              <th></th>
              {xLabels.map(x => <th key={x}>{x}</th>)}
            </tr>
          </thead>
          <tbody>
            {yLabels.map(y => (
              <tr key={y}>
                <th>{y}</th>
                {xLabels.map(x => {
                  const cell = chartData.correlation_heatmap.find(d => d.x === x && d.y === y);
                  const val = cell ? cell.value : 0;
                  // Color scale: -1 (Red) to 0 (White) to 1 (Blue)
                  const alpha = Math.abs(val);
                  const color = val > 0 ? `rgba(0, 123, 255, ${alpha})` : `rgba(255, 99, 71, ${alpha})`;
                  return (
                    <td key={x} style={{ backgroundColor: color, color: alpha > 0.5 ? '#fff' : '#000' }}>
                      {val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ textAlign: 'left' }}>
          <h1>Automated Data Analytics Web Application</h1>
          <p>End-to-end Machine Learning powered prediction and interactive dashboard system</p>
        </div>
        <div>
          <Link to="/history" className="cta-button" style={{ marginRight: '10px', textDecoration: 'none' }}>Analysis History</Link>
          <button className="cta-button" onClick={() => { localStorage.clear(); navigate('/login'); }}>Logout</button>
        </div>
      </header>

      <div className="api-key-section glass-panel">
        <p>Optional: Enter Google Gemini API Key below for automatic AI Business Insights on your data.</p>
        <div className="api-input">
          <input
            type="password"
            placeholder="Enter Gemini API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>
      </div>

      <div className="upload-section glass-panel">
        <input type="file" accept=".csv" onChange={handleFileChange} className="file-input" />
        <button onClick={handleUpload} disabled={loading} className="cta-button">
          {loading ? 'Analyzing...' : 'Upload & Start Analysis'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {data && (
        <div className="dashboard-grid">

          {/* 1. Dataset Overview */}
          <section className="card overview">
            <h2>Dataset Overview</h2>
            <div className="stats-grid">
              <div className="stat-box">
                <strong>Rows</strong>
                <p>{data.structure.rows}</p>
              </div>
              <div className="stat-box">
                <strong>Columns</strong>
                <p>{data.structure.columns}</p>
              </div>
              <div className="stat-box">
                <strong>Missing Values</strong>
                <p>{Object.values(data.structure.missing_values).reduce((a, b) => a + b, 0)}</p>
              </div>
              <div className="stat-box">
                <strong>Duplicates</strong>
                <p>{data.structure.duplicate_rows}</p>
              </div>
            </div>
          </section>

          {/* 2. Auto-ML Results */}
          <section className="card ml-results">
            <h2>AI Model Analysis</h2>
            {data.ml_results.error ? (
              <div className="error-box">
                <p><strong>⚠️ Intelligence Engine Warning</strong></p>
                <p>{data.ml_results.model_description}</p>
                <p className="small-text">Technical details: {data.ml_results.error}</p>
              </div>
            ) : (
              <div className="ml-details">
                <div className="ml-header">
                  <span className="badge">{data.ml_results.type || "N/A"}</span>
                  <h3>{data.ml_results.model || "Unknown Model"}</h3>
                </div>
                <p className="model-desc">{data.ml_results.model_description}</p>

                <div className="metrics-grid">
                  <div className="metric-box">
                    <span>Target Variable</span>
                    <strong>{data.ml_results.target_column || "Not Detected"}</strong>
                  </div>
                  {data.ml_results.test_score_r2 !== undefined && (
                    <div className="metric-box highlighted">
                      <span>Performance (R² Score)</span>
                      <strong>{(data.ml_results.test_score_r2 * 100).toFixed(1)}%</strong>
                    </div>
                  )}
                  {data.ml_results.rmse !== undefined && (
                    <div className="metric-box">
                      <span>Avg. Prediction Error (RMSE)</span>
                      <strong>{data.ml_results.rmse.toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong>
                    </div>
                  )}
                  {data.ml_results.accuracy !== undefined && (
                    <div className="metric-box highlighted">
                      <span>Prediction Accuracy</span>
                      <strong>{(data.ml_results.accuracy * 100).toFixed(1)}%</strong>
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>

          {/* 3. Visualizations Grid */}
          {chartData && (
            <section className="card charts-section">
              <h2>Visual Insights</h2>
              <div className="charts-grid">

                {/* Target Distribution */}
                {chartData.target_distribution && (
                  <div className="chart-card">
                    <h3>Target Distribution ({data.ml_results.target_column})</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={Object.entries(chartData.target_distribution).map(([k, v]) => ({ name: k, count: v }))}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                        <Bar dataKey="count" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Feature Importance */}
                {data.ml_results.feature_importance && (
                  <div className="chart-card">
                    <h3>Key Drivers (Feature Importance)</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        layout="vertical"
                        data={data.ml_results.feature_importance}
                        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" />
                        <YAxis dataKey="feature" type="category" width={80} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="importance" fill="#10B981" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Scatter Plot */}
                {chartData.scatter_plot && (
                  <div className="chart-card">
                    <h3>Correlation Analysis: {chartData.scatter_plot.feature} vs {chartData.scatter_plot.target}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid />
                        <XAxis type="number" dataKey="x" name={chartData.scatter_plot.feature} />
                        <YAxis type="number" dataKey="y" name={chartData.scatter_plot.target} />
                        <ZAxis type="number" range={[50, 50]} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter name="Data Points" data={chartData.scatter_plot.data} fill="#EC4899" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Line Chart */}
                {chartData.line_chart && (
                  <div className="chart-card">
                    <h3>Trend Over Time ({chartData.line_chart.y_label})</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={chartData.line_chart.data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="x" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="y" stroke="#8884d8" activeDot={{ r: 8 }} strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

              </div>

              {/* Heatmap Section */}
              {chartData.correlation_heatmap && chartData.correlation_heatmap.length > 0 && (
                <div className="chart-card full-width">
                  <h3>Correlation Heatmap</h3>
                  {renderHeatmap()}
                </div>
              )}
            </section>
          )}

          {/* 4. AI Insights */}
          <section className="card insights-section">
            <div className="insights-header">
              <h2>AI Business Insights</h2>
              <div className="api-input">
                <button onClick={handleGenerateInsights} disabled={loadingInsights}>
                  {loadingInsights ? "Generating..." : "Generate Insights"}
                </button>
              </div>
            </div>

            {insights && (
              <div className="insights-content markdown-body">
                <ReactMarkdown>{insights}</ReactMarkdown>
              </div>
            )}
          </section>

          {/* 5. Data Preview */}
          <section className="card preview">
            <div className="section-header">
              <h2>Data Preview</h2>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    {data.structure.column_names.map(col => <th key={col}>{col}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {data.preview.map((row, i) => (
                    <tr key={i}>
                      {data.structure.column_names.map(col => <td key={col}>{row[col]}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

        </div>
      )}
    </div>
  );
}

export default Dashboard;