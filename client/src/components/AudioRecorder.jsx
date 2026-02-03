import React, { useState, useRef, useEffect } from 'react';
import './AudioRecorder.css';

const AudioRecorder = ({ onRecordingComplete, maxDuration = 15 }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [timeLeft, setTimeLeft] = useState(maxDuration);
    const [error, setError] = useState(null);

    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    useEffect(() => {
        return () => {
            // Cleanup
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [audioUrl]);

    const startRecording = async () => {
        try {
            setError(null);
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);
                setAudioBlob(blob);
                setAudioUrl(url);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                if (onRecordingComplete) {
                    onRecordingComplete(blob);
                }
            };

            mediaRecorder.start();
            setIsRecording(true);
            setTimeLeft(maxDuration);

            // Start countdown timer
            timerRef.current = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        stopRecording();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);

        } catch (err) {
            console.error('Error accessing microphone:', err);
            setError('Could not access microphone. Please grant permission.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);

            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        }
    };

    const resetRecording = () => {
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
        }
        setAudioBlob(null);
        setAudioUrl(null);
        setTimeLeft(maxDuration);
        setError(null);
    };

    return (
        <div className="audio-recorder">
            {error && (
                <div className="error-message">
                    {error}
                </div>
            )}

            <div className="recorder-controls">
                {!isRecording && !audioBlob && (
                    <button
                        className="btn-record"
                        onClick={startRecording}
                    >
                        🎤 Start Recording
                    </button>
                )}

                {isRecording && (
                    <div className="recording-status">
                        <button
                            className="btn-stop"
                            onClick={stopRecording}
                        >
                            ⏹ Stop Recording
                        </button>
                        <div className="timer">
                            <span className="recording-indicator">●</span>
                            Time left: {timeLeft}s
                        </div>
                    </div>
                )}

                {audioBlob && !isRecording && (
                    <div className="playback-controls">
                        <audio controls src={audioUrl} />
                        <button
                            className="btn-reset"
                            onClick={resetRecording}
                        >
                            🔄 Re-record
                        </button>
                    </div>
                )}
            </div>

            {isRecording && (
                <div className="recording-animation">
                    <div className="pulse"></div>
                </div>
            )}
        </div>
    );
};

export default AudioRecorder;
