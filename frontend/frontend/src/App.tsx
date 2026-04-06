import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AssistantResponse, ConversationMessage, Conversation } from './types';
import ChatSidebar from './components/ChatSidebar';
import { apiService } from './services/api';
import MessageInput from './components/MessageInput';
import ChatMessage from './components/ChatMessage';
import Toast from './components/Toast';
import ConnectionStatus from './components/ConnectionStatus';
import LanguageDropdown from './components/LanguageDropdown';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';

function AppContent() {
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(true);
  
  // Load conversations from localStorage on mount
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    try {
      const saved = localStorage.getItem('chatHistory');
      return saved ? JSON.parse(saved) : [];
    } catch { 
      return []; 
    }
  });
  
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 1024);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'warning' | 'error' } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasScrolledRef = useRef(false);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    if (!hasScrolledRef.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      hasScrolledRef.current = true;
      // Reset after animation completes
      setTimeout(() => {
        hasScrolledRef.current = false;
      }, 500);
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Save conversations to localStorage
  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(conversations));
  }, [conversations]);

  // Sync current messages with active conversation
  useEffect(() => {
    if (!currentConversationId) return;

    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        return {
          ...c,
          messages: messages,
          title: c.title === 'New Chat' && messages.length > 0
            ? messages[0].userMessage.slice(0, 30) + (messages[0].userMessage.length > 30 ? '...' : '')
            : c.title,
          timestamp: new Date().toISOString()
        };
      }
      return c;
    }));
  }, [messages, currentConversationId]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setCurrentConversationId(null);
    if (window.innerWidth < 1024) setIsSidebarOpen(false);
  }, []);

  const handleSelectChat = useCallback((id: string) => {
    const convo = conversations.find(c => c.id === id);
    if (convo) {
      setMessages(convo.messages);
      setCurrentConversationId(id);
      if (window.innerWidth < 1024) setIsSidebarOpen(false);
    }
  }, [conversations]);

  const handleDeleteChat = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversationId === id) {
      handleNewChat();
    }
  }, [currentConversationId, handleNewChat]);

  const handleSendMessage = useCallback(async (userMessage: string) => {
    // Initialize conversation if needed
    let activeId = currentConversationId;
    if (!activeId) {
      activeId = `conv-${Date.now()}`;
      const newConv: Conversation = {
        id: activeId,
        title: 'New Chat',
        messages: [],
        timestamp: new Date().toISOString()
      };
      setConversations(prev => [newConv, ...prev]);
      setCurrentConversationId(activeId);
    }

    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const timestamp = new Date().toISOString();

    // Add user message immediately
    const newMessage: ConversationMessage = {
      id: messageId,
      userMessage: userMessage,
      assistantResponse: null,
      timestamp,
      isLoading: true,
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsLoading(true);
    setToast({ message: 'Message sent', type: 'success' });

    try {
      const response = await apiService.sendMessage({
        message: userMessage,
        platform: 'web',
        device_context: 'desktop',
      });

      // Update message with response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                assistantResponse: response,
                isLoading: false,
                error: response.status === 'error' ? response.error : undefined,
              }
            : msg
        )
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';

      const errorResponse: AssistantResponse = {
        status: 'error',
        data: {},
        error: errorMessage,
      };

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                assistantResponse: errorResponse,
                isLoading: false,
                error: errorMessage,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [currentConversationId]);

  // Show auth loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-iosGray-100 to-white dark:from-black dark:to-iosGray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-iosBlue-500"></div>
      </div>
    );
  }

  // Show login/signup when not authenticated
  if (!isAuthenticated) {
    return showLogin ? (
      <Login onToggleForm={() => setShowLogin(false)} />
    ) : (
      <Signup onToggleForm={() => setShowLogin(true)} />
    );
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gradient-to-b from-iosGray-100 to-white dark:from-black dark:to-iosGray-900">
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        activeId={currentConversationId}
        onSelect={handleSelectChat}
        onNewChat={handleNewChat}
        onDelete={handleDeleteChat}
      />

      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${isSidebarOpen ? 'lg:pl-[280px]' : ''}`}>
        {/* Connection Status */}
        <ConnectionStatus />

        {/* Toast Notification */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Header */}
        <header className="sticky top-0 z-40 backdrop-blur-xl bg-white/70 dark:bg-iosGray-900/70 border-b border-iosGray-200/50 dark:border-iosGray-800/50">
          <div className="px-4 sm:px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* Toggle sidebar button - shows on all screens when sidebar is closed on desktop */}
                <button
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className={`p-2 -ml-2 rounded-xl hover:bg-black/5 dark:hover:bg-white/10 transition-colors ${isSidebarOpen ? 'lg:hidden' : ''}`}
                  aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
                  title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
                >
                  <svg className="w-6 h-6 text-iosGray-600 dark:text-iosGray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2.5 h-2.5 bg-iosBlue-500 rounded-full animate-pulse"></span>
                    <h1 className="text-xl sm:text-2xl font-semibold text-iosGray-900 dark:text-white font-sf">
                      Mitra
                    </h1>
                  </div>
                  <p className="text-xs text-iosGray-500 dark:text-iosGray-500 font-sf">
                    AI Being
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-4">
                <LanguageDropdown />
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-right hidden sm:block">
                    <div className="text-sm font-medium text-iosGray-900 dark:text-white font-sf truncate max-w-[150px]">{user?.name}</div>
                    <div className="text-xs text-iosGray-500 dark:text-iosGray-500 font-sf truncate max-w-[150px]">{user?.email}</div>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2 rounded-xl hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-iosGray-600 dark:text-iosGray-300"
                    title="Logout"
                    aria-label="Logout"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="px-4 py-6 max-w-5xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center py-16 sm:py-24">
                <div className="inline-block p-6 sm:p-8 backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl mb-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                  <svg
                    className="w-16 h-16 sm:w-20 sm:h-20 text-iosBlue-500 mx-auto"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl sm:text-3xl font-semibold text-iosGray-900 dark:text-white mb-3 font-sf">
                  Start a conversation
                </h2>
                <p className="text-iosGray-600 dark:text-iosGray-400 mb-8 max-w-md mx-auto font-sf px-4">
                  I'm your unified AI assistant with multi-agent capabilities, safety enforcement, and intelligent routing.
                </p>
              </div>
            ) : (
              <div className="space-y-3 pb-32">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    userMessage={message.userMessage}
                    assistantResponse={message.assistantResponse}
                    timestamp={message.timestamp}
                    isLoading={message.isLoading}
                    error={message.error}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Message Input */}
        <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
