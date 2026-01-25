import React, { useState } from 'react';
import Sidebar from './Sidebar';
import type { Thread } from '../../App';

interface LayoutProps {
  children: React.ReactNode;
  onNewChat: () => void;
  threads: Thread[];
  currentChatId: string | null;
  onSelectThread: (id: string) => void;
  onRenameThread: (id: string, newTitle: string) => void;
  onDeleteThread: (id: string) => void;
  onPinThread: (id: string, pinned: boolean) => void;
  onShareThread: (id: string) => void;
  theme: 'light' | 'dark' | 'drilling-slate' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'drilling-slate' | 'system') => void;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  onNewChat,
  threads,
  currentChatId,
  onSelectThread,
  onRenameThread,
  onDeleteThread,
  onPinThread,
  onShareThread,
  theme,
  setTheme
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] transition-colors duration-300 overflow-hidden">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={onNewChat}
        threads={threads}
        currentChatId={currentChatId}
        onSelectThread={onSelectThread}
        onRenameThread={onRenameThread}
        onDeleteThread={onDeleteThread}
        onPinThread={onPinThread}
        onShareThread={onShareThread}
        theme={theme}
        setTheme={setTheme}
      />

      <main
        className={`flex-1 flex flex-col h-full relative transition-all duration-300 ease-in-out
          ${isSidebarOpen ? 'ml-64' : 'ml-16'}
        `}
      >
        {children}
      </main>
    </div>
  );
};

export default Layout;
