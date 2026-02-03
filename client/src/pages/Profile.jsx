import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import PlatformCard from '../components/PlatformCard';
import ConnectedAccountsList from '../components/ConnectedAccountsList';
import AccountSelectionModal from '../components/AccountSelectionModal';
import voiceService from '../services/voiceService';
import './Profile.css';

const API_BASE_URL = 'http://localhost:3001';

const Profile = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('basic');
    const [displayName, setDisplayName] = useState('');
    const [accounts, setAccounts] = useState([]);
    const [isLoadingAccounts, setIsLoadingAccounts] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    // Account selection modal state
    const [showAccountModal, setShowAccountModal] = useState(false);
    const [accountSelectionData, setAccountSelectionData] = useState(null);
    const [isConnectingAccounts, setIsConnectingAccounts] = useState(false);

    // Voice sample state
    const [voiceStatus, setVoiceStatus] = useState({ has_sample: false, loading: true });

    useEffect(() => {
        if (user?.email) {
            const name = user.email.split('@')[0];
            const formattedName = name
                .split(/[._-]/)
                .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
                .join(' ');
            setDisplayName(formattedName);
        }
    }, [user]);

    const getUserId = useCallback(() => {
        if (user?.id) return user.id;
        if (user?._id) return user._id;
        if (user?.sub) return user.sub;
        // Fallback: generate ID from email (matching VoiceSetup.jsx logic)
        if (user?.email) return user.email.replace('@', '_').replace('.', '_');
        return null;
    }, [user]);

    // Fetch voice sample status
    useEffect(() => {
        const checkVoice = async () => {
            const userId = getUserId();

            if (userId) {
                try {
                    const status = await voiceService.checkVoiceSample(userId);
                    const count = status.metadata?.samples?.length || (status.has_sample ? 1 : 0);
                    setVoiceStatus({
                        has_sample: status.has_sample,
                        sample_count: count,
                        loading: false
                    });
                } catch (error) {
                    console.error('Error checking voice sample:', error);
                    setVoiceStatus({ has_sample: false, sample_count: 0, loading: false });
                }
            } else {
                setVoiceStatus({ has_sample: false, sample_count: 0, loading: false });
            }
        };

        if (user) {
            checkVoice();
        }
    }, [user, getUserId]);

    const fetchAccounts = useCallback(async () => {
        setIsLoadingAccounts(true);
        try {
            const response = await axios.get(`${API_BASE_URL}/api/oauth/connected-accounts`, {
                withCredentials: true
            });
            if (response.data.success) {
                setAccounts(response.data.accounts);
            }
        } catch (error) {
            console.error('Error fetching accounts:', error);
        } finally {
            setIsLoadingAccounts(false);
        }
    }, []);

    useEffect(() => {
        fetchAccounts();
    }, [fetchAccounts]);

    // Listen for OAuth popup messages
    useEffect(() => {
        const handleOAuthMessage = async (event) => {
            console.log('--- OAuth Message Received ---');
            console.log('Origin:', event.origin);
            console.log('Data:', event.data);

            // Allow messages from the same origin or the API origin
            const isAllowed = event.origin === window.location.origin ||
                event.origin === API_BASE_URL ||
                event.origin.includes('localhost:3001') ||
                event.origin.includes('127.0.0.1:3001');

            if (!isAllowed) {
                console.warn('Origin not allowed. Expected:', window.location.origin, 'or', API_BASE_URL);
                return;
            }

            if (event.data && event.data.type === 'LINKEDIN_UNIFIED_SUCCESS') {
                console.log('LinkedIn Unified Success! Profile:', event.data.profile);
                console.log('Organizations:', event.data.organizations);

                setAccountSelectionData({
                    profile: event.data.profile,
                    organizations: event.data.organizations || [],
                    tokenSessionId: event.data.tokenSessionId,
                });
                setShowAccountModal(true);
                console.log('showAccountModal set to true');
            } else if (event.data && event.data.type === 'LINKEDIN_OAUTH_ERROR') {
                console.error('LinkedIn OAuth Error:', event.data.error);
                alert('Error: ' + (event.data.error || 'Failed to connect LinkedIn account'));
            }
        };

        window.addEventListener('message', handleOAuthMessage);
        return () => window.removeEventListener('message', handleOAuthMessage);
    }, []);

    const openOAuthPopup = useCallback((url) => {
        const width = 500;
        const height = 600;
        const left = window.screenX + (window.outerWidth - width) / 2;
        const top = window.screenY + (window.outerHeight - height) / 2;

        window.open(
            url,
            'LinkedIn OAuth',
            `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,status=yes`
        );
    }, []);

    const handleLinkedInClick = async () => {
        setIsConnecting(true);
        try {
            const response = await axios.get(`${API_BASE_URL}/api/oauth/linkedin/init`, {
                withCredentials: true
            });
            if (response.data.success && response.data.url) {
                openOAuthPopup(response.data.url);
            } else {
                throw new Error('Failed to get authorization URL');
            }
        } catch (error) {
            console.error('Error initializing LinkedIn OAuth:', error);
            alert('Failed to initialize LinkedIn connection');
        } finally {
            setIsConnecting(false);
        }
    };

    const handleConnectAccounts = async (personal, selectedOrgs, profile, tokenSessionId) => {
        setIsConnectingAccounts(true);
        try {
            const response = await axios.post(
                `${API_BASE_URL}/api/oauth/linkedin/connect-accounts`,
                { personal, organizations: selectedOrgs, profile, tokenSessionId },
                { withCredentials: true }
            );

            if (response.data.success) {
                const accountCount = response.data.accounts.length;
                alert(`Connected ${accountCount} account${accountCount > 1 ? 's' : ''}`);
                fetchAccounts();
                setShowAccountModal(false);
                setAccountSelectionData(null);
            }
        } catch (error) {
            alert(error.response?.data?.error || 'Failed to connect accounts');
        } finally {
            setIsConnectingAccounts(false);
        }
    };

    const handleDeleteAccount = async (platform, accountId) => {
        if (!window.confirm('Are you sure you want to disconnect this account?')) {
            return;
        }

        try {
            await axios.delete(
                `${API_BASE_URL}/api/oauth/connected-accounts/${platform.toLowerCase()}/${encodeURIComponent(accountId)}`,
                { withCredentials: true }
            );
            fetchAccounts();
            alert('Account disconnected successfully');
        } catch (error) {
            console.error('Error deleting account:', error);
            alert('Failed to disconnect the account');
        }
    };

    const handleReconnect = (platform) => {
        if (platform === 'linkedin') {
            handleLinkedInClick();
        }
    };

    const linkedinAccounts = accounts.filter(a => a.platform === 'linkedin');

    const getInitials = (email) => {
        if (!email) return 'CU';
        const parts = email.split('@')[0].split(/[._-]/);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return parts[0].substring(0, 2).toUpperCase();
    };

    return (
        <div className="profile-page">
            <div className="profile-header">
                <h1>Profile Settings</h1>
                <p>Manage your account and connected platforms</p>
            </div>

            <div className="tabs">
                <button
                    className={`tab ${activeTab === 'basic' ? 'active' : ''}`}
                    onClick={() => setActiveTab('basic')}
                >
                    Basic Info
                </button>
                <button
                    className={`tab ${activeTab === 'accounts' ? 'active' : ''}`}
                    onClick={() => setActiveTab('accounts')}
                >
                    Connected Accounts
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'basic' && (
                    <div className="card">
                        <h2>Your Profile</h2>
                        <div className="profile-info">
                            <div className="avatar-large">
                                {user && getInitials(user.email)}
                            </div>
                            <div className="user-details">
                                <h3>{displayName}</h3>
                                <p className="email">{user?.email}</p>
                                <span className="badge">User Account</span>
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="displayName">Display Name</label>
                            <input
                                id="displayName"
                                type="text"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                className="input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">Email Address</label>
                            <input
                                id="email"
                                type="email"
                                value={user?.email || ''}
                                disabled
                                className="input"
                            />
                        </div>

                        <div className="voice-sample-section">
                            <h3>🎤 Voice Sample</h3>
                            <p className="section-description">
                                {voiceStatus.has_sample
                                    ? "Your voice sample is uploaded and ready for cloning."
                                    : "Upload a voice sample to enable AI-generated speech in your voice"
                                }
                            </p>

                            {voiceStatus.loading ? (
                                <p>Loading voice status...</p>
                            ) : voiceStatus.has_sample ? (
                                <div className="voice-audio-player">
                                    <div className="voice-status-info" style={{ marginBottom: '10px', fontSize: '0.9em' }}>
                                        <strong>{voiceStatus.sample_count} clip{voiceStatus.sample_count !== 1 ? 's' : ''} uploaded.</strong>
                                        {voiceStatus.sample_count < 3 && (
                                            <span style={{ color: '#f59e0b', marginLeft: '8px' }}>
                                                ⚠️ Recommended: 3+ clips
                                            </span>
                                        )}
                                    </div>
                                    <audio
                                        controls
                                        src={voiceService.getAudioUrl(getUserId(), 'sample.wav')}
                                        className="w-full mt-4 mb-4"
                                    />
                                    <div className="voice-actions">
                                        <a href="/voice-setup" className="button secondary small">
                                            {voiceStatus.sample_count < 5 ? "Record More Samples" : "Re-record Samples"}
                                        </a>
                                    </div>
                                </div>
                            ) : (
                                <a href="/voice-setup" className="button secondary">
                                    Go to Voice Setup
                                </a>
                            )}
                        </div>

                        <button className="button primary">Save Profile</button>
                    </div>
                )}

                {activeTab === 'accounts' && (
                    <>
                        <div className="card">
                            <h2>Connect a Platform</h2>
                            <p className="subtitle">Select a social media platform to connect your account</p>

                            <div className="platforms-grid">
                                <PlatformCard
                                    platform="linkedin"
                                    name="LinkedIn"
                                    icon={
                                        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                                        </svg>
                                    }
                                    isConnected={linkedinAccounts.length > 0}
                                    connectedCount={linkedinAccounts.length}
                                    isLoading={isConnecting}
                                    onClick={handleLinkedInClick}
                                />
                                <PlatformCard
                                    platform="twitter"
                                    name="Twitter / X"
                                    icon={
                                        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                                        </svg>
                                    }
                                    isConnected={false}
                                    isComingSoon={true}
                                    onClick={() => { }}
                                />
                            </div>
                        </div>

                        <div className="card">
                            <h2>Connected Accounts</h2>
                            <p className="subtitle">Manage your connected social media accounts</p>

                            <ConnectedAccountsList
                                accounts={accounts}
                                isLoading={isLoadingAccounts}
                                onDelete={handleDeleteAccount}
                                onReconnect={handleReconnect}
                            />
                        </div>
                    </>
                )}
            </div>

            {/* Account Selection Modal */}
            {accountSelectionData && (
                <AccountSelectionModal
                    open={showAccountModal}
                    onOpenChange={setShowAccountModal}
                    profile={accountSelectionData.profile}
                    organizations={accountSelectionData.organizations}
                    tokenSessionId={accountSelectionData.tokenSessionId}
                    connectedAccounts={accounts}
                    onConnect={handleConnectAccounts}
                    isLoading={isConnectingAccounts}
                />
            )}
        </div>
    );
};

export default Profile;
