import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AudioRecorder from '../components/AudioRecorder';
import './VoiceCloningDemo.css';

// Sample texts for recording (longer, more natural)
const SAMPLE_TEXTS = [
    "Hello, I'm excited to demonstrate this voice cloning technology. This sample will help create a natural-sounding voice model that captures my unique speaking style, tone, and rhythm. As I speak, I’m intentionally varying my pace and emphasis to help the system learn how my voice naturally flows in conversation.",
    "Technology is rapidly transforming how we communicate and create content. With AI-powered tools like this, we are no longer limited to generic voices. Instead, we can generate personalized audio that sounds authentic, expressive, and engaging, while still remaining clear and easy to understand for listeners.",
    "Welcome to this demonstration of voice synthesis. In just a few moments, you will hear how advanced AI systems can analyze speech patterns, pronunciation, and timing to replicate human speech with remarkable accuracy. This process allows machines to speak in a way that feels natural rather than robotic.",
    "Clear and expressive communication is essential in today’s digital world, especially when information is delivered through audio or video. This voice cloning system carefully analyzes pitch, pauses, stress, and emotion to produce high-quality speech that sounds consistent and pleasant across different types of content.",
    "Learning new technologies should always feel accessible and intuitive. By providing just a few carefully recorded voice samples, we can build a personalized text-to-speech system that preserves your unique vocal identity while remaining flexible enough to adapt to different tones and contexts.",
    "This sample is being spoken at a calm and steady pace, with clear pronunciation and natural pauses between sentences. The goal is to help the voice model understand how my voice behaves during longer explanations, where clarity and consistency are more important than speed.",
    "Now I will read a slightly longer passage to demonstrate how my voice sounds over extended speech. Notice how the pitch rises and falls naturally, and how certain words are emphasized to convey meaning. These subtle details are important for creating a realistic and pleasant synthesized voice.",
    "In real-world applications, a voice like this could be used for teaching, storytelling, product demonstrations, or virtual assistants. The more varied and expressive the input samples are, the better the system becomes at reproducing a voice that feels human, relatable, and engaging to listeners.",
    "As this recording continues, I am maintaining a consistent microphone distance and speaking in a relaxed manner. This helps reduce background noise and sudden volume changes, making it easier for the model to focus on the true characteristics of my voice rather than environmental distractions.",
    "Finally, this sample concludes with a smooth and natural ending. Ending sentences clearly and without rushing is just as important as starting them well. Together, all of these samples contribute to a stronger, more accurate voice cloning result."
];


