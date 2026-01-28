import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import UserProfileDropdown from './components/UserProfileDropdown';
import Profile from './pages/Profile';
import LinkedInOAuthCallback from './pages/LinkedInOAuthCallback';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <header className="App-header">
            <div className="header-content">
              <div className="logo-section">
                <h1>AI Agents</h1>
              </div>
              <div className="header-actions">
                <UserProfileDropdown />
              </div>
            </div>
          </header>

          <main className="App-main">
            <Routes>
              <Route path="/" element={<Navigate to="/profile" replace />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/oauth/linkedin/callback" element={<LinkedInOAuthCallback />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

