import React, { useEffect, useRef, Component } from 'react';
import type { ErrorInfo } from 'react';
import ReactMarkdown from 'react-markdown';
import { FiUser, FiCpu, FiDatabase, FiDownload, FiChevronDown, FiChevronRight, FiAlertTriangle } from 'react-icons/fi';
import PlotlyVisualizer from './PlotlyVisualizer';
import { exportToCSV } from '../../utils/export';
import type { Message } from '../../App';

class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Visualizer Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-red-500/30 bg-red-500/10 rounded-lg text-red-500 flex items-center gap-2">
          <FiAlertTriangle />
          <div className="text-xs font-mono">
            Visualization Error: {this.state.error?.message}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

interface ChatInterfaceProps {
  messages: Message[];
  theme: 'light' | 'dark' | 'drilling-slate' | 'system';
}

const ThinkingProcess: React.FC<{ thoughts: string[] }> = ({ thoughts }) => {
  const [isOpen, setIsOpen] = React.useState(false);

  if (!thoughts || thoughts.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-[var(--accent-primary)] hover:text-[var(--text-primary)] transition-colors select-none group cursor-pointer"
      >
        <div className="w-5 h-5 flex items-center justify-center">
          {/* Simple Sparkle Icon */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-[var(--accent-primary)]">
            <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" fill="currentColor" />
          </svg>
        </div>
        <span>Show thinking</span>
        <FiChevronDown className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="mt-3 ml-2 pl-4 border-l-2 border-[var(--border-subtle)] space-y-3 animate-fade-in py-2">
          {thoughts.map((thought, idx) => (
            <div key={idx} className="text-sm text-[var(--text-secondary)] font-mono leading-relaxed bg-[var(--bg-tertiary)]/50 p-3 rounded-md">
              <span className="opacity-50 mr-2 font-bold text-xs uppercase">Step {idx + 1}</span>
              <div className="mt-1">{thought}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, theme }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center opacity-50">
        <div className="w-16 h-16 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mb-4 text-[var(--accent-primary)]">
          <FiCpu size={32} />
        </div>
        <h2 className="text-xl font-heading font-medium text-[var(--text-primary)] mb-2">How can I help you today?</h2>
        <p className="text-[var(--text-secondary)] max-w-md">
          Ask about patient demographics, disease prevalence, or analytics. I can visualize data and write SQL.
        </p>
      </div>
    );
  }

  console.log("ChatInterface render", { msgId: messages.length, lastThoughts: messages[messages.length - 1]?.thoughts });

  return (
    <div className="@container flex-1 overflow-y-auto py-6 scroll-smooth custom-scrollbar">
      <div className="max-w-4xl mx-auto px-4 space-y-8 pb-12">
        {messages.map((msg) => (
          <div key={msg.id} id={msg.id} className="animate-fade-in group">{/* User Message */}
            {/* User Message */}
            {msg.sender === 'user' ? (
              <div className="flex justify-end mb-6">
                <div className="bg-[var(--bg-secondary)] px-5 py-3 rounded-2xl rounded-tr-sm text-[var(--text-primary)] @sm:max-w-[80%] max-w-full shadow-sm">
                  {msg.text}
                </div>
              </div>
            ) : (
              /* Bot Message */
              <div className="flex gap-4 items-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[var(--accent-primary)] to-purple-400 flex items-center justify-center text-white shrink-0 shadow-sm">
                  <FiCpu size={16} />
                </div>

                <div className="flex-1 min-w-0 space-y-4">
                  {/* Sender Name */}
                  <div className="text-sm font-bold text-[var(--text-primary)] h-8 flex items-center">
                    Mediquery AI
                  </div>

                  {/* Thinking Process */}
                  {msg.thoughts && <ThinkingProcess thoughts={msg.thoughts} />}

                  {/* Text Content */}
                  <div className="prose prose-sm max-w-none text-[var(--text-secondary)] dark:prose-invert">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>

                  {/* Visualizations & Data */}
                  {msg.data && (
                    <div className="mt-4 border border-[var(--border-subtle)] rounded-xl overflow-hidden bg-[var(--bg-primary)] shadow-sm">
                      <div className="bg-[var(--bg-secondary)] px-4 py-2 border-b border-[var(--border-subtle)] flex justify-between items-center">
                        <span className="text-xs font-bold text-[var(--text-secondary)] uppercase">Data Visualization</span>
                        <button
                          onClick={() => {
                            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                            exportToCSV(msg.data.data, msg.data.columns, `mediquery-${timestamp}`);
                          }}
                          className="flex items-center gap-2 text-xs text-[var(--accent-primary)] hover:underline"
                        >
                          <FiDownload /> Export CSV
                        </button>
                      </div>
                      <div className="p-4 overflow-x-auto min-h-[300px] flex items-center justify-center bg-[var(--bg-primary)]">
                        {/* Dynamic Import or direct usage if path correct */}
                        <ErrorBoundary>
                          <PlotlyVisualizer
                            data={msg.data}
                            visualizationType={msg.visualization_type || 'table'}
                            theme={theme}
                          />
                        </ErrorBoundary>
                      </div>
                    </div>
                  )}

                  {/* SQL Trace */}
                  {msg.sql && (
                    <details className="mt-2">
                      <summary className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer flex items-center gap-1 select-none w-fit">
                        <FiDatabase size={12} />
                        View SQL Query
                      </summary>
                      <div className="mt-2 p-3 bg-[var(--bg-secondary)] rounded-md border border-[var(--border-subtle)] overflow-x-auto">
                        <code className="text-xs font-mono text-[var(--accent-primary)] whitespace-pre-wrap break-all">
                          {msg.sql}
                        </code>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default ChatInterface;

// Note: I need to verify the path of PlotlyVisualizer. 
// Assuming it is one level up from valid components structure.
