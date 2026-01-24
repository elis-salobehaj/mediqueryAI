import React, { useState, useRef, useEffect } from 'react';
import { FiMessageSquare, FiMoreVertical, FiEdit2, FiTrash2, FiShare2, FiCheck, FiX } from 'react-icons/fi';
import { RiPushpinFill, RiPushpinLine } from 'react-icons/ri';
import type { Thread } from '../../App';

interface ThreadItemProps {
  thread: Thread;
  isActive: boolean;
  isSidebarOpen: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  onDelete: (id: string) => void;
  onPin: (id: string, pinned: boolean) => void;
  onShare: (id: string) => void;
}

const ThreadItem: React.FC<ThreadItemProps> = ({
  thread,
  isActive,
  isSidebarOpen,
  onSelect,
  onRename,
  onDelete,
  onPin,
  onShare
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [editTitle, setEditTitle] = useState(thread.title);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close menu on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when renaming starts
  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isRenaming]);

  const handleRenameSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (editTitle.trim()) {
      onRename(thread.id, editTitle.trim());
    } else {
      setEditTitle(thread.title); // Revert if empty
    }
    setIsRenaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameSubmit();
    if (e.key === 'Escape') {
      setIsRenaming(false);
      setEditTitle(thread.title);
    }
  };

  if (!isSidebarOpen) {
    return (
      <button
        onClick={() => onSelect(thread.id)}
        className={`
          w-full flex items-center justify-center p-2 my-1 rounded-md transition-colors relative group
          ${isActive ? 'bg-[var(--accent-primary)] text-white' : 'hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}
        `}
        title={thread.title}
      >
        <FiMessageSquare size={18} />
        {thread.pinned && (
          <div className="absolute top-1 right-1 w-2 h-2 bg-yellow-500 rounded-full border border-[var(--bg-secondary)]" />
        )}
      </button>
    );
  }

  return (
    <div
      className={`
        group flex items-center gap-2 px-3 py-2 my-1 rounded-full transition-colors relative cursor-pointer
        ${isActive ? 'bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]' : 'hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}
      `}
      onClick={() => !isRenaming && onSelect(thread.id)}
    >
      {/* Icon */}
      <div className={`shrink-0 ${isActive ? 'text-[var(--accent-primary)]' : 'text-[var(--text-tertiary)]'}`}>
        <FiMessageSquare size={16} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {isRenaming ? (
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              ref={inputRef}
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={() => handleRenameSubmit()}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded px-1 py-0.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <span className={`truncate text-sm ${isActive ? 'font-medium' : ''}`}>
              {thread.title}
            </span>
            {thread.pinned && <RiPushpinFill size={12} className="shrink-0 text-yellow-500 ml-2" />}
          </div>
        )}
      </div>

      {/* Actions (Hover Only or Menu Open) */}
      {!isRenaming && (
        <div className="relative" ref={menuRef} onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className={`
              p-1 rounded-md hover:bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]
              ${showMenu ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity
            `}
          >
            <FiMoreVertical size={16} />
          </button>

          {/* Context Menu */}
          {showMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg shadow-xl z-50 overflow-hidden animate-fade-in">
              <button
                onClick={() => { onShare(thread.id); setShowMenu(false); }}
                className="w-full text-left px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] flex items-center gap-2"
              >
                <FiShare2 size={14} /> Share conversation
              </button>
              <button
                onClick={() => { onRename(thread.id, editTitle); setIsRenaming(true); setShowMenu(false); }}
                className="w-full text-left px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] flex items-center gap-2"
              >
                <FiEdit2 size={14} /> Rename
              </button>
              <button
                onClick={() => { onPin(thread.id, !thread.pinned); setShowMenu(false); }}
                className="w-full text-left px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] flex items-center gap-2"
              >
                <RiPushpinLine size={14} /> {thread.pinned ? 'Unpin' : 'Pin'}
              </button>
              <div className="h-px bg-[var(--border-subtle)] my-1" />
              <button
                onClick={() => { onDelete(thread.id); setShowMenu(false); }}
                className="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 flex items-center gap-2"
              >
                <FiTrash2 size={14} /> Delete
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ThreadItem;