const VoiceCloningDemo = () => {
    const navigate = useNavigate();
    const [sampleSets, setSampleSets] = useState([]);
    const [selectedSetId, setSelectedSetId] = useState('');
    const [selectionMode, setSelectionMode] = useState('profile'); // 'profile', 'library', 'new'
    const [newSetSamples, setNewSetSamples] = useState([]);
    const [currentSampleText, setCurrentSampleText] = useState('');
    const [text, setText] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedAudio, setGeneratedAudio] = useState(null);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [generationHistory, setGenerationHistory] = useState([]);
    const [recordedBlob, setRecordedBlob] = useState(null);

    useEffect(() => {
        loadSampleSets();
        selectRandomText();
    }, []);

    const selectRandomText = () => {
        const randomText = SAMPLE_TEXTS[Math.floor(Math.random() * SAMPLE_TEXTS.length)];
        setCurrentSampleText(randomText);
    };

    const loadGenerationHistory = async (setId) => {
        try {
            const response = await fetch(
                `http://localhost:3001/api/voice-cloning/sample-sets/${setId}/history?t=${Date.now()}`
            );
            const data = await response.json();
            if (data.status === 'success') {
                setGenerationHistory(data.history);
            }
        } catch (err) {
            console.error('Error loading history:', err);
        }
    };

    const loadSampleSets = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/voice-cloning/sample-sets');
            const data = await response.json();
            if (data.status === 'success') {
                setSampleSets(data.sample_sets);

                // Auto-select first profile set if available and nothing else selected
                if (!selectedSetId) {
                    const profileSet = data.sample_sets.find(s => s.set_type === 'profile');
                    if (profileSet) {
                        setSelectedSetId(profileSet.set_id);
                        setSelectionMode('profile');
                        loadGenerationHistory(profileSet.set_id);
                    }
                }
            }
        } catch (err) {
            console.error('Error loading sample sets:', err);
        }
    };

    const handleCreateNewSet = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/voice-cloning/sample-sets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ set_type: 'demo' })
            });
            const data = await response.json();
            if (data.status === 'success') {
                setSelectedSetId(data.set_id);
                setNewSetSamples([]);
                loadSampleSets();
            }
        } catch (err) {
            setError('Failed to create new sample set');
        }
    };

    const handleModeChange = (mode) => {
        setSelectionMode(mode);
        if (mode === 'new') {
            setSelectedSetId(''); // Clear temporarily until set created
            setNewSetSamples([]);
            setRecordedBlob(null);
            handleCreateNewSet();
        }
    };

    const handleSelectSet = (setId) => {
        setSelectedSetId(setId);
        setSelectionMode('library');
        loadGenerationHistory(setId);
        setTimeout(() => {
            document.getElementById('workbench')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    const handleUploadSample = async () => {
        if (!recordedBlob || !selectedSetId) return;

        const formData = new FormData();
        formData.append('audio_file', recordedBlob, 'sample.wav');

        try {
            const response = await fetch(
                `http://localhost:3001/api/voice-cloning/sample-sets/${selectedSetId}/upload`,
                { method: 'POST', body: formData }
            );
            const data = await response.json();
            if (data.status === 'success') {
                setNewSetSamples([...newSetSamples, data.sample_info]);
                setRecordedBlob(null);
                setSuccess('Sample uploaded successfully!');
                setTimeout(() => setSuccess(null), 3000);
                // Reload sets to update sample count in library
                loadSampleSets();
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError('Failed to upload sample');
        }
    };

    const handleGenerate = async () => {
        if (!text || !selectedSetId) {
            setError('Please select a sample set and enter text');
            return;
        }

        setIsGenerating(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:3001/api/voice-cloning/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ set_id: selectedSetId, text })
            });
            const data = await response.json();
            if (data.status === 'success') {
                setGeneratedAudio(data.generation);
                loadGenerationHistory(selectedSetId);
                setSuccess('Speech generated successfully!');
                setTimeout(() => setSuccess(null), 3000);
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError('Failed to generate speech');
        } finally {
            setIsGenerating(false);
        }
    };

    const isReadyToGenerate = () => {
        if (!text.trim()) return false;
        if (!selectedSetId) return false;

        const set = sampleSets.find(s => s.set_id === selectedSetId);
        if (!set) return false;

        // If it's a demo set, require minimum samples
        if (set.set_type === 'demo') {
            const count = set.total_samples || 0;
            if (count < 3) return false;
        }

        return true;
    };

    const getPreviewSample = (set) => {
        if (set.samples && set.samples.length > 0) {
            // Prefer the latest sample
            return set.samples[set.samples.length - 1];
        }
        return null;
    };

    return (
        <div className="voice-cloning-demo-container">
            <div className="demo-header">
                <button className="btn-back" onClick={() => navigate('/solutions')}>
                    ← Back to Solutions
                </button>
                <h1>🎤 Voice Cloning Demo</h1>
                <p className="subtitle">
                    Select a voice from your library or create a new one to generate speech.
                </p>
            </div>

            <div className="demo-content">

                {/* Voice Library Section */}
                <div className="section library-section">
                    <div className="section-header">
                        <h2>📚 Voice Library</h2>
                        <button className="btn-create-new" onClick={() => handleModeChange('new')}>
                            + Create New Voice
                        </button>
                    </div>

                    <div className="voice-grid">
                        {sampleSets.map((set) => {
                            const preview = getPreviewSample(set);
                            const isSelected = selectedSetId === set.set_id;
                            return (
                                <div
                                    key={set.set_id}
                                    className={`voice-card ${isSelected ? 'selected' : ''}`}
                                    onClick={() => handleSelectSet(set.set_id)}
                                >
                                    <div className="voice-card-header">
                                        <span className={`badge ${set.set_type}`}>
                                            {set.set_type === 'profile' ? '👤 Profile' : '🧪 Demo'}
                                        </span>
                                        <span className="sample-count">{set.total_samples} samples</span>
                                    </div>
                                    <div className="voice-card-body">
                                        <h3>{set.set_type === 'profile' ? 'My Voice' : `Voice Set ${set.set_id.substring(4, 10)}`}</h3>
                                        <p className="set-date">{new Date(set.created_at).toLocaleDateString()}</p>
                                    </div>
                                    <div className="voice-card-preview" onClick={(e) => e.stopPropagation()}>
                                        {preview ? (
                                            <audio
                                                controls
                                                controlsList="nodownload"
                                                src={`http://localhost:3001/api/voice-cloning/sample/${set.set_id}/${preview.filename}`}
                                            />
                                        ) : (
                                            <div className="no-preview">No audio samples</div>
                                        )}
                                    </div>
                                    {isSelected && <div className="selected-indicator">✓ Selected</div>}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Workbench Section (Generation & History) */}
                <div id="workbench" className={`section workbench-section ${!selectedSetId ? 'disabled' : ''}`}>
                    <h2>⚡ Generation Workbench</h2>
                    {!selectedSetId ? (
                        <div className="empty-state">
                            <p>👈 Select a voice from the library above to start generating.</p>
                        </div>
                    ) : (
                        (() => {
                            const currentSet = sampleSets.find(s => s.set_id === selectedSetId);
                            const isDemoSet = currentSet?.set_type === 'demo';
                            const sampleCount = (currentSet?.total_samples || 0);

                            return (
                                <>
                                    {/* Management Section for Demo Sets */}
                                    {isDemoSet && (
                                        <div className="management-section">
                                            <h3>🧪 Manage Voice Samples</h3>
                                            <div className="upload-section compact-upload">
                                                <p className="samples-count">
                                                    Current samples: <strong>{sampleCount}</strong>/5
                                                    {sampleCount < 3 && <span className="warning-badge"> (Min 3 required)</span>}
                                                </p>

                                                {sampleCount < 5 && !recordedBlob && currentSampleText && (
                                                    <div className="text-prompt-mini">
                                                        <p><strong>Read:</strong> "{currentSampleText}"</p>
                                                        <button className="btn-text-refresh" onClick={selectRandomText}>🔄</button>
                                                    </div>
                                                )}
                                                {!recordedBlob && <span className="instruction-text">Record a sample to add...</span>}

                                                {sampleCount < 5 && (
                                                    <div className="upload-row">
                                                        <div className="recorder-wrapper">
                                                            <AudioRecorder
                                                                onRecordingComplete={setRecordedBlob}
                                                                maxDuration={20}
                                                            />
                                                        </div>

                                                        <div className="upload-actions">
                                                            {recordedBlob && (
                                                                <button
                                                                    className="btn-upload small"
                                                                    onClick={handleUploadSample}
                                                                >
                                                                    📤 Upload Recording
                                                                </button>
                                                            )}
                                                            
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    <div className="workbench-input">
                                        <div className="text-area-container">
                                            <label>Enter Text to Generate:</label>
                                            <textarea
                                                className="text-input"
                                                placeholder={`Generate speech using selected voice...`}
                                                value={text}
                                                onChange={(e) => setText(e.target.value)}
                                                rows={3}
                                            />
                                        </div>

                                        <div className="generate-actions">
                                            <button
                                                className="btn-generate icon-btn"
                                                onClick={handleGenerate}
                                                disabled={!isReadyToGenerate() || isGenerating}
                                            >
                                                {isGenerating ? '⏳ Generating...' : '✨ Generate Speech'}
                                            </button>
                                        </div>
                                    </div>

                                    {selectedSetId && selectionMode === 'new' && newSetSamples.length < 3 && (
                                        <p className="warning-text">⚠️ Please upload at least 3 samples to enable generation.</p>
                                    )}

                                    {/* Messages */}
                                    {error && <div className="error-box">⚠️ {error}</div>}
                                    {success && <div className="success-box">✅ {success}</div>}

                                    {/* Most Recent Generation */}
                                    {generatedAudio && (
                                        <div className="latest-result">
                                            <h3>🎉 Latest Generation</h3>
                                            <div className="audio-player highlight-player">
                                                <div className="audio-info">
                                                    <span className="file-name">{generatedAudio.audio_filename}</span>
                                                </div>
                                                <audio
                                                    controls
                                                    autoPlay
                                                    src={`http://localhost:3001/api/voice-cloning/audio/${selectedSetId}/${generatedAudio.audio_filename}`}
                                                />
                                                <a
                                                    href={`http://localhost:3001/api/voice-cloning/audio/${selectedSetId}/${generatedAudio.audio_filename}`}
                                                    download
                                                    className="btn-icon"
                                                    title="Download"
                                                >
                                                    ⬇️
                                                </a>
                                            </div>
                                        </div>
                                    )}

                                    {/* Generation History Table */}
                                    <div className="history-container">
                                        <h3>📜 History</h3>
                                        {generationHistory.length > 0 ? (
                                            <div className="history-list compact">
                                                {generationHistory.map((item, index) => (
                                                    <div key={index} className="history-item-compact">
                                                        <div className="history-meta-compact">
                                                            <span className="date">{new Date(item.generated_at).toLocaleTimeString()}</span>
                                                        </div>
                                                        <div className="history-content-compact">
                                                            <div className="text-preview">"{item.text.substring(0, 60)}{item.text.length > 60 ? '...' : ''}"</div>
                                                            <audio
                                                                controls
                                                                src={`http://localhost:3001/api/voice-cloning/audio/${item.set_id}/${item.audio_filename}`}
                                                            />
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="no-history">No history for this voice yet.</p>
                                        )}
                                    </div>
                                </>
                            );
                        })()
                    )}
                </div>
            </div>
        </div>
    );
};

export default VoiceCloningDemo;
