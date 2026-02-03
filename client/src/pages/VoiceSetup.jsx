import React, { useState, useEffect } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import voiceService from '../services/voiceService';
import './VoiceSetup.css';

// Sample texts for users to read (12-15 seconds each)
const SAMPLE_TEXTS = [
    "Hello, I'm excited to create personalized teaching content. This voice sample will help generate natural-sounding audio for my lessons.",
    "Technology is transforming education. With AI-powered tools, we can create engaging and accessible learning experiences for everyone.",
    "Welcome to my course. In this lesson, we'll explore fascinating concepts and build practical skills together. Let's get started!",
    "Clear communication is essential for effective teaching. This sample captures my natural speaking style and tone.",
    "Learning should be interactive and fun. By personalizing content, we make education more engaging and memorable.",
];

const VoiceSetup = () => {
    const [currentText, setCurrentText] = useState('');
    const [audioBlob, setAudioBlob] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [error, setError] = useState(null);
    const [samples, setSamples] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Get user ID (for now, use email as ID)
    const getUserId = () => {
        return 'test@example.com'.replace('@', '_').replace('.', '_');
    };

    useEffect(() => {
        // Select random sample text
        selectRandomText();

        // Check if user already has samples
        checkExistingSamples();
    }, []);

    const selectRandomText = () => {
        const randomText = SAMPLE_TEXTS[Math.floor(Math.random() * SAMPLE_TEXTS.length)];
        setCurrentText(randomText);
    };

    const checkExistingSamples = async () => {
        setIsLoading(true);
        try {
            const result = await voiceService.checkVoiceSample(getUserId());
            if (result.metadata && result.metadata.samples) {
                setSamples(result.metadata.samples);
            } else if (result.has_sample) {
                // Backward compatibility for single sample
                // checkVoiceSample might return old format or synthesized new format
                // If service returns valid metadata with samples, use it
                // Otherwise assume 1 sample exists
                setSamples([{
                    filename: 'sample.wav',
                    uploaded_at: new Date().toISOString()
                }]);
            }
        } catch (err) {
            console.error('Error checking samples:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRecordingComplete = (blob) => {
        setAudioBlob(blob);
        setUploadSuccess(false);
        setError(null);
    };

    const handleUpload = async () => {
        if (!audioBlob) {
            setError('Please record audio first');
            return;
        }

        setIsUploading(true);
        setError(null);

        try {
            const result = await voiceService.uploadVoiceSample(
                getUserId(),
                audioBlob,
                `sample_${Date.now()}.wav` // Filename is ignored by backend now but good practice
            );

            setUploadSuccess(true);

            // Update samples list from response
            if (result.sample_info) {
                setSamples(prev => [...prev, result.sample_info]);
            } else {
                // Fallback if backend doesn't return sample_info
                checkExistingSamples();
            }

            // Reset recording state
            setAudioBlob(null);
            selectRandomText(); // Get new text for next sample

            // Reset success message after 3 seconds
            setTimeout(() => {
                setUploadSuccess(false);
            }, 3000);

        } catch (err) {
            setError(err.message || 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    const handleNewSampleText = () => {
        selectRandomText();
        setAudioBlob(null);
        setUploadSuccess(false);
        setError(null);
    };

    return (
        <div className="voice-setup-container">
            <div className="voice-setup-card">
                <h1>🎤 Voice Sample Setup</h1>
                <p className="subtitle">
                    Record 3-5 short audio clips (10-15s each) to clone your voice.
                    <br />
                    More samples = Better quality!
                </p>

                {isLoading ? (
                    <p>Loading your voice profile...</p>
                ) : (
                    <div className="samples-status-section">
                        <div className="status-header">
                            <h3>Recorded Samples ({samples.length}/5)</h3>
                            <span className={`status-badge ${samples.length >= 3 ? 'success' : 'warning'}`}>
                                {samples.length >= 3 ? '✅ Ready to use' : '⚠️ Record at least 3 clips'}
                            </span>
                        </div>

                        {samples.length > 0 ? (
                            <ul className="samples-list">
                                {samples.map((sample, index) => (
                                    <li key={index} className="sample-item">
                                        <span className="sample-icon">🎵</span>
                                        <span className="sample-name">Clip {index + 1}</span>
                                        <span className="sample-duration">
                                            {sample.duration_seconds ? `${sample.duration_seconds.toFixed(1)}s` : ''}
                                        </span>
                                        <span className="sample-date">
                                            {new Date(sample.uploaded_at).toLocaleDateString()}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="no-samples">No samples recorded yet. Start below!</p>
                        )}
                    </div>
                )}

                {samples.length < 5 && (
                    <>
                        <div className="sample-text-section">
                            <h3>📝 Read this text aloud:</h3>
                            <div className="sample-text-box">
                                <p>{currentText}</p>
                            </div>
                            <button className="btn-new-text" onClick={handleNewSampleText}>
                                🔄 Get different text
                            </button>
                        </div>

                        <div className="recorder-section">
                            <h3>🎙️ Record Clip #{samples.length + 1}:</h3>
                            <AudioRecorder
                                onRecordingComplete={handleRecordingComplete}
                                maxDuration={15}
                            />
                        </div>

                        {error && (
                            <div className="error-box">
                                ⚠️ {error}
                            </div>
                        )}

                        {uploadSuccess && (
                            <div className="success-box">
                                ✅ Clip uploaded successfully! Ready for the next one.
                            </div>
                        )}

                        <div className="action-buttons">
                            <button
                                className="btn-upload"
                                onClick={handleUpload}
                                disabled={!audioBlob || isUploading}
                            >
                                {isUploading ? '⏳ Uploading...' : '📤 Upload Clip'}
                            </button>
                        </div>
                    </>
                )}

                {samples.length >= 5 && (
                    <div className="completion-message">
                        <h3>🎉 You've reached the maximum number of samples!</h3>
                        <p>Your voice clone should sound great. You can see your status in your profile.</p>
                        <a href="/profile" className="btn-primary">Go to Profile</a>
                    </div>
                )}

                <div className="info-section">
                    <h4>💡 Tips for best results:</h4>
                    <ul>
                        <li>Record in a quiet environment (Critical!)</li>
                        <li>Speak naturally, like you're teaching a class</li>
                        <li>Keep consistent volume across clips</li>
                        <li>We automatically clean up noise and silence</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default VoiceSetup;
