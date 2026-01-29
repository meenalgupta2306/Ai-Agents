import React from 'react';
import './SessionList.css';

const SessionList = ({ sessions, currentSessionId, onSessionSelect, onNewSession, onDeleteSession }) => {
    const formatDate = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    const getSessionPreview = (session) => {
        if (!session.messages || session.messages.length === 0) {
            return 'New conversation';
        }
        const lastUserMessage = session.messages
            .filter(m => m.role === 'user')
            .slice(-1)[0];
        if (lastUserMessage) {
            return lastUserMessage.content.substring(0, 50) + (lastUserMessage.content.length > 50 ? '...' : '');
        }
        return 'New conversation';
    };

    return (
        <div className="session-list">
            <div className="session-list-header">
                <h3>Chat Sessions</h3>
                <button className="new-session-btn" onClick={onNewSession} title="New Chat">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 5v14M5 12h14" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                </button>
            </div>

            <div className="sessions-container">
                {sessions.length === 0 ? (
                    <div className="empty-sessions">
                        <p>No chat sessions yet</p>
                        <button className="create-first-btn" onClick={onNewSession}>
                            Start New Chat
                        </button>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                            onClick={() => onSessionSelect(session.id)}
                        >
                            <div className="session-content">
                                <div className="session-preview">{getSessionPreview(session)}</div>
                                <div className="session-meta">
                                    <span className="session-time">{formatDate(session.updated_at || session.created_at)}</span>
                                    <span className="session-model">{session.model?.split('-')[0] || 'gemini'}</span>
                                </div>
                            </div>
                            <button
                                className="delete-session-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    if (window.confirm('Delete this chat session?')) {
                                        onDeleteSession(session.id);
                                    }
                                }}
                                title="Delete session"
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeWidth="2" strokeLinecap="round" />
                                </svg>
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default SessionList;
