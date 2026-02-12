import React, { useState, useEffect } from 'react';
import './DndTest.css';

const DndTest = () => {
    const [config, setConfig] = useState(null);
    const [isRunning, setIsRunning] = useState(false);
    const [progress, setProgress] = useState([]);
    const [results, setResults] = useState(null);
    const [url, setUrl] = useState('http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank');
    const [useExistingBrowser, setUseExistingBrowser] = useState(true);

    // Load config on mount
    useEffect(() => {
        loadConfig();
    }, []);

    // Poll for progress updates when test is running
    useEffect(() => {
        if (!isRunning) return;

        const interval = setInterval(async () => {
            try {
                const response = await fetch('http://localhost:3001/api/dnd-test/progress');
                const data = await response.json();

                if (data.updates && data.updates.length > 0) {
                    data.updates.forEach(update => {
                        if (update.type === 'complete') {
                            setResults(update.result);
                            setIsRunning(false);
                        } else {
                            setProgress(prev => [...prev, update]);
                        }
                    });
                }
            } catch (error) {
                console.error('Error fetching progress:', error);
            }
        }, 500); // Poll every 500ms

        return () => clearInterval(interval);
    }, [isRunning]);

    const loadConfig = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/dnd-test/config');
            const data = await response.json();
            if (data.status === 'success') {
                setConfig(data.config);
            }
        } catch (error) {
            console.error('Error loading config:', error);
        }
    };

    const startTest = async () => {
        try {
            setProgress([]);
            setResults(null);
            setIsRunning(true);

            const response = await fetch('http://localhost:3001/api/dnd-test/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url,
                    use_existing_browser: useExistingBrowser,
                    cdp_url: 'http://localhost:9222'
                }),
            });

            const data = await response.json();
            if (data.status === 'started') {
                setProgress([{ message: 'Test started...', status: 'info' }]);
            }
        } catch (error) {
            console.error('Error starting test:', error);
            setIsRunning(false);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'success':
                return '✓';
            case 'error':
                return '✗';
            case 'warning':
                return '⚠';
            default:
                return '→';
        }
    };

    const getStatusClass = (status) => {
        return `progress-item ${status}`;
    };

    return (
        <div className="dnd-test-container">
            <div className="dnd-test-card">
                <h1>🎯 Drag & Drop Test Automation</h1>
                <p className="subtitle">Automated browser testing for config-driven drag-and-drop features</p>

                {/* Config Status */}
                <div className="config-status">
                    <h3>Configuration</h3>
                    {config ? (
                        <div className="config-info">
                            <span className="status-badge success">✓ Config Loaded</span>
                            <div className="config-details">
                                <span>{config.draggableItems?.items?.length || 0} draggable items</span>
                                <span>{config.dropzones?.zones?.length || 0} drop zones</span>
                            </div>
                        </div>
                    ) : (
                        <span className="status-badge error">✗ Config not loaded</span>
                    )}
                </div>

                {/* URL Input */}
                <div className="url-section">
                    <h3>Target URL</h3>
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Enter URL to test"
                        className="url-input"
                        disabled={isRunning}
                    />
                </div>

                {/* Browser Mode Selection */}
                <div className="browser-mode-section">
                    <h3>Browser Mode</h3>
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={useExistingBrowser}
                            onChange={(e) => setUseExistingBrowser(e.target.checked)}
                            disabled={isRunning}
                        />
                        <span>Use existing Chrome (keeps your authentication)</span>
                    </label>

                    {useExistingBrowser && (
                        <div className="browser-instructions">
                            <p><strong>📋 Setup Instructions:</strong></p>
                            <ol>
                                <li>Close all Chrome windows</li>
                                <li>Open terminal and run:</li>
                            </ol>
                            <code className="command-box">
                                google-chrome --remote-debugging-port=9222
                            </code>
                            <p className="note">
                                ✓ This will open Chrome with remote debugging enabled<br />
                                ✓ Login to your application in this Chrome window<br />
                                ✓ Then click "Start Test" below - it will use this Chrome instance
                            </p>
                        </div>
                    )}

                    {!useExistingBrowser && (
                        <div className="browser-instructions warning">
                            <p>⚠️ <strong>New browser mode:</strong></p>
                            <p>A fresh Chrome window will open without your authentication. You'll need to login manually or the test may fail.</p>
                        </div>
                    )}
                </div>

                {/* Control Buttons */}
                <div className="control-buttons">
                    <button
                        onClick={startTest}
                        disabled={isRunning || !config}
                        className="btn btn-primary"
                    >
                        {isRunning ? '🔄 Running...' : '▶ Start Test'}
                    </button>
                </div>

                {/* Progress Display */}
                {progress.length > 0 && (
                    <div className="progress-section">
                        <h3>Progress</h3>
                        <div className="progress-list">
                            {progress.map((item, index) => (
                                <div key={index} className={getStatusClass(item.status)}>
                                    <span className="status-icon">{getStatusIcon(item.status)}</span>
                                    <span className="progress-message">{item.message}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Results Display */}
                {results && (
                    <div className="results-section">
                        <h3>Results</h3>
                        <div className={`results-card ${results.success ? 'success' : 'error'}`}>
                            <div className="result-header">
                                <span className="result-icon">
                                    {results.success ? '✓' : '✗'}
                                </span>
                                <span className="result-title">
                                    {results.success ? 'Test Passed!' : 'Test Failed'}
                                </span>
                            </div>
                            <div className="result-details">
                                <div className="result-stat">
                                    <span className="stat-label">Completed:</span>
                                    <span className="stat-value">
                                        {results.completed_operations}/{results.total_operations}
                                    </span>
                                </div>
                                {results.errors && results.errors.length > 0 && (
                                    <div className="errors-list">
                                        <h4>Errors:</h4>
                                        {results.errors.map((error, index) => (
                                            <div key={index} className="error-item">{error}</div>
                                        ))}
                                    </div>
                                )}
                                {results.screenshot && (
                                    <div className="screenshot-info">
                                        <span>Screenshot saved: {results.screenshot}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Info Box */}
                <div className="info-box">
                    <h4>ℹ️ How it works</h4>
                    <ul>
                        <li>Browser will open <strong>visibly</strong> on your screen</li>
                        <li>You'll see the automation happening in real-time</li>
                        <li>The test reads config.json and performs drag-and-drop operations</li>
                        <li>Make sure the target URL is accessible and you're authenticated</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default DndTest;
