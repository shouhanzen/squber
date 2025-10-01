import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Anchor } from 'lucide-react';
import { SquberWebSocketClient, ChatMessage } from '../lib/websocketClient';

interface ChatInterfaceProps {
  client: SquberWebSocketClient;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ client }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [availableTools, setAvailableTools] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Set up event listeners
    client.on('message', (message: ChatMessage) => {
      setMessages(prev => [...prev, {
        ...message,
        timestamp: new Date(message.timestamp)
      }]);
    });

    client.on('typing', (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping);
    });

    client.on('tools', (tools: any[]) => {
      setAvailableTools(tools);
    });

    client.on('connected', () => {
      setConnectionStatus('connected');
    });

    client.on('disconnected', () => {
      setConnectionStatus('disconnected');
    });

    client.on('error', (data: any) => {
      console.error('Chat error:', data);
    });

    // Update connection status
    const updateStatus = () => {
      setConnectionStatus(client.getConnectionState());
    };

    const interval = setInterval(updateStatus, 1000);
    updateStatus();

    return () => {
      clearInterval(interval);
    };
  }, [client]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    // Send to backend
    client.sendMessage(userMessage);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-100 text-green-800';
      case 'connecting': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-red-100 text-red-800';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      default: return 'Disconnected';
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';

    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`
          chat-bubble
          ${isUser ? 'chat-bubble-user' : isSystem ? 'chat-bubble-system' : 'chat-bubble-assistant'}
        `}>
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Render tool results if available */}
          {message.toolResults && message.toolResults.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.toolResults.map((toolResult, index) => (
                <div key={index} className="tool-result">
                  <div className="font-semibold text-sm mb-2">🛠️ {toolResult.toolName}</div>
                  <pre className="text-xs overflow-x-auto">
                    {typeof toolResult.result === 'string'
                      ? toolResult.result
                      : JSON.stringify(toolResult.result, null, 2)
                    }
                  </pre>
                </div>
              ))}
            </div>
          )}

          <div className="text-xs opacity-60 mt-2">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h1>
          <Anchor className="w-6 h-6" />
          Squber - Squid Fishing AI Assistant
        </h1>

        <div className="flex items-center gap-4">
          <div className={`connection-status ${getStatusColor()}`}>
            {getStatusText()}
          </div>

          {availableTools.length > 0 && (
            <div className="text-sm opacity-80">
              {availableTools.length} tools available
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && connectionStatus === 'connected' && (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-4">🦑</div>
            <p>Welcome to Squber! Start a conversation about squid fishing.</p>
          </div>
        )}

        {messages.map(renderMessage)}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start mb-4">
            <div className="chat-bubble chat-bubble-assistant">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Squber is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about markets, trip planning, futures, or regulations..."
          disabled={connectionStatus !== 'connected' || isTyping}
          rows={1}
          style={{
            minHeight: '2.5rem',
            height: 'auto',
            resize: 'none',
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = target.scrollHeight + 'px';
          }}
        />

        <button
          onClick={handleSend}
          disabled={!input.trim() || connectionStatus !== 'connected' || isTyping}
          className="send-button"
        >
          <Send className="w-4 h-4" />
          Send
        </button>
      </div>
    </div>
  );
};