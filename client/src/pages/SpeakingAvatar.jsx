import React, { useState } from 'react';
import './SpeakingAvatar.css';

const SpeakingAvatar = () => {
    const [image, setImage] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [audio, setAudio] = useState(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleImageDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            setImage(file);
            setImagePreview(URL.createObjectURL(file));
        }
    };

    const handleImageSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImage(file);
            setImagePreview(URL.createObjectURL(file));
        }
    };

    const handleAudioSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setAudio(file);
        }
    };

    return (
        <div className="speaking-avatar-container">
            <div className="avatar-header">
                <h1>🎬 Speaking Avatar</h1>
                <p className="subtitle">
                    Upload an image and audio to generate a realistic video with lip-sync and natural expressions.
                </p>
            </div>

            <div className="avatar-content">
                {/* Image Upload */}
                <div className="section">
                    <h2>1. Upload Image</h2>
                    <div
                        className={`drop-zone ${isDragging ? 'dragging' : ''}`}
                        onDrop={handleImageDrop}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                        onDragLeave={() => setIsDragging(false)}
                        onClick={() => document.getElementById('image-input').click()}
                    >
                        {imagePreview ? (
                            <img src={imagePreview} alt="Preview" className="image-preview" />
                        ) : (
                            <div className="drop-zone-content">
                                <div className="upload-icon">📸</div>
                                <p>Drag & drop an image here</p>
                                <p className="or-text">or</p>
                                <button className="btn-browse">Browse Files</button>
                            </div>
                        )}
                        <input
                            id="image-input"
                            type="file"
                            accept="image/*"
                            onChange={handleImageSelect}
                            style={{ display: 'none' }}
                        />
                    </div>
                </div>

                {/* Audio Upload */}
                <div className="section">
                    <h2>2. Upload Audio</h2>
                    <div className="audio-upload">
                        <input
                            id="audio-input"
                            type="file"
                            accept="audio/*"
                            onChange={handleAudioSelect}
                            style={{ display: 'none' }}
                        />
                        <button
                            className="btn-upload-audio"
                            onClick={() => document.getElementById('audio-input').click()}
                        >
                            {audio ? `✓ ${audio.name}` : '🎵 Choose Audio File'}
                        </button>
                        {audio && (
                            <audio controls src={URL.createObjectURL(audio)} className="audio-player" />
                        )}
                    </div>
                </div>

                {/* Coming Soon Notice */}
                <div className="section coming-soon">
                    <h2>🚧 Coming Soon</h2>
                    <p>
                        Video generation with SadTalker is currently in development.
                        This feature will use Google Colab T4 GPU for processing.
                    </p>
                    <div className="feature-list">
                        <h3>What to expect:</h3>
                        <ul>
                            <li>✨ Realistic lip-sync with your audio</li>
                            <li>🎭 Natural facial expressions and head movements</li>
                            <li>🎬 High-quality video output</li>
                            <li>⚡ Cloud GPU processing for fast generation</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SpeakingAvatar;
