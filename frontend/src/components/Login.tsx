import React, { useState } from 'react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

interface LoginProps {
  onLogin: (token: string, username: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegistering) {
        await axios.post(getApiUrl('/auth/register'), {
          username,
          password
        });
        // Auto login after register
        const res = await axios.post(getApiUrl('/auth/token'),
          new URLSearchParams({
            'username': username,
            'password': password,
            'grant_type': 'password'
          }),
          { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        );
        onLogin(res.data.access_token, username);
      } else {
        const res = await axios.post(getApiUrl('/auth/token'),
          new URLSearchParams({
            'username': username,
            'password': password,
            'grant_type': 'password'
          }),
          { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        );
        onLogin(res.data.access_token, username);
      }
    } catch (err: any) {
      if (err.response) {
        setError(err.response.data.detail || "Authentication failed");
      } else {
        setError("Network error. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const res = await axios.post(getApiUrl('/auth/guest'));
      onLogin(res.data.access_token, "Guest");
    } catch (e: any) {
      setError("Guest Login Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="@container flex flex-col items-center justify-center w-full h-full bg-[var(--bg-primary)] z-50 absolute top-0 left-0">
      <div className="absolute inset-0 bg-[var(--bg-primary)]/80 backdrop-blur-sm"></div>

      {/* Login Card - Responsive with Container Queries */}
      <div className="relative @sm:w-[400px] w-[90%] p-6 @sm:p-8 border border-[var(--accent-primary)]/30 bg-[var(--bg-secondary)]/90 backdrop-blur-md rounded-lg shadow-xl">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl @sm:text-3xl text-[var(--text-primary)] font-bold tracking-widest mb-1 font-heading">
            MEDIQUERY<span className="text-[var(--accent-primary)]">.AI</span>
          </h1>
          <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-[var(--accent-primary)]/50 to-transparent my-2"></div>
          <h2 className="text-xs @sm:text-sm text-[var(--accent-primary)] font-mono tracking-[0.3em]">
            {isRegistering ? 'INITIALIZE IDENTITY' : 'IDENTITY VERIFICATION'}
          </h2>
        </div>

        {error && (
          <div className="mb-6 p-2 bg-red-900/20 border border-red-500/50 text-red-200 text-xs font-mono text-center">
            [ ALERT: {error} ]
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="group">
            <label className="block text-[var(--accent-primary)]/60 text-[10px] font-mono mb-1 tracking-wider group-focus-within:text-[var(--accent-primary)] transition-colors">USER_ID</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-primary)] p-3 focus:outline-none focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all font-mono rounded"
              placeholder="ENTER USERNAME"
              required
            />
          </div>
          <div className="group">
            <label className="block text-[var(--accent-primary)]/60 text-[10px] font-mono mb-1 tracking-wider group-focus-within:text-[var(--accent-primary)] transition-colors">ACCESS_CODE</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-primary)] p-3 focus:outline-none focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all font-mono rounded"
              placeholder="ENTER PASSWORD"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full bg-[var(--accent-primary)] text-white font-bold py-3 px-4 uppercase font-heading tracking-widest hover:bg-[var(--accent-hover)] hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed rounded text-base @sm:text-lg cursor-pointer"
          >
            {loading ? 'PROCESSING...' : (isRegistering ? 'ESTABLISH LINK' : 'AUTHENTICATE')}
          </button>
        </form>

        <div className="mt-8 flex flex-col items-center gap-4 w-full">
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-[var(--accent-primary)] text-sm hover:text-[var(--accent-hover)] transition-colors font-mono tracking-wider border-b border-[var(--accent-primary)]/30 pb-1 cursor-pointer"
          >
            {isRegistering ? '<< RETURN TO LOGIN' : '>> CREATE NEW IDENTITY'}
          </button>

          <div className="w-full flex items-center gap-4 my-2">
            <div className="h-[1px] flex-1 bg-[var(--border-subtle)]"></div>
            <div className="text-[var(--text-tertiary)] text-[10px] font-mono">OR</div>
            <div className="h-[1px] flex-1 bg-[var(--border-subtle)]"></div>
          </div>

          <button
            type="button"
            onClick={handleGuestLogin}
            disabled={loading}
            className="w-full bg-transparent border border-[var(--accent-primary)] text-[var(--accent-primary)] py-3 px-6 hover:bg-[var(--accent-primary)]/10 hover:shadow-md transition-all font-heading tracking-widest rounded text-sm cursor-pointer"
          >
            INITIATE GUEST PROTOCOL
          </button>
        </div>

        {/* Footer / SSO Placeholders */}
        <div className="mt-6 text-center">
          <div className="text-[var(--text-tertiary)] text-[10px] mb-2 font-mono tracking-widest">- SECURE CONNECTION -</div>
          <div className="flex justify-center gap-3 opacity-50">
            <span className="text-[10px] text-[var(--text-tertiary)] border border-[var(--border-subtle)] px-2 py-1 rounded">ENTRA</span>
            <span className="text-[10px] text-[var(--text-tertiary)] border border-[var(--border-subtle)] px-2 py-1 rounded">AWS</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
