import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { FaRobot, FaUser, FaMicrochip, FaDatabase, FaChevronUp } from 'react-icons/fa';
import { getApiUrl } from '../config/api';

import type { Message } from '../App';
import clsx from 'clsx';
import PlotlyVisualizer from './PlotlyVisualizer';

interface ChatBoxProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

const MODELS = [
  { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder (7B)' },
  { id: 'sqlcoder:7b', name: 'Defog SQLCoder (7B)' },
  { id: 'gemma-3-27b-it', name: 'GEMMA 3 27B (CLOUD)' },
];

/* Custom Futuristic Dropdown Component */
const CustomSelect = ({ value, onChange, options }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const selected = options.find((o: any) => o.id === value) || options[0];
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="hud-select-wrapper" ref={ref} onClick={() => setIsOpen(!isOpen)}>
      <div className="hud-select-trigger">
        <span className="text-[#00F0FF] opacity-80">SYS.MODEL //</span>
        <span className="font-bold">{selected.name}</span>
        <FaChevronUp className={`text-[10px] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>
      {isOpen && (
        <div className="hud-select-options">
          {options.map((opt: any) => (
            <div
              key={opt.id}
              className={`hud-option ${opt.id === value ? 'selected' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log("Selecting model:", opt.id); // Debug Log
                onChange(opt.id);
                setIsOpen(false);
              }}
            >
              {opt.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ChatBox: React.FC<ChatBoxProps> = ({ messages, setMessages }) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<Array<{ id: string, name: string }>>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Fetch models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await axios.get(getApiUrl('/config/models'));
        const availableModels = response.data;
        setModels(availableModels);
        if (availableModels.length > 0) {
          setSelectedModel(availableModels[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch models", error);
        // Fallback
        setModels(MODELS);
        setSelectedModel(MODELS[0].id);
      }
    };
    fetchModels();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(getApiUrl('/query'), {
        question: userMsg.text,
        model_id: selectedModel
      });

      const resData = response.data;
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: resData.insight || "DATA RETRIEVED.",
        data: resData.data,
        sql: resData.sql,
        visualization_type: resData.visualization_type,
        thoughts: resData.meta?.thoughts
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (error: any) {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: `Error: ${error.response?.data?.detail || error.message}. SYSTEM FAILURE.`
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="flex flex-col h-0 flex-1 w-full max-w-6xl mx-auto p-4 md:p-6 gap-6 z-10 relative overflow-hidden">
      {/* HUD Message Stream */}
      <div className="flex-1 min-h-0 space-y-6 pr-2 scroll-smooth relative pb-10 z-10 overflow-y-auto custom-scrollbar">
        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex gap-4 group", msg.sender === 'user' ? "flex-row-reverse" : "flex-row")}>

            {/* Avatar Hexagon */}
            <div className={clsx(
              "w-12 h-12 flex items-center justify-center hexagon-clip border-2 border-[#00F0FF] shadow-[0_0_15px_rgba(0,240,255,0.4)] bg-black z-10 shrink-0",
              msg.sender === 'bot' ? "text-[#00F0FF]" : "text-white bg-[#00F0FF]/20"
            )}>
              {msg.sender === 'bot' ? <FaRobot className="text-xl" /> : <FaUser className="text-lg" />}
            </div>

            <div className={clsx(
              "max-w-[85%] relative p-6 border transition-all duration-300 backdrop-blur-md",
              msg.sender === 'user'
                ? "bg-[#00F0FF]/5 border-[#00F0FF]/30 text-white rounded-bl-2xl rounded-tr-2xl shadow-[0_0_20px_rgba(0,240,255,0.05)]"
                : "bg-[#020408]/80 border-[#00F0FF]/30 text-[#E0F7FA] rounded-br-2xl rounded-tl-2xl shadow-[0_0_20px_rgba(0,240,255,0.05)]"
            )}>
              {/* Tiny deco bits */}
              {/* Tiny deco bits - Adjusted to sit on SQUARE corners */}
              <div className={clsx(
                "absolute w-3 h-3 border-[#00F0FF]",
                msg.sender === 'user'
                  ? "top-0 left-0 border-t-2 border-l-2"  // User: Top-Left (Square)
                  : "top-0 right-0 border-t-2 border-r-2" // Bot: Top-Right (Square)
              )}></div>
              <div className={clsx(
                "absolute w-3 h-3 border-[#00F0FF]",
                msg.sender === 'user'
                  ? "bottom-0 right-0 border-b-2 border-r-2" // User: Bottom-Right (Square)
                  : "bottom-0 left-0 border-b-2 border-l-2"  // Bot: Bottom-Left (Square)
              )}></div>

              <div className="font-mono text-[10px] opacity-70 mb-2 flex items-center gap-2">
                {msg.sender === 'user' ? '>> USER_COMMAND' : '>> SYS_RESPONSE'}
                {msg.sender === 'bot' && <span className="text-[#00F0FF] animate-pulse">● LIVE</span>}
              </div>

              <div className="leading-relaxed text-sm font-light tracking-wide">

                {/* Thinking Process UI */}
                {msg.sender === 'bot' && msg.thoughts && msg.thoughts.length > 0 && (
                  <details className="mb-4 border border-[#00F0FF]/30 rounded-md bg-[#001015]/90 overflow-hidden group/thoughts open:bg-[#001520]">
                    <summary className="cursor-pointer p-2 text-xs font-mono text-[#00F0FF]/70 hover:text-[#00F0FF] flex items-center gap-2 select-none">
                      <FaMicrochip className="text-[10px]" />
                      <span>SYSTEM_THOUGHT_PROCESS</span>
                      <span className="opacity-50 text-[10px] ml-auto group-open/thoughts:hidden">[{msg.thoughts.length} STEPS]</span>
                    </summary>
                    <div className="p-3 pt-0 text-[10px] font-mono text-green-400/80 space-y-1 max-h-40 overflow-y-auto">
                      {msg.thoughts.map((thought, idx) => (
                        <div key={idx} className="flex gap-2">
                          <span className="opacity-50">[{idx + 1}]</span>
                          <span>{thought}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>

              {/* Visuals */}
              {msg.sender === 'bot' && msg.data && (
                <PlotlyVisualizer
                  data={msg.data}
                  visualizationType={msg.visualization_type || 'table'}
                />
              )}

              {/* SQL Log */}
              {msg.sender === 'bot' && msg.sql && (
                <div className="mt-4 pt-3 border-t border-[#00F0FF]/20 text-[10px] font-mono text-[#00F0FF]/70">
                  <div className="flex items-center gap-1 mb-1"><FaDatabase /> SQL_EXECUTION_TRACE:</div>
                  <code className="block bg-black/50 p-2 rounded border border-[#00F0FF]/20 text-green-400 break-words">{msg.sql}</code>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-center my-4">
            <div className="flex items-center gap-3 text-[#00F0FF] font-mono text-sm px-4 py-2 bg-[#00F0FF]/5 border border-[#00F0FF]/30 rounded-full animate-pulse">
              <FaMicrochip className="animate-spin" />
              <span>PROCESSING DATA STREAM...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* HUGE CENTERED INPUT MODULE (Integrated Phase 2) */}
      <div className="relative w-full max-w-4xl mx-auto mb-4 animate-in slide-in-from-bottom-5 duration-700 z-20">

        <div className="flex justify-between items-end mb-2 px-1">
          <div className="text-[#00F0FF] font-display text-xs tracking-[0.2em] opacity-80 blink">
            _READY_FOR_INPUT
          </div>

          {/* Custom Futuristic Selector */}
          <CustomSelect
            value={selectedModel}
            onChange={setSelectedModel}
            options={models.length > 0 ? models : MODELS}
          />
        </div>

        <div className="hud-input-group">
          <textarea
            className="hud-input-field resize-none h-24"
            placeholder="ENTER INSTRUCTION (e.g., 'Analyze patient demographics')..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
            autoFocus
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="hud-btn-send h-24"
          >
            TRANSMIT
          </button>
        </div>
      </div>

    </div>
  );
};

export default ChatBox;
