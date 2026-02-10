import React, { useState } from 'react';
import './AccountSelectionModal.css';

const AccountSelectionModal = ({
    open,
    onOpenChange,
    platform = 'linkedin',
    profile,
    organizations,
    adAccounts,
    tokenSessionId,
    connectedAccounts,
    onConnect,
    isLoading
}) => {
    const [selectedPersonal, setSelectedPersonal] = useState(false);
    const [selectedItems, setSelectedItems] = useState([]);

    if (!open) return null;

    const isPersonalConnected = connectedAccounts.some(
        acc => acc.platform === platform && acc.type === 'personal' && acc.accountId === (profile.urn || profile.id)
    );

    const isItemConnected = (itemId) => {
        const accountType = platform === 'linkedin' ? 'organization' : 'ad_account';
        return connectedAccounts.some(
            acc => acc.platform === platform && acc.type === accountType && acc.accountId === itemId
        );
    };

    const handleItemToggle = (item) => {
        const itemId = item.urn || item.id;
        if (isItemConnected(itemId)) return;

        setSelectedItems(prev => {
            const exists = prev.find(i => (i.urn || i.id) === itemId);
            if (exists) {
                return prev.filter(i => (i.urn || i.id) !== itemId);
            } else {
                return [...prev, item];
            }
        });
    };

    const handleConnect = () => {
        onConnect(platform, selectedPersonal, selectedItems, profile, tokenSessionId);
    };

    const canConnect = selectedPersonal || selectedItems.length > 0;

    const items = platform === 'linkedin' ? organizations : adAccounts;
    const itemsLabel = platform === 'linkedin' ? 'Organizations' : 'Ad Accounts';
    const itemIcon = platform === 'linkedin' ? '🏢' : '📊';

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

                    {/* Items (Organizations or Ad Accounts) */}
                    {items && items.length > 0 && (
                        <>
                            <div className="section-divider">
                                <span>{itemsLabel}</span>
                            </div>
                            {items.map((item) => {
                                const itemId = item.urn || item.id;
                                const connected = isItemConnected(itemId);
                                const selected = selectedItems.find(i => (i.urn || i.id) === itemId);

                                return (
                                    <div key={itemId} className={`account-option ${connected ? 'disabled' : ''}`}>
                                        <input
                                            type="checkbox"
                                            id={`item-${itemId}`}
                                            checked={selected || connected}
                                            onChange={() => handleItemToggle(item)}
                                            disabled={connected}
                                        />
                                        <label htmlFor={`item-${itemId}`}>
                                            <div className="account-details">
                                                <div className="account-icon organization">{itemIcon}</div>
                                                <div>
                                                    <div className="account-title">{item.name}</div>
                                                    <div className="account-subtitle">{platform === 'linkedin' ? 'Organization' : 'Ad Account'}</div>
                                                    {item.vanityName && (
                                                        <div className="account-email">linkedin.com/company/{item.vanityName}</div>
                                                    )}
                                                    {item.currency && (
                                                        <div className="account-email">Currency: {item.currency}</div>
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
                        {isLoading ? 'Connecting...' : `Connect ${(selectedPersonal ? 1 : 0) + selectedItems.length} Account${(selectedPersonal ? 1 : 0) + selectedItems.length !== 1 ? 's' : ''}`}
                    </button>
                </div>
            </div>
        </>
    );
};

export default AccountSelectionModal;
