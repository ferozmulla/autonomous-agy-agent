import React, { useState, useRef, useEffect, useCallback } from 'react';

/**
 * ConversationalAnalytics — Full-width panel (12 columns).
 *
 * Contains the chat interface: status indicator, message area, text input
 * with send button, and suggested prompt buttons.
 *
 * In Phase 1 (when backendUrl is a placeholder or empty), displays "Coming Soon".
 * In Phase 2, connects to the CA backend via fetch() to /chat and /health.
 *
 * @param {Object} props
 * @param {string} props.backendUrl - CA backend URL (e.g., "https://...run.app").
 * @param {Array<string>} props.suggestedPrompts - Array of 3 suggested prompt strings.
 * @param {string} props.companyName - Company name for display.
 */
export default function ConversationalAnalytics({
  backendUrl,
  suggestedPrompts,
  companyName,
}) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('gray'); // 'gray' | 'yellow' | 'green'
  const [statusText, setStatusText] = useState('Connecting...');
  const messagesEndRef = useRef(null);

  // Determine if backend is available (not a placeholder)
  const isBackendAvailable =
    backendUrl &&
    !backendUrl.startsWith('{{') &&
    backendUrl.startsWith('http');

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Health check polling
  useEffect(() => {
    if (!isBackendAvailable) {
      setStatus('gray');
      setStatusText('Offline');
      return;
    }

    let cancelled = false;

    const checkHealth = async () => {
      try {
        setStatus('yellow');
        setStatusText('Connecting...');

        const response = await fetch(`${backendUrl}/health`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (!cancelled && response.ok) {
          const data = await response.json();
          if (data.status === 'healthy') {
            setStatus('green');
            setStatusText('System Online');

            // Add welcome message if no messages yet
            setMessages((prev) => {
              if (prev.length === 0) {
                return [
                  {
                    role: 'ai',
                    text: `Welcome to the ${companyName} Pulse Dashboard. I can help you analyze ${companyName}'s data. What would you like to explore today?`,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  },
                ];
              }
              return prev;
            });
          } else {
            setStatus('yellow');
            setStatusText('Initializing...');
          }
        }
      } catch {
        if (!cancelled) {
          setStatus('gray');
          setStatusText('Offline');
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [isBackendAvailable, backendUrl, companyName]);

  // Send a message to the CA backend
  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || !isBackendAvailable || isLoading) return;

      const userMessage = {
        role: 'user',
        text: text.trim(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);

      try {
        const response = await fetch(`${backendUrl}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text.trim() }),
        });

        if (response.ok) {
          const data = await response.json();
          setMessages((prev) => [
            ...prev,
            {
              role: 'ai',
              text: data.response || 'No response received.',
              sql: data.sql || null,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: 'ai',
              text: 'Sorry, I encountered an error processing your request. Please try again.',
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: 'ai',
            text: 'Unable to reach the analytics backend. Please check the connection.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [backendUrl, isBackendAvailable, isLoading]
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleSuggestedClick = (prompt) => {
    sendMessage(prompt);
  };

  // --- Phase 1: Coming Soon State ---
  if (!isBackendAvailable) {
    return (
      <div className="panel ca-panel">
        <div className="ca-header">
          <div className="ca-header-left">
            <span className="material-symbols-outlined ca-header-icon">smart_toy</span>
            <h3 className="ca-header-title">Terminal AI Assistant</h3>
          </div>
          <div className="ca-status">
            <span className="ca-status-dot ca-status-dot--gray" />
            <span className="ca-status-text">Offline</span>
          </div>
        </div>

        <div className="ca-coming-soon">
          <span className="material-symbols-outlined ca-coming-soon-icon">smart_toy</span>
          <h4 className="ca-coming-soon-title">Conversational Analytics</h4>
          <p className="ca-coming-soon-desc">
            AI-powered data analysis is coming soon. This panel will feature a
            natural language interface to query and explore {companyName}'s analytics data.
          </p>
        </div>
      </div>
    );
  }

  // --- Phase 2: Live Chat Interface ---
  return (
    <div className="panel ca-panel">
      {/* Header */}
      <div className="ca-header">
        <div className="ca-header-left">
          <span className="material-symbols-outlined ca-header-icon">smart_toy</span>
          <h3 className="ca-header-title">Terminal AI Assistant</h3>
        </div>
        <div className="ca-status">
          <span className={`ca-status-dot ca-status-dot--${status}`} />
          <span className="ca-status-text">{statusText}</span>
        </div>
      </div>

      {/* Messages */}
      <div className="ca-messages">
        {messages.map((msg, index) => (
          <MessageBubble key={index} message={msg} />
        ))}

        {isLoading && (
          <div className="ca-loading">
            <div className="ca-loading-dots">
              <div className="ca-loading-dot" />
              <div className="ca-loading-dot" />
              <div className="ca-loading-dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="ca-input-area">
        <form onSubmit={handleSubmit} className="ca-input-wrapper">
          <input
            type="text"
            className="ca-input"
            placeholder={`Ask a question about ${companyName}...`}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading || status !== 'green'}
          />
          <button
            type="submit"
            className="ca-send-btn"
            disabled={isLoading || !inputValue.trim() || status !== 'green'}
          >
            <span className="material-symbols-outlined">send</span>
          </button>
        </form>

        {/* Suggested prompts */}
        <div className="ca-suggested-prompts">
          {suggestedPrompts
            .filter((p) => p && !p.startsWith('{{'))
            .map((prompt, index) => (
              <button
                key={index}
                className="ca-suggested-btn"
                onClick={() => handleSuggestedClick(prompt)}
                disabled={isLoading || status !== 'green'}
              >
                {prompt}
              </button>
            ))}
        </div>
      </div>
    </div>
  );
}

/**
 * MessageBubble — Single chat message.
 */
function MessageBubble({ message }) {
  const [showSql, setShowSql] = useState(false);
  const isUser = message.role === 'user';
  const senderLabel = isUser ? 'User' : 'AI Assistant';

  return (
    <div className={`ca-message ${isUser ? 'ca-message--user' : ''}`}>
      <span className="ca-message-sender">
        {senderLabel} • {message.timestamp}
      </span>
      <div
        className={`ca-message-bubble ${
          isUser ? 'ca-message-bubble--user' : 'ca-message-bubble--ai'
        }`}
      >
        <p>{message.text}</p>
      </div>
      {message.sql && (
        <>
          <button
            className="ca-sql-toggle"
            onClick={() => setShowSql(!showSql)}
          >
            {showSql ? 'Hide SQL' : 'Show SQL'}
          </button>
          {showSql && (
            <pre className="ca-sql-block">{message.sql}</pre>
          )}
        </>
      )}
    </div>
  );
}
