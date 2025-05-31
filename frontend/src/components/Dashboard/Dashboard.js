import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [user, setUser] = useState(null);
    const [analysisHistory, setAnalysisHistory] = useState([]);
    const [error, setError] = useState('');
    const [errorVisible, setErrorVisible] = useState(false);
    const [expandedItem, setExpandedItem] = useState(null);
    const navigate = useNavigate();
    const maxLength = 1000;

    useEffect(() => {
        const userData = localStorage.getItem('user');
        if (userData) {
            setUser(JSON.parse(userData));
            fetchAnalysisHistory();
        }
    }, []);

    useEffect(() => {
        let timeoutId;
        if (error) {
            setErrorVisible(true);
            timeoutId = setTimeout(() => {
                setErrorVisible(false);
                setTimeout(() => setError(''), 500); // Clear error after fade-out animation
            }, 3000); // Show error for 3 seconds
        }
        return () => clearTimeout(timeoutId);
    }, [error]);

    const fetchAnalysisHistory = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:5000/analysis-history', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setAnalysisHistory(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Error fetching history:', error);
            setAnalysisHistory([]);
        }
    };

    const checkNews = async () => {
        if (!text.trim()) {
            setError('Please enter some text to analyze');
            return;
        }

        if(text.length < 100)
        {
            setError('Text is too short. Please enter at least 100 characters.');
            return;
        }

        setError('');
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setError('Authentication required. Please log in again.');
                navigate('/login');
                return;
            }

            console.log('Sending request with token:', token);
            const response = await fetch('http://localhost:5000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ text }),
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (response.ok) {
                setResult(data);
                fetchAnalysisHistory();
            } else {
                if (response.status === 401) {
                    setError('Session expired. Please log in again.');
                    navigate('/login');
                } else if (response.status === 422) {
                    setError('Invalid request. Please try again.');
                } else {
                    setError(data.error || 'Analysis failed');
                }
                setResult(null);
            }
        } catch (error) {
            console.error('Error details:', error);
            setError('An error occurred while analyzing the text');
            setResult(null);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const charCountClassName = text.length >= maxLength ? 'char-count-limit-reached' : 'character-count-overlay';

    const fetchFullAnalysis = async (analysisId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:5000/analysis/${analysisId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            if (response.ok) {
                setText(data.text);
                setResult({
                    result: data.result,
                    confidence: data.confidence
                });

            } else {
                console.error('Error fetching analysis:', data.error);
            }
        } catch (error) {
            console.error('Error fetching analysis:', error);
        }
    };

    const toggleExpand = async (index) => {
        console.log('Toggle expand clicked for index:', index);
        setExpandedItem(expandedItem === index ? null : index);
        
        // Fetch the full text when clicking a history item
        const analysisId = analysisHistory[index].id;
        await fetchFullAnalysis(analysisId);
    };

    const deleteAnalysis = async (analysisId, event) => {
        event.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this analysis?')) {
            return;
        }
    
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:5000/analysis/${analysisId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                // Remove the deleted item from the history
                setAnalysisHistory(prevHistory => 
                    prevHistory.filter(item => item.id !== analysisId)
                );
                // If the deleted item was expanded, collapse it
                setExpandedItem(null);
                // If the deleted item was showing in the textarea, clear it
                setText('');
                setResult(null);
            } else {
                const data = await response.json();
                console.error('Error deleting analysis:', data.error);
            }
        } catch (error) {
            console.error('Error deleting analysis:', error);
        }
    };

    return (
        <div className="dashboard">
            <nav className="dashboard-nav">
                <div className="nav-title">
                    <a href="/">
                        <img src="/newspaper.png" alt="Fake News Detector Logo" className="nav-logo" />
                    </a>
                    <h1>Fake News Detector</h1>
                </div>
                <div className="user-info">
                    <span>Welcome, {user?.name}</span>
                    <button onClick={handleLogout}>Logout</button>
                </div>
            </nav>

            <div className="dashboard-content">
                <div className="analysis-section">
                    <h2>Analyze News</h2>
                    {error && (
                        <div className={`error-message ${!errorVisible ? 'fade-out' : ''}`}>
                            {error}
                        </div>
                    )}
                    <div className="textarea-wrapper">
                        <textarea
                            id="textarea"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Paste news article here..."
                            rows="10"
                            maxLength={maxLength}
                        />
                        <div className={charCountClassName}>
                            {text.length}/{maxLength}
                        </div>
                    </div>
                    <button onClick={checkNews} className="check-auth-button">Check Authenticity</button>

                    {result && (
                        <div className={`result ${result.result?.toLowerCase() || ''}`}>
                            <h3>Result: {result.result}</h3>
                            <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                        </div>
                    )}
                </div>

                <div className="history-section">
                    <h2>Analysis History</h2>
                    <div className="history-list">
                        {Array.isArray(analysisHistory) && analysisHistory.map((item, index) => (
                            <div 
                                key={index} 
                                className={`history-item ${expandedItem === index ? 'expanded' : ''}`}
                                onClick={() => toggleExpand(index)}
                            >
                                <p className="history-text">
                                    {expandedItem === index ? item.text : `${item.text.substring(0, 150)}...`}
                                </p>
                                <div className="history-details">
                                    <span className={`result-badge ${item.result.toLowerCase()}`}>
                                        {item.result}
                                    </span>
                                    <span className="confidence">
                                        {(item.confidence * 100).toFixed(1)}%
                                    </span>
                                    <span className="timestamp">{item.timestamp + " UTC"}</span>
                                    <button 
                                        className="delete-button"
                                        onClick={(e) => deleteAnalysis(item.id, e)}
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="warning">
                WARNING: This tool predicts fake news based on text patterns, not absolute truth.
            </div>
        </div>
    );
};

export default Dashboard; 