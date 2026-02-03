import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Solutions.css';

const Solutions = () => {
    const navigate = useNavigate();

    const features = [
        {
            id: 'voice-cloning',
            title: '🎤 Voice Cloning',
            description: 'Transform text into speech using your voice samples. Upload voice clips and generate natural-sounding audio in your own voice.',
            route: '/voice-cloning-demo',
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            icon: '🎙️'
        },
        {
            id: 'speaking-avatar',
            title: '🎬 Speaking Avatar',
            description: 'Bring images to life! Upload a photo and audio to generate a realistic video of the person speaking with natural lip-sync and expressions.',
            route: '/speaking-avatar',
            gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            icon: '🎭'
        }
    ];

    return (
        <div className="solutions-container">
            <div className="solutions-header">
                <h1>🚀 AI Solutions Showcase</h1>
                <p className="subtitle">
                    Explore our proof-of-concept AI features. Each solution demonstrates
                    cutting-edge AI capabilities for content creation.
                </p>
            </div>

            <div className="features-grid">
                {features.map((feature) => (
                    <div
                        key={feature.id}
                        className="feature-card"
                        onClick={() => navigate(feature.route)}
                        style={{ background: feature.gradient }}
                    >
                        <div className="feature-icon">{feature.icon}</div>
                        <h2>{feature.title}</h2>
                        <p>{feature.description}</p>
                        <button className="feature-button">
                            Try it now →
                        </button>
                    </div>
                ))}
            </div>

            <div className="info-banner">
                <h3>💡 About These Features</h3>
                <p>
                    These are experimental proof-of-concept implementations showcasing
                    AI-powered content generation. Perfect for testing and demonstrations.
                </p>
            </div>
        </div>
    );
};

export default Solutions;
