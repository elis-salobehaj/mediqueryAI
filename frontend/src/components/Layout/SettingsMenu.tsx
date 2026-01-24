import React, { useRef, useEffect } from 'react';
import { FiMoon, FiSun, FiMonitor, FiCheck } from 'react-icons/fi';
import { GiOilRig } from 'react-icons/gi';

interface SettingsMenuProps {
  theme: 'light' | 'dark' | 'drilling-slate' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'drilling-slate' | 'system') => void;
  onClose: () => void;
  isSidebarOpen: boolean;
}

const SettingsMenu: React.FC<SettingsMenuProps> = ({ theme, setTheme, onClose, isSidebarOpen }) => {
  return (
    <div
      className={`
        absolute bottom-full mb-2 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] 
        rounded-lg shadow-xl overflow-hidden min-w-[200px] animate-fade-in
        ${isSidebarOpen ? 'left-0' : 'left-full ml-2'}
      `}
      style={{ zIndex: 100 }}
    >
      <div className="p-3 border-b border-[var(--border-subtle)]">
        <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">
          Appearance
        </p>

        <div className="space-y-1">
          <button
            onClick={() => setTheme('light')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-[var(--bg-tertiary)] text-sm transition-colors ${theme === 'light' ? 'text-[var(--accent-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}
          >
            <div className="flex items-center gap-2">
              <FiSun size={16} />
              <span>Light</span>
            </div>
            {theme === 'light' && <FiCheck size={16} />}
          </button>

          <button
            onClick={() => setTheme('dark')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-[var(--bg-tertiary)] text-sm transition-colors ${theme === 'dark' ? 'text-[var(--accent-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}
          >
            <div className="flex items-center gap-2">
              <FiMoon size={16} />
              <span>Dark</span>
            </div>
            {theme === 'dark' && <FiCheck size={16} />}
          </button>

          <button
            onClick={() => setTheme('drilling-slate')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-[var(--bg-tertiary)] text-sm transition-colors ${theme === 'drilling-slate' ? 'text-[var(--accent-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}
          >
            <div className="flex items-center gap-2">
              <GiOilRig size={16} />
              <span>Drilling Slate</span>
            </div>
            {theme === 'drilling-slate' && <FiCheck size={16} />}
          </button>

          <button
            onClick={() => setTheme('system')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-[var(--bg-tertiary)] text-sm transition-colors ${theme === 'system' ? 'text-[var(--accent-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}
          >
            <div className="flex items-center gap-2">
              <FiMonitor size={16} />
              <span>System</span>
            </div>
            {theme === 'system' && <FiCheck size={16} />}
          </button>
        </div>
      </div>

      <div className="p-2">
        <button className="w-full text-left px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-md">
          Help & Support
        </button>
        <button className="w-full text-left px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-md">
          About {import.meta.env.VITE_APP_TITLE || 'MediqueryAI'}
        </button>
      </div>
    </div>
  );
};

export default SettingsMenu;
