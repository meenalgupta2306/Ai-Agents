import React, { useState } from 'react';
import voiceService from '../services/voiceService';
import './VoiceTestPanel.css';

const VoiceTestPanel = () => {
    const [text, setText] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    const [config, setConfig] = useState({
        temperature: 0.75,
        speed: 1.0,
        repetition_penalty: 2.0
    });

    const getUserId = () => {
        return 'test@example.com'.replace('@', '_').replace('.', '_');
    };

    const handleGenerate = async () => {
        if (!text.trim()) {
            setError('Please enter some text');
            return;
        }

        setIsGenerating(true);
        setError(null);
        setSuccess(false);
        setAudioUrl(null);

        try {
            // Pass config parameters along with text
            const result = await voiceService.generateSpeech(getUserId(), text, config);

            if (result.audio_url) {
                setAudioUrl(result.audio_url);
                setSuccess(true);
            } else {
                setError('No audio URL returned');
            }
        } catch (err) {
            setError(err.message || 'Generation failed');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownload = () => {
        if (audioUrl) {
            const link = document.createElement('a');
            link.href = audioUrl;
            link.download = 'generated_speech.wav';
            link.click();
        }
    };

    return (
        <div className="voice-test-panel">
            <h3>🎙️ Test Voice Generation</h3>
            <p className="panel-description">
                Enter text below to generate speech in your cloned voice
            </p>

            <div className="tuning-section" style={{ marginBottom: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
                <h4>Tune Generation</h4>

                <div className="control-group" style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Stability (Temperature): {config.temperature}</span>
                        <span style={{ fontSize: '0.8em', color: '#666' }}>Lower = More Stable</span>
                    </label>
                    <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.05"
                        value={config.temperature}
                        onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="control-group">
                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Speed: {config.speed}x</span>
                    </label>
                    <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={config.speed}
                        onChange={(e) => setConfig({ ...config, speed: parseFloat(e.target.value) })}
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            <div className="text-input-section">
                <textarea
                    className="text-input"
                    placeholder="Enter text to convert to speech..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={5}
                    maxLength={5000}
                />
                <div className="char-count">
                    {text.length} / 5000 characters
                </div>
            </div>

            {error && (
                <div className="error-message">
                    ⚠️ {error}
                </div>
            )}

            {success && (
                <div className="success-message">
                    ✅ Speech generated successfully!
                </div>
            )}

            <button
                className="btn-generate"
                onClick={handleGenerate}
                disabled={isGenerating || !text.trim()}
            >
                {isGenerating ? '⏳ Generating...' : '🎵 Generate Speech'}
            </button>

            {audioUrl && (
                <div className="audio-player-section">
                    <h4>🔊 Generated Audio:</h4>
                    <audio controls src={audioUrl} />
                    <button className="btn-download" onClick={handleDownload}>
                        📥 Download Audio
                    </button>
                </div>
            )}
        </div>
    );
};

export default VoiceTestPanel;
