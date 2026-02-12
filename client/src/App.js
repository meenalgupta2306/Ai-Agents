import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import UserProfileDropdown from './components/UserProfileDropdown';
import Chat from './pages/Chat';
import Profile from './pages/Profile';
import OAuthCallback from './pages/LinkedInOAuthCallback';
import VoiceSetup from './pages/VoiceSetup';
import Solutions from './pages/Solutions';
import VoiceCloningDemo from './pages/VoiceCloningDemo';
import SpeakingAvatar from './pages/SpeakingAvatar';
import DndTest from './pages/DndTest';
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
              <nav className="header-nav">
                <Link to="/solutions" className="nav-link">Solutions</Link>
                <Link to="/dnd-test" className="nav-link">DnD Test</Link>
              </nav>
              <div className="header-actions">
                <UserProfileDropdown />
              </div>
            </div>
          </header>

          <main className="App-main">
            <Routes>
              <Route path="/" element={<Chat />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/voice-setup" element={<VoiceSetup />} />
              <Route path="/solutions" element={<Solutions />} />
              <Route path="/voice-cloning-demo" element={<VoiceCloningDemo />} />
              <Route path="/speaking-avatar" element={<SpeakingAvatar />} />
              <Route path="/dnd-test" element={<DndTest />} />
              <Route path="/oauth/linkedin/callback" element={<OAuthCallback />} />
              <Route path="/oauth/meta/callback" element={<OAuthCallback />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

