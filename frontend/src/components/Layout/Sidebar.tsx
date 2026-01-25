import React, { useState } from 'react';
import { FiMenu, FiSettings, FiPlus } from 'react-icons/fi';
import SettingsMenu from './SettingsMenu';
import ThreadItem from './ThreadItem';
import type { Thread } from '../../App';

interface SidebarProps {
  onNewChat: () => void;
  threads: Thread[];
  currentChatId: string | null;
  onSelectThread: (id: string) => void;
  onRenameThread: (id: string, newTitle: string) => void;
  onDeleteThread: (id: string) => void;
  onPinThread: (id: string, pinned: boolean) => void;
  onShareThread: (id: string) => void;
  isOpen: boolean;
  onToggle: () => void;
  theme: 'light' | 'dark' | 'drilling-slate' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'drilling-slate' | 'system') => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  onNewChat,
  threads,
  currentChatId,
  onSelectThread,
  onRenameThread,
  onDeleteThread,
  onPinThread,
  onShareThread,
  isOpen,
  onToggle,
  theme,
  setTheme
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const settingsBtnRef = React.useRef<HTMLButtonElement>(null);
  const settingsMenuRef = React.useRef<HTMLDivElement>(null);

  // Close settings when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        showSettings &&
        settingsMenuRef.current &&
        !settingsMenuRef.current.contains(event.target as Node) &&
        settingsBtnRef.current &&
        !settingsBtnRef.current.contains(event.target as Node)
      ) {
        setShowSettings(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showSettings]);

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-[var(--bg-secondary)] border-r border-[var(--border-subtle)] transition-all duration-300 ease-in-out z-40 flex flex-col
      ${isOpen ? 'w-64' : 'w-16'}
      `}
    >
      {/* Header / Hamburger */}
      <div className="flex items-center p-4">
        <button
          onClick={onToggle}
          className="btn-icon p-2 rounded-full hover:bg-[var(--bg-tertiary)] cursor-pointer"
        >
          <FiMenu size={20} />
        </button>
        {isOpen && (
          <span className="ml-3 font-heading font-semibold text-[var(--text-secondary)]">
            {import.meta.env.VITE_APP_TITLE || 'MediqueryAI'}
          </span>
        )}
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-4">
        <button
          onClick={onNewChat}
          className={`w-full flex items-center gap-3 px-3 py-2.5 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-[var(--accent-hover)] transition-colors shadow-sm cursor-pointer
          ${!isOpen && 'justify-center'}
          `}
          title="New Chat"
        >
          <FiPlus size={24} className={isOpen ? 'text-[var(--text-secondary)] shrink-0' : 'text-[var(--text-secondary)] mx-auto shrink-0'} />
          {isOpen && <span className="font-medium text-[var(--text-primary)] text-sm">New chat</span>}
        </button>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto px-2 custom-scrollbar">
        {isOpen && (
          <div className="mb-2 px-4 text-xs font-bold text-[var(--text-primary)] opacity-60 uppercase tracking-wider">
            Recent
          </div>
        )}

        {threads.length === 0 && isOpen && (
          <div className="px-4 py-8 text-sm text-[var(--text-tertiary)] text-center italic">
            No recent chats
          </div>
        )}

        {threads.map((thread) => (
          <ThreadItem
            key={thread.id}
            thread={thread}
            isActive={currentChatId === thread.id}
            isSidebarOpen={isOpen}
            onSelect={onSelectThread}
            onRename={onRenameThread}
            onDelete={onDeleteThread}
            onPin={onPinThread}
            onShare={onShareThread}
          />
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="p-3 mt-auto border-t border-[var(--border-subtle)]">
        <div className="relative">
          <button
            ref={settingsBtnRef}
            onClick={() => setShowSettings(!showSettings)}
            className={`
               flex items-center gap-3 w-full p-3 rounded-md hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] cursor-pointer
               ${!isOpen && 'justify-center'}
               ${showSettings ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]' : ''}
             `}
          >
            <FiSettings size={20} />
            {isOpen && <span className="text-sm font-medium">Settings</span>}
          </button>

          {/* Settings Context Menu */}
          {showSettings && (
            <div ref={settingsMenuRef}>
              <SettingsMenu
                theme={theme}
                setTheme={setTheme}
                onClose={() => setShowSettings(false)}
                isSidebarOpen={isOpen}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
