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
    <div className="flex flex-col items-center justify-center w-full h-full bg-black z-50 absolute top-0 left-0 bg-[url('/grid-bg.png')] bg-cover">
      <div className="absolute inset-0 bg-[#000000]/80"></div>

      {/* Login Card */}
      <div className="relative w-[400px] p-8 border border-[#00F0FF]/30 bg-[#020408]/90 backdrop-blur-md rounded-lg shadow-[0_0_50px_rgba(0,240,255,0.15)] clip-corner">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl text-white font-bold tracking-widest mb-1">
            MEDIQUERY<span className="text-[#00F0FF]">.AI</span>
          </h1>
          <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-[#00F0FF]/50 to-transparent my-2"></div>
          <h2 className="text-sm text-[#00F0FF] font-mono tracking-[0.3em]">
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
            <label className="block text-[#00F0FF]/60 text-[10px] font-mono mb-1 tracking-wider group-focus-within:text-[#00F0FF] transition-colors">USER_ID</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[#00F0FF]/5 border border-[#00F0FF]/20 text-[#00F0FF] p-3 focus:outline-none focus:border-[#00F0FF] focus:bg-[#00F0FF]/10 transition-all font-mono"
              placeholder="ENTER USERNAME"
              required
            />
          </div>
          <div className="group">
            <label className="block text-[#00F0FF]/60 text-[10px] font-mono mb-1 tracking-wider group-focus-within:text-[#00F0FF] transition-colors">ACCESS_CODE</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#00F0FF]/5 border border-[#00F0FF]/20 text-[#00F0FF] p-3 focus:outline-none focus:border-[#00F0FF] focus:bg-[#00F0FF]/10 transition-all font-mono"
              placeholder="ENTER PASSWORD"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full bg-[#00F0FF] text-black font-bold py-3 px-4 uppercase font-display tracking-widest hover:bg-white hover:shadow-[0_0_30px_rgba(0,240,255,0.6)] transition-all disabled:opacity-50 disabled:cursor-not-allowed clip-button text-lg"
          >
            {loading ? 'PROCESSING...' : (isRegistering ? 'ESTABLISH LINK' : 'AUTHENTICATE')}
          </button>
        </form>

        <div className="mt-8 flex flex-col items-center gap-4 w-full">
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-[#00F0FF] text-sm hover:text-white transition-colors font-mono tracking-wider border-b border-[#00F0FF]/30 pb-1"
          >
            {isRegistering ? '<< RETURN TO LOGIN' : '>> CREATE NEW IDENTITY'}
          </button>

          <div className="w-full flex items-center gap-4 my-2">
            <div className="h-[1px] flex-1 bg-[#00F0FF]/20"></div>
            <div className="text-[#00F0FF]/40 text-[10px] font-mono">OR</div>
            <div className="h-[1px] flex-1 bg-[#00F0FF]/20"></div>
          </div>

          <button
            type="button"
            onClick={handleGuestLogin}
            disabled={loading}
            className="w-full bg-transparent border border-[#00F0FF] text-[#00F0FF] py-3 px-6 hover:bg-[#00F0FF]/10 hover:shadow-[0_0_20px_rgba(0,240,255,0.2)] transition-all font-display tracking-widest clip-button text-sm"
          >
            INITIATE GUEST PROTOCOL
          </button>
        </div>

        {/* Footer / SSO Placeholders */}
        <div className="mt-6 text-center">
          <div className="text-[#00F0FF]/20 text-[10px] mb-2 font-mono tracking-widest">- SECURE CONNECTION -</div>
          <div className="flex justify-center gap-3 opacity-50">
            {/* Icons placeholders or text */}
            <span className="text-[10px] text-[#00F0FF]/40 border border-[#00F0FF]/20 px-2 py-1 rounded">ENTRA</span>
            <span className="text-[10px] text-[#00F0FF]/40 border border-[#00F0FF]/20 px-2 py-1 rounded">AWS</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
