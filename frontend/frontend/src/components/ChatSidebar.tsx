import React from 'react';
import { Conversation } from '../types';

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  isOpen: boolean;
  onClose: () => void;
}

// Format date in a user-friendly way
const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (diffInDays === 1) {
    return 'Yesterday';
  } else if (diffInDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
};

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  isOpen,
  onClose,
}) => {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50
          w-[280px] bg-iosGray-100/95 dark:bg-iosGray-900/95 backdrop-blur-xl
          border-r border-iosGray-200/50 dark:border-iosGray-800/50
          transform transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          flex flex-col
        `}
        aria-label="Chat history sidebar"
      >
        {/* Header */}
        <div className="p-4 border-b border-iosGray-200/50 dark:border-iosGray-800/50 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-iosGray-900 dark:text-white font-sf">History</h2>
          <div className="flex items-center gap-1">
            {/* Collapse button - visible on all screen sizes */}
            <button 
              onClick={onClose} 
              className="hidden lg:flex p-2 text-iosGray-500 hover:text-iosGray-900 dark:hover:text-white rounded-xl hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
            {/* Close button - mobile only */}
            <button 
              onClick={onClose} 
              className="lg:hidden p-2 text-iosGray-500 hover:text-iosGray-900 dark:hover:text-white rounded-xl hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              aria-label="Close sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 bg-iosBlue-500 hover:bg-iosBlue-600 active:bg-iosBlue-700 text-white py-3 px-4 rounded-xl font-medium transition-all shadow-ios active:scale-[0.98]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
          {conversations.length === 0 ? (
            <div className="text-center py-12 px-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-iosGray-200 dark:bg-iosGray-800 mb-3">
                <svg className="w-6 h-6 text-iosGray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <p className="text-sm text-iosGray-500 dark:text-iosGray-500 font-sf">No conversations yet</p>
              <p className="text-xs text-iosGray-400 dark:text-iosGray-600 mt-1 font-sf">Start a new chat to begin</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`
                  group relative flex items-center p-3 rounded-xl cursor-pointer transition-all
                  ${activeId === conv.id
                    ? 'bg-white dark:bg-iosGray-800 shadow-sm'
                    : 'hover:bg-white/60 dark:hover:bg-iosGray-800/60'
                  }
                `}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelect(conv.id)}
                aria-pressed={activeId === conv.id}
              >
                <div className="flex-1 min-w-0 mr-2">
                  <h3 className={`text-sm font-medium truncate font-sf ${
                    activeId === conv.id 
                      ? 'text-iosBlue-600 dark:text-iosBlue-400' 
                      : 'text-iosGray-900 dark:text-gray-200'
                  }`}>
                    {conv.title || 'New Conversation'}
                  </h3>
                  <p className="text-xs text-iosGray-500 truncate font-sf mt-0.5">
                    {formatDate(conv.timestamp)}
                  </p>
                </div>

                <button
                  onClick={(e) => onDelete(conv.id, e)}
                  aria-label="Delete conversation"
                  className={`
                    p-2 rounded-lg text-iosGray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all
                    opacity-0 group-hover:opacity-100 focus:opacity-100
                    ${activeId === conv.id ? 'opacity-100' : ''}
                  `}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  );
};

export default ChatSidebar;
