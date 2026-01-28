import React, { useState } from 'react';
import './AccountSelectionModal.css';

const AccountSelectionModal = ({
    open,
    onOpenChange,
    profile,
    organizations,
    tokenSessionId,
    connectedAccounts,
    onConnect,
    isLoading
}) => {
    const [selectedPersonal, setSelectedPersonal] = useState(false);
    const [selectedOrgs, setSelectedOrgs] = useState([]);

    if (!open) return null;

    const isPersonalConnected = connectedAccounts.some(
        acc => acc.platform === 'linkedin' && acc.type === 'personal' && acc.accountId === profile.urn
    );

    const isOrgConnected = (orgUrn) => {
        return connectedAccounts.some(
            acc => acc.platform === 'linkedin' && acc.type === 'organization' && acc.accountId === orgUrn
        );
    };

    const handleOrgToggle = (org) => {
        if (isOrgConnected(org.urn)) return;

        setSelectedOrgs(prev => {
            const exists = prev.find(o => o.urn === org.urn);
            if (exists) {
                return prev.filter(o => o.urn !== org.urn);
            } else {
                return [...prev, org];
            }
        });
    };

    const handleConnect = () => {
        onConnect(selectedPersonal, selectedOrgs, profile, tokenSessionId);
    };

    const canConnect = selectedPersonal || selectedOrgs.length > 0;

    return (
        <>
            <div className="modal-overlay" onClick={() => onOpenChange(false)} />
            <div className="modal-container">
                <div className="modal-header">
                    <h2>Select Accounts to Connect</h2>
                    <button className="modal-close" onClick={() => onOpenChange(false)}>✕</button>
                </div>

                <div className="modal-content">
                    {/* Personal Account */}
                    <div className={`account-option ${isPersonalConnected ? 'disabled' : ''}`}>
                        <input
                            type="checkbox"
                            id="personal-account"
                            checked={selectedPersonal || isPersonalConnected}
                            onChange={(e) => setSelectedPersonal(e.target.checked)}
                            disabled={isPersonalConnected}
                        />
                        <label htmlFor="personal-account">
                            <div className="account-details">
                                <div className="account-icon personal">👤</div>
                                <div>
                                    <div className="account-title">{profile.name}</div>
                                    <div className="account-subtitle">Personal Profile</div>
                                    {profile.email && <div className="account-email">{profile.email}</div>}
                                </div>
                            </div>
                            {isPersonalConnected && <span className="connected-label">Already Connected</span>}
                        </label>
                    </div>

                    {/* Organizations */}
                    {organizations && organizations.length > 0 && (
                        <>
                            <div className="section-divider">
                                <span>Organizations</span>
                            </div>
                            {organizations.map((org) => {
                                const connected = isOrgConnected(org.urn);
                                const selected = selectedOrgs.find(o => o.urn === org.urn);

                                return (
                                    <div key={org.urn} className={`account-option ${connected ? 'disabled' : ''}`}>
                                        <input
                                            type="checkbox"
                                            id={`org-${org.id}`}
                                            checked={selected || connected}
                                            onChange={() => handleOrgToggle(org)}
                                            disabled={connected}
                                        />
                                        <label htmlFor={`org-${org.id}`}>
                                            <div className="account-details">
                                                <div className="account-icon organization">🏢</div>
                                                <div>
                                                    <div className="account-title">{org.name}</div>
                                                    <div className="account-subtitle">Organization</div>
                                                    {org.vanityName && (
                                                        <div className="account-email">linkedin.com/company/{org.vanityName}</div>
                                                    )}
                                                </div>
                                            </div>
                                            {connected && <span className="connected-label">Already Connected</span>}
                                        </label>
                                    </div>
                                );
                            })}
                        </>
                    )}
                </div>

                <div className="modal-footer">
                    <button
                        className="button secondary"
                        onClick={() => onOpenChange(false)}
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    <button
                        className="button primary"
                        onClick={handleConnect}
                        disabled={!canConnect || isLoading}
                    >
                        {isLoading ? 'Connecting...' : `Connect ${(selectedPersonal ? 1 : 0) + selectedOrgs.length} Account${(selectedPersonal ? 1 : 0) + selectedOrgs.length !== 1 ? 's' : ''}`}
                    </button>
                </div>
            </div>
        </>
    );
};

export default AccountSelectionModal;
