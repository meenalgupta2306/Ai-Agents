import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:3001';

const OAuthCallback = () => {
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('loading');
    const [message, setMessage] = useState('Connecting...');

    // Determine platform from URL path
    const platform = window.location.pathname.includes('meta') ? 'meta' : 'linkedin';
    const platformName = platform === 'meta' ? 'Meta' : 'LinkedIn';

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            const error = searchParams.get('error');
            const state = searchParams.get('state');

            // Handle error from OAuth provider
            if (error) {
                setStatus('error');
                setMessage(
                    error.includes('access_denied')
                        ? `${platformName} access was denied`
                        : `Failed to connect ${platformName} account`
                );

                // Send error to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        { type: `${platform.toUpperCase()}_OAUTH_ERROR`, error: error },
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
                // Call /finalize endpoint for the appropriate platform
                setMessage(`Fetching your ${platformName} accounts...`);

                const endpoint = platform === 'linkedin'
                    ? `${API_BASE_URL}/api/oauth/linkedin/finalize`
                    : `${API_BASE_URL}/api/oauth/meta/finalize`;

                const response = await axios.post(
                    endpoint,
                    { code, state },
                    { withCredentials: true }
                );

                if (response.data.success) {
                    setStatus('success');

                    if (platform === 'linkedin') {
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
                    } else {
                        // Meta
                        const { profile, adAccounts } = response.data;
                        const accountCount = 1 + (adAccounts?.length || 0);
                        setMessage(`Found ${accountCount} account${accountCount > 1 ? 's' : ''}!`);

                        // Send data to parent window for account selection
                        if (window.opener) {
                            window.opener.postMessage(
                                {
                                    type: 'META_OAUTH_SUCCESS',
                                    profile: response.data.profile,
                                    adAccounts: response.data.adAccounts || [],
                                    tokenSessionId: response.data.tokenSessionId,
                                },
                                '*'
                            );
                        }
                    }

                    setTimeout(() => window.close(), 1500);
                } else {
                    throw new Error(response.data.error || 'Connection failed');
                }
            } catch (err) {
                console.error(`${platformName} OAuth error:`, err);
                setStatus('error');
                setMessage(err.response?.data?.error || err.message || `Failed to connect ${platformName}`);

                // Send error to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        { type: `${platform.toUpperCase()}_OAUTH_ERROR`, error: err.message },
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
                            borderTop: platform === 'linkedin' ? '3px solid #0077B5' : '3px solid #1877F2',
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

export default OAuthCallback;
