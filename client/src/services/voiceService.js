/**
 * Voice Service API Client
 */

const API_BASE_URL = 'http://localhost:3001/api/voice';

export const voiceService = {
    /**
     * Check if voice service is healthy
     */
    async checkHealth() {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.json();
    },

    /**
     * Upload voice sample
     * @param {string} userId - User ID
     * @param {Blob} audioBlob - Audio file blob
     * @param {string} filename - Filename
     */
    async uploadVoiceSample(userId, audioBlob, filename = 'sample.wav') {
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('audio_file', audioBlob, filename);

        const response = await fetch(`${API_BASE_URL}/upload-sample`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        return response.json();
    },

    /**
     * Check if user has a voice sample
     * @param {string} userId - User ID
     */
    async checkVoiceSample(userId) {
        const response = await fetch(`${API_BASE_URL}/check-sample?user_id=${userId}`);
        return response.json();
    },

    /**
     * Generate speech from text
     * @param {string} userId - User ID
     * @param {string} text - Text to convert to speech
     * @param {object} config - Optional configuration (temperature, speed, etc.)
     */
    async generateSpeech(userId, text, config = {}) {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                text: text,
                ...config
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Generation failed');
        }

        return response.json();
    },

    /**
     * Get audio URL for playback
     * @param {string} userId - User ID
     * @param {string} filename - Audio filename
     */
    getAudioUrl(userId, filename) {
        return `${API_BASE_URL}/audio/${userId}/${filename}`;
    },
};

export default voiceService;
