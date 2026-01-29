import api from './api';

/**
 * Chat Service - Handles chat API calls
 */

export const chatService = {
    /**
     * Send a message to the chat agent
     * @param {string} message - The user's message
     * @param {string} conversationId - Optional conversation ID
     * @param {string} model - The model to use (e.g., 'gemini-2.5-flash', 'gpt-4o')
     * @returns {Promise} Response from the chat agent
     */
    sendMessage: async (message, conversationId = null, model = 'gemini-2.5-flash') => {
        const response = await api.post('/api/chat/message', {
            message,
            conversation_id: conversationId,
            model
        });
        return response.data;
    },

    /**
     * Get all chat sessions for the current user
     * @returns {Promise} List of chat sessions
     */
    getSessions: async () => {
        const response = await api.get('/api/chat/sessions');
        return response.data;
    },

    /**
     * Create a new chat session
     * @param {string} model - The model to use for this session
     * @returns {Promise} Created session data
     */
    createSession: async (model = 'gemini-2.5-flash') => {
        const response = await api.post('/api/chat/sessions', { model });
        return response.data;
    },

    /**
     * Delete a chat session
     * @param {string} sessionId - Session ID to delete
     * @returns {Promise} Deletion confirmation
     */
    deleteSession: async (sessionId) => {
        const response = await api.delete(`/api/chat/sessions/${sessionId}`);
        return response.data;
    },

    /**
     * Get messages for a specific session
     * @param {string} sessionId - Session ID
     * @returns {Promise} Session messages
     */
    getSessionMessages: async (sessionId) => {
        const response = await api.get(`/api/chat/sessions/${sessionId}/messages`);
        return response.data;
    }
};
