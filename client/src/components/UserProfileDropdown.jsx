import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './UserProfileDropdown.css';

const UserProfileDropdown = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = React.useState(false);

    if (!user) return null;

    const getInitials = (email) => {
        if (!email) return 'U';
        const parts = email.split('@')[0].split(/[._-]/);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return parts[0].substring(0, 2).toUpperCase();
    };

    const handleProfileClick = () => {
        navigate('/profile');
        setIsOpen(false);
    };

    const handleLogout = () => {
        logout();
        setIsOpen(false);
    };

    return (
        <div className="profile-dropdown">
            <button
                className="profile-button"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="avatar">
                    {getInitials(user.email)}
                </div>
            </button>

            {isOpen && (
                <>
                    <div className="dropdown-overlay" onClick={() => setIsOpen(false)} />
                    <div className="dropdown-menu">
                        <div className="dropdown-header">
                            <div className="user-info">
                                <p className="user-email">{user.email}</p>
                                <p className="user-role">User Account</p>
                            </div>
                        </div>
                        <div className="dropdown-divider" />
                        <button className="dropdown-item" onClick={handleProfileClick}>
                            <span className="icon">👤</span>
                            <span>Profile</span>
                        </button>
                        <div className="dropdown-divider" />
                        <button className="dropdown-item" onClick={handleLogout}>
                            <span className="icon">🚪</span>
                            <span>Log out</span>
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default UserProfileDropdown;
