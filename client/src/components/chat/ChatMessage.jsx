import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, type, timestamp }) => {
    const isUser = type === 'user';

    const handleReportClick = async (filename) => {
        try {
            console.log('Fetching report:', filename);
            const response = await fetch(`http://localhost:3001/api/chat/reports/${filename}`);
            console.log('Response status:', response.status);

            if (!response.ok) {
                throw new Error(`Failed to fetch report: ${response.status}`);
            }

            let htmlContent = await response.text();
            console.log('HTML content length:', htmlContent.length);

            // Replace relative image/chart paths with absolute URLs
            htmlContent = htmlContent.replace(/src="\.\.\/images\//g, 'src="http://localhost:3001/api/chat/reports/images/');
            htmlContent = htmlContent.replace(/src="\.\.\/charts\//g, 'src="http://localhost:3001/api/chat/reports/charts/');

            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            console.log('Blob URL created:', url);

            const newWindow = window.open(url, '_blank');
            if (!newWindow) {
                alert('Please allow popups for this site to view the report');
            }

            // Clean up the URL after a longer delay to ensure it loads
            setTimeout(() => URL.revokeObjectURL(url), 5000);
        } catch (error) {
            console.error('Error opening report:', error);
            alert(`Failed to open report: ${error.message}`);
        }
    };

    const renderMessage = () => {
        // Debug: log the raw message
        console.log('Raw message:', message);

        // Try to parse as JSON
        try {
            const parsed = JSON.parse(message);
            console.log('Parsed JSON:', parsed);

            if (parsed.message && parsed.action) {
                console.log('Has message and action fields');
                const { message: text, action } = parsed;

                // Replace {{REPORT_LINK}} with clickable link
                if (text.includes('{{REPORT_LINK}}')) {
                    console.log('Found {{REPORT_LINK}} placeholder');
                    const parts = text.split('{{REPORT_LINK}}');
                    return (
                        <>
                            {parts[0]}
                            <span
                                className="report-link"
                                onClick={() => handleReportClick(action.filename)}
                            >
                                {action.label}
                            </span>
                            {parts[1]}
                        </>
                    );
                }

                return text;
            }
        } catch (e) {
            // Not JSON, render as plain text
            console.log('Not JSON, rendering as plain text');
        }

        return message;
    };

    return (
        <div className={`chat-message ${isUser ? 'user-message' : 'ai-message'}`}>
            <div className="message-bubble">
                <div className="message-text">{renderMessage()}</div>
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
