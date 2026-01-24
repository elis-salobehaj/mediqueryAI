import React, { useState, type KeyboardEvent } from 'react';
import { FiSend, FiCpu, FiMoreHorizontal } from 'react-icons/fi';

interface InputBarProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  fastMode: boolean;
  setFastMode: (enabled: boolean) => void;
  multiAgent: boolean;
  setMultiAgent: (enabled: boolean) => void;
  models: Array<{ id: string, name: string }>;
  selectedModel: string;
  setSelectedModel: (id: string) => void;
}

const InputBar: React.FC<InputBarProps> = ({
  onSend,
  isLoading,
  fastMode,
  setFastMode,
  multiAgent,
  setMultiAgent,
  models,
  selectedModel,
  setSelectedModel
}) => {
  const [input, setInput] = useState('');
  const [showOptions, setShowOptions] = useState(true);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        onSend(input);
        setInput('');
      }
    }
  };

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6">
      <div className="relative group">
        <div className={`
          gemini-input flex flex-col transition-all duration-300
          ${isLoading ? 'opacity-80' : 'opacity-100'}
          bg-[var(--bg-input)]
        `}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Mediquery..."
            className="w-full bg-transparent border-none outline-none resize-none min-h-[50px] max-h-[200px] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] py-2"
            rows={1}
            style={{ height: 'auto', minHeight: '24px' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto'; // Reset height
              target.style.height = `${Math.min(target.scrollHeight, 200)}px`; // Set new height
            }}
          />

          <div className="flex items-center justify-between mt-2 pt-2 border-t border-[var(--border-subtle)]/30">
            {/* Left: Toggles & Options */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowOptions(!showOptions)}
                className={`btn-icon p-2 rounded-full hover:bg-[var(--bg-tertiary)] ${showOptions ? 'text-[var(--accent-primary)] bg-[var(--bg-tertiary)]' : ''}`}
                title="Model Settings"
              >
                <FiMoreHorizontal size={18} />
              </button>

              {showOptions && (
                <div className="flex items-center gap-2 animate-fade-in bg-[var(--bg-primary)] px-2 py-1 rounded-full border border-[var(--border-subtle)] shadow-sm">
                  {/* Model Select */}
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="text-xs bg-transparent border-none outline-none text-[var(--text-secondary)] font-medium cursor-pointer max-w-[120px] truncate"
                  >
                    {models.map(m => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>

                  <div className="w-px h-3 bg-[var(--border-subtle)] mx-1"></div>

                  {/* Fast Mode Toggle */}
                  <button
                    onClick={() => setFastMode(!fastMode)}
                    className={`text-xs px-2 py-0.5 rounded-full transition-colors font-medium border ${fastMode ? 'bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] border-[var(--accent-primary)]/20' : 'text-[var(--text-tertiary)] border-transparent hover:bg-[var(--bg-tertiary)]'}`}
                    title="Fast Mode uses simpler models for speed"
                  >
                    ⚡ Fast
                  </button>

                  {/* Multi-Agent Toggle */}
                  <button
                    onClick={() => setMultiAgent(!multiAgent)}
                    className={`text-xs px-2 py-0.5 rounded-full transition-colors font-medium border ${multiAgent ? 'bg-purple-500/10 text-purple-600 border-purple-500/20' : 'text-[var(--text-tertiary)] border-transparent hover:bg-[var(--bg-tertiary)]'}`}
                    title="Multi-Agent Mode uses specialized agents"
                  >
                    🤖 Agents
                  </button>
                </div>
              )}
            </div>

            {/* Right: Send Button */}
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={`
                p-2 rounded-full transition-all duration-200
                ${input.trim() && !isLoading
                  ? 'bg-[var(--accent-primary)] text-white shadow-md hover:bg-[var(--accent-hover)] transform hover:scale-105'
                  : 'bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] cursor-not-allowed'}
              `}
            >
              {isLoading ? (
                <FiCpu className="animate-spin" size={18} />
              ) : (
                <FiSend size={18} className={input.trim() ? 'ml-0.5' : ''} />
              )}
            </button>
          </div>
        </div>
      </div>
      <div className="text-center mt-2">
        <p className="text-[10px] text-[var(--text-tertiary)]">
          Mediquery can make mistakes. Use with professional verification.
        </p>
      </div>
    </div>
  );
};

export default InputBar;
