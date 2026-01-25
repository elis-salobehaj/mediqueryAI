import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from './components/Layout/Layout';
import ChatInterface from './components/Chat/ChatInterface';
import InputBar from './components/Chat/InputBar';
import Login from './components/Login';
import { getApiUrl } from './config/api';

export interface Thread {
  id: string;
  title: string;
  updated_at: number;
  pinned: boolean;
}

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  data?: any;
  sql?: string;
  visualization_type?: string;
  thoughts?: string[];
}

const MODELS = [
  { id: 'global.anthropic.claude-haiku-4-5-20251001-v1:0', name: 'Claude Haiku 4.5 (Bedrock)' },
  { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder' },
  { id: 'sqlcoder:7b', name: 'Defog SQLCoder' },
  { id: 'gemma-3-27b-it', name: 'GEMMA 3 27B' },
];

function App() {
  // State
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [token, setToken] = useState<string | null>(localStorage.getItem('mediquery_token'));
  const [user, setUser] = useState<string | null>(localStorage.getItem('mediquery_user'));
  const [isLoading, setIsLoading] = useState(false);

  // Settings - Use backend defaults if localStorage is empty (first-time users)
  const [fastMode, setFastMode] = useState(() => {
    const stored = localStorage.getItem('fastMode');
    return stored !== null ? stored === 'true' : false; // Default: thinking mode ON (fast mode OFF)
  });
  const [multiAgent, setMultiAgent] = useState(() => {
    const stored = localStorage.getItem('multiAgent');
    return stored !== null ? stored === 'true' : true; // Default: multi-agent ON
  });
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id);

  // Persistence
  useEffect(() => localStorage.setItem('fastMode', String(fastMode)), [fastMode]);
  useEffect(() => localStorage.setItem('multiAgent', String(multiAgent)), [multiAgent]);

  // Theme State ... (Keep theme logic same)
  // Theme State
  const [theme, setTheme] = useState<'light' | 'dark' | 'drilling-slate' | 'system'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark' | 'drilling-slate' | 'system') || 'system';
  });

  // Apply Theme
  useEffect(() => {
    const root = window.document.documentElement;

    const applyTheme = (themeName: 'light' | 'dark' | 'drilling-slate' | 'system') => {
      let effectiveTheme: 'light' | 'dark' | 'drilling-slate' = themeName === 'system'
        ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        : themeName;

      document.documentElement.setAttribute('data-theme', effectiveTheme);
    };

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mediaQuery.matches ? 'dark' : 'light');

      const handleChange = (e: MediaQueryListEvent) => {
        applyTheme(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      applyTheme(theme);
    }

    localStorage.setItem('theme', theme);
  }, [theme]);

  // Auth Headers
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // API Utils
  const fetchThreads = async () => {
    if (!token) return;
    try {
      const res = await axios.get(getApiUrl('/threads'));
      setThreads(res.data.threads || []);
    } catch (err) {
      console.error("Failed to fetch threads", err);
    }
  };

  const fetchMessages = async (threadId: string) => {
    try {
      const res = await axios.get(getApiUrl(`/threads/${threadId}/messages`));
      const rawMessages = res.data.messages || [];
      const formattedMessages: Message[] = rawMessages.map((msg: any) => ({
        id: msg.id,
        sender: msg.role === 'user' ? 'user' : 'bot',
        text: msg.text,
        data: msg.meta?.data,
        sql: msg.meta?.sql,
        visualization_type: msg.meta?.visualization_type,
        thoughts: (msg.meta?.thoughts && msg.meta.thoughts.length > 0)
          ? msg.meta.thoughts
          : (msg.meta?.query_plan ? [msg.meta.query_plan] : [])
      }));
      setMessages(formattedMessages);
    } catch (err) {
      console.error("Failed to fetch messages", err);
    }
  };

  // Effects
  useEffect(() => {
    if (token) fetchThreads();
  }, [token]);

  useEffect(() => {
    if (currentThreadId) {
      fetchMessages(currentThreadId);
    } else {
      setMessages([]);
    }
  }, [currentThreadId]);

  // Handlers
  const handleLogin = (newToken: string, username: string) => {
    setToken(newToken);
    setUser(username);
    localStorage.setItem('mediquery_token', newToken);
    localStorage.setItem('mediquery_user', username);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('mediquery_token');
    localStorage.removeItem('mediquery_user');
    setMessages([]);
    setThreads([]);
    setCurrentThreadId(null);
  };

  const handleNewChat = () => {
    setCurrentThreadId(null);
    setMessages([]);
  };

  const handleSelectThread = (threadId: string) => {
    setCurrentThreadId(threadId);
  };

  const handleRenameThread = async (threadId: string, newTitle: string) => {
    try {
      await axios.patch(getApiUrl(`/threads/${threadId}`), { title: newTitle });
      fetchThreads();
    } catch (err) {
      console.error("Failed to rename thread", err);
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    try {
      await axios.delete(getApiUrl(`/threads/${threadId}`));
      if (currentThreadId === threadId) {
        handleNewChat();
      }
      fetchThreads();
    } catch (err) {
      console.error("Failed to delete thread", err);
    }
  };

  const handlePinThread = async (threadId: string, pinned: boolean) => {
    try {
      await axios.patch(getApiUrl(`/threads/${threadId}`), { pinned });
      fetchThreads();
    } catch (err) {
      console.error("Failed to pin thread", err);
    }
  };

  const handleShareThread = (threadId: string) => {
    // Mock share
    alert(`Shared thread ${threadId}`);
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Optimistic Update: User Message
    const tempId = Date.now().toString();
    const userMsg: Message = { id: tempId, sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    // Initial "Thinking" Bot Message
    const botId = (Date.now() + 1).toString();
    const initialThoughts = ["Analyzing request..."];
    const thinkingMsg: Message = {
      id: botId,
      sender: 'bot',
      text: "",
      thoughts: initialThoughts
    };
    setMessages(prev => [...prev, thinkingMsg]);

    // Simulated streaming of thoughts
    const thoughtSteps = [
      "Identifying relevant medical tables...",
      "Analyzing schema relationships...",
      "Constructing SQL query...",
      "Optimizing query performance...",
      "Validating against safety protocols...",
      "Executing database query...",
      "Formatting visualization..."
    ];

    let stepIndex = 0;
    const thoughtInterval = setInterval(() => {
      if (stepIndex < thoughtSteps.length) {
        setMessages(prev => prev.map(msg =>
          msg.id === botId
            ? { ...msg, thoughts: [...(msg.thoughts || []), thoughtSteps[stepIndex]] }
            : msg
        ));
        stepIndex++;
      }
    }, 1500);

    try {
      const response = await axios.post(getApiUrl('/query'), {
        question: text,
        thread_id: currentThreadId,
        model_id: selectedModel,
        fast_mode: fastMode,
        multi_agent: multiAgent
      });

      const resData = response.data;

      // Update current thread if changed
      if (resData.meta?.thread_id && resData.meta.thread_id !== currentThreadId) {
        setCurrentThreadId(resData.meta.thread_id);
        fetchThreads();
      }

      // Preserve existing thoughts if backend sends none, or merge them
      const existingThoughts = messages.find(m => m.id === botId)?.thoughts || [];
      const backendThoughts = resData.meta?.thoughts || [];

      // Use backend thoughts if available (full trace), otherwise keep simulated steps + completion
      const finalThoughts = backendThoughts.length > 0
        ? backendThoughts
        : [...existingThoughts, "Analysis complete.", "Rendering results..."];

      setMessages(prev => prev.map(msg =>
        msg.id === botId
          ? {
            ...msg,
            text: resData.insight || "Here is the data you requested.",
            data: resData.data,
            sql: resData.sql,
            visualization_type: resData.visualization_type,
            thoughts: finalThoughts
          }
          : msg
      ));
    } catch (error: any) {
      const errorText = `I encountered an error processing your request: ${error.response?.data?.detail || error.message}`;
      setMessages(prev => prev.map(msg =>
        msg.id === botId
          ? { ...msg, text: errorText, thoughts: [...(msg.thoughts || []), "Error encountered."] }
          : msg
      ));
    } finally {
      clearInterval(thoughtInterval);
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-md bg-[var(--bg-secondary)] p-8 rounded-2xl shadow-lg border border-[var(--border-subtle)]">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold font-heading text-[var(--accent-primary)] mb-2">Mediquery AI</h1>
            <p className="text-[var(--text-secondary)]">Please sign in to continue</p>
          </div>
          <Login onLogin={handleLogin} />
        </div>
      </div>
    );
  }

  return (
    <Layout
      onNewChat={handleNewChat}
      threads={threads}
      currentChatId={currentThreadId}
      onSelectThread={handleSelectThread}
      onRenameThread={handleRenameThread}
      onDeleteThread={handleDeleteThread}
      onPinThread={handlePinThread}
      onShareThread={handleShareThread}
      theme={theme}
      setTheme={setTheme}
    >
      <ChatInterface messages={messages} theme={theme} />

      <InputBar
        onSend={handleSend}
        isLoading={isLoading}
        fastMode={fastMode}
        setFastMode={setFastMode}
        multiAgent={multiAgent}
        setMultiAgent={setMultiAgent}
        models={MODELS}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
      />
    </Layout>
  );
}

export default App;

