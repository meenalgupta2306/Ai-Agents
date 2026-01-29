import React, { useEffect, useRef } from 'react';
import ChatMessage from '../components/chat/ChatMessage';
import ChatInput from '../components/chat/ChatInput';
import ModelSelector from '../components/chat/ModelSelector';
import SessionList from '../components/chat/SessionList';
import { chatService } from '../services/chatService';
import './Chat.css';

const Chat = () => {
    const [messages, setMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [sessions, setSessions] = React.useState([]);
    const [currentSessionId, setCurrentSessionId] = React.useState(null);
    const [selectedModel, setSelectedModel] = React.useState('gemini-2.5-flash');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load sessions on mount
    useEffect(() => {
        loadSessions();
    }, []);

    // Load messages when session changes
    useEffect(() => {
        if (currentSessionId) {
            loadSessionMessages(currentSessionId);
        }
    }, [currentSessionId]);

    const loadSessions = async () => {
        try {
            const response = await chatService.getSessions();
            setSessions(response.sessions || []);

            // If no current session and sessions exist, select the first one
            if (!currentSessionId && response.sessions && response.sessions.length > 0) {
                setCurrentSessionId(response.sessions[0].id);
                setSelectedModel(response.sessions[0].model || 'gemini-2.5-flash');
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    };

    const loadSessionMessages = async (sessionId) => {
        try {
            const response = await chatService.getSessionMessages(sessionId);
            const sessionMessages = response.messages || [];

            // Convert to UI format
            const formattedMessages = sessionMessages.map((msg, idx) => ({
                id: idx,
                text: msg.content,
                type: msg.role === 'user' ? 'user' : 'ai',
                timestamp: msg.timestamp
            }));

            setMessages(formattedMessages);
        } catch (error) {
            console.error('Error loading session messages:', error);
            setMessages([]);
        }
    };

    const handleNewSession = async () => {
        try {
            const response = await chatService.createSession(selectedModel);
            const newSession = response.session;

            setSessions(prev => [newSession, ...prev]);
            setCurrentSessionId(newSession.id);
            setMessages([]);
        } catch (error) {
            console.error('Error creating session:', error);
        }
    };

    const handleSessionSelect = (sessionId) => {
        const session = sessions.find(s => s.id === sessionId);
        if (session) {
            setCurrentSessionId(sessionId);
            setSelectedModel(session.model || 'gemini-2.0-flash-exp');
        }
    };

    const handleDeleteSession = async (sessionId) => {
        try {
            await chatService.deleteSession(sessionId);
            setSessions(prev => prev.filter(s => s.id !== sessionId));

            // If deleted session was current, clear it
            if (sessionId === currentSessionId) {
                setCurrentSessionId(null);
                setMessages([]);

                // Select first remaining session if any
                const remainingSessions = sessions.filter(s => s.id !== sessionId);
                if (remainingSessions.length > 0) {
                    setCurrentSessionId(remainingSessions[0].id);
                }
            }
        } catch (error) {
            console.error('Error deleting session:', error);
        }
    };

    const handleModelChange = (model) => {
        setSelectedModel(model);
        // Note: Model change doesn't affect existing session
        // New messages will use the new model
    };

    const handleSendMessage = async (messageText) => {
        // If no session exists, create one
        if (!currentSessionId) {
            await handleNewSession();
            // Wait a bit for session to be created
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        // Add user message to chat
        const userMessage = {
            id: Date.now(),
            text: messageText,
            type: 'user',
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);
        setLoading(true);

        try {
            const response = await chatService.sendMessage(messageText, currentSessionId, selectedModel);

            // Add AI response
            const aiMessage = {
                id: Date.now() + 1,
                text: response.message,
                type: 'ai',
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, aiMessage]);

            // Reload sessions to update timestamps
            loadSessions();
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = {
                id: Date.now() + 1,
                text: 'Sorry, I encountered an error. Please try again.',
                type: 'ai',
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-page-with-sidebar">
            <SessionList
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSessionSelect={handleSessionSelect}
                onNewSession={handleNewSession}
                onDeleteSession={handleDeleteSession}
            />

            <div className="chat-main">
                <div className="chat-container">
                    <div className="chat-header">
                        <div className="chat-header-content">
                            <h2>AI Agent</h2>
                            <p>Ask me anything! I can help you with research, managing accounts, and more.</p>
                        </div>
                        <ModelSelector
                            selectedModel={selectedModel}
                            onModelChange={handleModelChange}
                            disabled={loading}
                        />
                    </div>

                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <div className="empty-state">
                                <div className="empty-icon">💬</div>
                                <h3>Start a conversation</h3>
                                <p>Try asking:</p>
                                <ul>
                                    <li>"What accounts are connected?"</li>
                                    <li>"Research AI trends"</li>
                                    <li>"Generate an image of a robot"</li>
                                </ul>
                            </div>
                        )}

                        {messages.map((msg) => (
                            <ChatMessage
                                key={msg.id}
                                message={msg.text}
                                type={msg.type}
                                timestamp={msg.timestamp}
                            />
                        ))}

                        {loading && (
                            <div className="typing-indicator">
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    <ChatInput onSend={handleSendMessage} disabled={loading} />
                </div>
            </div>
        </div>
    );
};

export default Chat;
