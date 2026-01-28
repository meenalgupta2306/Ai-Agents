import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:3001';

const LinkedInOAuthCallback = () => {
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('loading');
    const [message, setMessage] = useState('Connecting to LinkedIn...');

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            const error = searchParams.get('error');
            const state = searchParams.get('state');

            // Handle error from LinkedIn
            if (error) {
                setStatus('error');
                setMessage(
                    error.includes('access_denied')
                        ? 'LinkedIn access was denied'
                        : 'Failed to connect LinkedIn account'
                );

                // Send error to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        { type: 'LINKEDIN_OAUTH_ERROR', error: error },
                        '*'
                    );
                }

                // Close popup after a short delay
                setTimeout(() => window.close(), 2000);
                return;
            }

            // No code received
            if (!code) {
                setStatus('error');
                setMessage('No authorization code received');
                setTimeout(() => window.close(), 2000);
                return;
            }

            try {
                // Call unified /finalize endpoint
                setMessage('Fetching your LinkedIn accounts...');

                const response = await axios.post(
                    `${API_BASE_URL}/api/oauth/linkedin/finalize`,
                    { code, state },
                    { withCredentials: true }
                );

                if (response.data.success) {
                    setStatus('success');
                    const { profile, organizations } = response.data;
                    const accountCount = 1 + (organizations?.length || 0);
                    setMessage(`Found ${accountCount} account${accountCount > 1 ? 's' : ''}!`);

                    // Send data to parent window for account selection
                    if (window.opener) {
                        window.opener.postMessage(
                            {
                                type: 'LINKEDIN_UNIFIED_SUCCESS',
                                profile: response.data.profile,
                                organizations: response.data.organizations || [],
                                tokenSessionId: response.data.tokenSessionId,
                            },
                            '*'
                        );
                    }

                    setTimeout(() => window.close(), 1500);
                } else {
                    throw new Error(response.data.error || 'Connection failed');
                }
            } catch (err) {
                console.error('LinkedIn OAuth error:', err);
                setStatus('error');
                setMessage(err.response?.data?.error || err.message || 'Failed to connect LinkedIn');

                // Send error to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        { type: 'LINKEDIN_OAUTH_ERROR', error: err.message },
                        '*'
                    );
                }

                // Close popup after a short delay
                setTimeout(() => window.close(), 3000);
            }
        };

        handleCallback();
    }, [searchParams]);

    return (
        <div style={{
            display: 'flex',
            height: '100vh',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            fontFamily: 'Arial, sans-serif'
        }}>
            <div style={{
                textAlign: 'center',
                padding: '2rem',
                background: 'white',
                borderRadius: '10px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }}>
                {status === 'loading' && (
                    <>
                        <div style={{
                            border: '3px solid #f3f3f3',
                            borderTop: '3px solid #0077B5',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            animation: 'spin 1s linear infinite',
                            margin: '20px auto'
                        }} />
                        <p style={{ fontSize: '18px', fontWeight: '500', color: '#1f2937' }}>{message}</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div style={{ fontSize: '48px', color: '#10b981', marginBottom: '16px' }}>✓</div>
                        <p style={{ fontSize: '18px', fontWeight: '500', color: '#1f2937' }}>{message}</p>
                        <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>
                            This window will close automatically...
                        </p>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div style={{ fontSize: '48px', color: '#ef4444', marginBottom: '16px' }}>✕</div>
                        <p style={{ fontSize: '18px', fontWeight: '500', color: '#1f2937' }}>{message}</p>
                        <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>
                            This window will close automatically...
                        </p>
                    </>
                )}
            </div>
            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export default LinkedInOAuthCallback;
