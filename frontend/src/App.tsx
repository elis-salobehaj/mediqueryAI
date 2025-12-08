import { useState, useEffect } from 'react';
import axios from 'axios';
import ChatBox from './components/ChatBox';
import { getApiUrl } from './config/api';

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  data?: any;
  sql?: string;
  visualization_type?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(getApiUrl('/history'));
        if (res.data && res.data.length > 0) {
          const hist = res.data.map((msg: any) => ({
            id: msg.id,
            sender: msg.role === 'user' ? 'user' : 'bot',
            text: msg.text,
            data: msg.meta?.data,
            sql: msg.meta?.sql,
            visualization_type: msg.meta?.visualization_type
          }));
          setMessages(hist);
        } else {
          setMessages([{ id: '1', sender: 'bot', text: 'SYSTEM INITIALIZED.\n\nReady to process healthcare queries. Awaiting input...' }]);
        }
      } catch (err) {
        console.error("History load failed", err);
        setMessages([{ id: '1', sender: 'bot', text: 'SYSTEM INITIALIZED.\n\nReady to process healthcare queries. Awaiting input...' }]);
      }
    };
    fetchHistory();
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden flex flex-col">
      {/* Scanline Overlay */}
      <div className="scanline"></div>

      {/* Responsive Background Logo */}
      <div className="bg-logo-fixed"></div>

      {/* Ambient Glow */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#00F0FF] opacity-[0.05] blur-[100px] pointer-events-none rounded-full"></div>

      {/* Top Status Bar (HUD Header) */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-[rgba(0,240,255,0.2)] bg-[rgba(2,4,8,0.8)] backdrop-blur-sm z-20 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex flex-col">
            <h1 className="text-xl leading-none hud-title tracking-widest text-white">MEDIQUERY<span className="text-[#00F0FF]">.AI</span></h1>
            <span className="text-[10px] text-[#00F0FF]/60 tracking-[0.2em]">OPERATIONAL</span>
          </div>
        </div>

        <div className="flex items-center gap-6 text-[10px] font-mono text-[#00F0FF]/50 tracking-widest hidden md:flex">
          <div>CPU: <span className="text-[#00F0FF]">NORMAL</span></div>
          <div>NET: <span className="text-[#00F0FF]">SECURE</span></div>
          <div>DB:  <span className="text-[#00F0FF]">CONNECTED</span></div>
          <div>[v2.5.0]</div>
        </div>
      </header>

      {/* Main Viewport */}
      <main className="flex-1 relative overflow-hidden flex flex-col w-full">
        {/* Central Chat Interface */}
        <ChatBox messages={messages} setMessages={setMessages} />
      </main>

    </div>
  );
}

export default App;
