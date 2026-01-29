import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, type, timestamp }) => {
    const isUser = type === 'user';

    return (
        <div className={`chat-message ${isUser ? 'user-message' : 'ai-message'}`}>
            <div className="message-bubble">
                <div className="message-text">{message}</div>
                {timestamp && (
                    <div className="message-timestamp">
                        {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
