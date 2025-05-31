import React from 'react';
import './NotFound.css';

const NotFound = () => {
    return (
        <div className="dashboard">
            <nav className="dashboard-nav">
                <div className="nav-title">
                    <a href="/">
                        <img src="/newspaper.png" alt="Fake News Detector Logo" className="nav-logo" />
                    </a>
                    <h1>Fake News Detector</h1>
                </div>
            </nav>
            <div className="not-found-container">
                <h1>404</h1>
                <h2>Page Not Found</h2>
            <p>The page you are looking for does not exist.</p>
            </div>
        </div>
    );
};

export default NotFound; 