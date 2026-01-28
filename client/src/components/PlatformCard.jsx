import React from 'react';
import './PlatformCard.css';

const PlatformCard = ({
    platform,
    name,
    icon,
    isConnected,
    connectedCount = 0,
    isLoading,
    isComingSoon,
    onClick
}) => {
    return (
        <div className={`platform-card ${isConnected ? 'connected' : ''} ${isComingSoon ? 'coming-soon' : ''}`}>
            <div className="platform-icon">
                {icon}
            </div>
            <h3 className="platform-name">{name}</h3>

            {isComingSoon ? (
                <span className="badge coming-soon-badge">Coming Soon</span>
            ) : isConnected ? (
                <div className="connected-info">
                    <span className="badge connected-badge">
                        {connectedCount} Connected
                    </span>
                    <button
                        className="connect-button secondary"
                        onClick={onClick}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Connecting...' : 'Add More'}
                    </button>
                </div>
            ) : (
                <button
                    className="connect-button primary"
                    onClick={onClick}
                    disabled={isLoading}
                >
                    {isLoading ? 'Connecting...' : 'Connect'}
                </button>
            )}
        </div>
    );
};

export default PlatformCard;
