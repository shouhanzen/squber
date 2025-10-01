import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Anchor, Fish } from 'lucide-react';
import { MCPHttpClient } from '../lib/mcpClient';
import type { MCPMessage, MCPTool, ConnectionStatus } from '../types/mcp';
import { ConnectionStatusIndicator } from './ConnectionStatus';
import { MessageBubble } from './MessageBubble';
import { ToolSelector } from './ToolSelector';

interface ChatInterfaceProps {
  client: MCPHttpClient;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ client }) => {
  const [messages, setMessages] = useState<MCPMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [tools, setTools] = useState<MCPTool[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const updateStatus = () => {
      setStatus(client.getStatus());
      setTools(client.getTools());
    };

    const interval = setInterval(updateStatus, 1000);
    updateStatus();

    return () => clearInterval(interval);
  }, [client]);

  const addMessage = (message: Omit<MCPMessage, 'id' | 'timestamp'>) => {
    const newMessage: MCPMessage = {
      ...message,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || status !== 'connected') return;

    const userMessage = addMessage({
      role: 'user',
      content: input.trim()
    });

    setInput('');
    setIsLoading(true);

    try {
      // Add thinking message
      const thinkingMessage = addMessage({
        role: 'assistant',
        content: 'Let me help you with that...'
      });

      // Simple tool matching logic
      const toolToCall = findBestTool(userMessage.content, tools);

      if (toolToCall) {
        const toolCall = {
          name: toolToCall.name,
          arguments: extractArguments(userMessage.content, toolToCall)
        };

        // Update thinking message with tool call info
        setMessages(prev => prev.map(msg =>
          msg.id === thinkingMessage.id
            ? { ...msg, content: `Calling ${toolToCall.name}...`, toolCall }
            : msg
        ));

        const result = await client.callTool(toolCall);

        // Add tool result message
        addMessage({
          role: 'tool',
          content: result.content[0]?.text || 'No result',
          toolResult: result
        });

        // Add assistant response
        addMessage({
          role: 'assistant',
          content: formatToolResponse(toolToCall.name, result)
        });
      } else {
        // Update thinking message with general response
        setMessages(prev => prev.map(msg =>
          msg.id === thinkingMessage.id
            ? { ...msg, content: generateContextualResponse(userMessage.content) }
            : msg
        ));
      }
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `Error: ${error}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const connectToServer = async () => {
    try {
      setStatus('connecting');
      await client.connect();
      addMessage({
        role: 'system',
        content: `Connected to Squber MCP Server! 🦑\n\nAvailable tools: ${client.getTools().map(t => t.name).join(', ')}`
      });
    } catch (error) {
      addMessage({
        role: 'system',
        content: `Failed to connect: ${error}`
      });
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-squber-blue">
              <Fish className="w-6 h-6" />
              <Anchor className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Squber</h1>
              <p className="text-sm text-gray-600">Squid Fishing AI Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionStatusIndicator status={status} />
            {status === 'disconnected' && (
              <button
                onClick={connectToServer}
                className="px-3 py-1 bg-squber-blue text-white rounded-md text-sm hover:bg-squber-navy"
              >
                Connect
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Fish className="w-12 h-12 mx-auto mb-4 text-squber-blue" />
            <h3 className="text-lg font-medium mb-2">Welcome to Squber!</h3>
            <p className="mb-4">Your AI assistant for squid fishing operations.</p>
            {status === 'disconnected' ? (
              <p className="text-sm">Connect to the MCP server to get started.</p>
            ) : (
              <div className="text-sm space-y-1">
                <p>Ask me about:</p>
                <ul className="space-y-1 text-left max-w-md mx-auto">
                  <li>• Market conditions and pricing</li>
                  <li>• Trip planning and timing</li>
                  <li>• Regulatory updates</li>
                  <li>• Futures market analysis</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Tool Selector */}
      {tools.length > 0 && (
        <ToolSelector
          tools={tools}
          onToolSelect={(tool, args) => {
            setInput(`Use ${tool.name} ${Object.entries(args).map(([k, v]) => `${k}=${v}`).join(' ')}`);
          }}
        />
      )}

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={status === 'connected' ? "Ask about market conditions, trip planning, or futures..." : "Connect to server first"}
            disabled={status !== 'connected' || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-squber-blue focus:border-transparent disabled:bg-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || status !== 'connected' || isLoading}
            className="px-4 py-2 bg-squber-blue text-white rounded-lg hover:bg-squber-navy disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper functions
function findBestTool(input: string, tools: MCPTool[]): MCPTool | null {
  const lowerInput = input.toLowerCase();

  // Tool matching keywords
  const toolKeywords: Record<string, string[]> = {
    'get_market_report': ['market', 'price', 'pricing', 'port', 'sell', 'where to land'],
    'trip_advisor': ['trip', 'when', 'leave', 'return', 'timing', 'plan'],
    'futures_contract_explorer': ['futures', 'contract', 'hedge'],
    'futures_market_data': ['futures price', 'futures data', 'contract price'],
    'futures_hedge_advisor': ['hedge', 'risk', 'futures advice'],
    'query_data': ['data', 'query', 'search', 'find'],
    'squber_howto': ['help', 'how', 'explain', 'what is']
  };

  for (const tool of tools) {
    const keywords = toolKeywords[tool.name] || [];
    if (keywords.some(keyword => lowerInput.includes(keyword))) {
      return tool;
    }
  }

  return null;
}

function extractArguments(input: string, tool: MCPTool): Record<string, any> {
  const args: Record<string, any> = {};

  // Simple argument extraction logic
  if (tool.name === 'get_market_report') {
    args.days = 7; // Default
    if (input.includes('monterey')) args.port_codes = 'MRY';
    if (input.includes('san francisco')) args.port_codes = 'SFO';
  } else if (tool.name === 'trip_advisor') {
    args.vessel_name = 'NORTHWIND'; // Default vessel
    if (input.includes('monterey')) args.target_port = 'MRY';
  }

  return args;
}

function formatToolResponse(toolName: string, result: any): string {
  if (result.isError) {
    return `I encountered an error while ${toolName.replace('_', ' ')}: ${result.content[0]?.text}`;
  }

  const responses: Record<string, string> = {
    'get_market_report': 'Here\'s the current market report:',
    'trip_advisor': 'Here are my trip recommendations:',
    'futures_contract_explorer': 'Here\'s what I found in the futures market:',
    'futures_market_data': 'Here\'s the futures market data:',
    'futures_hedge_advisor': 'Here\'s my hedging advice:',
    'query_data': 'Here\'s what I found in the database:',
    'squber_howto': 'Here\'s the information you requested:'
  };

  return responses[toolName] || 'Here\'s the result:';
}

function generateContextualResponse(input: string): string {
  const lowerInput = input.toLowerCase();

  if (lowerInput.includes('hello') || lowerInput.includes('hi')) {
    return 'Hello! I\'m your Squber AI assistant. I can help you with market conditions, trip planning, and futures trading for squid fishing operations. What would you like to know?';
  }

  if (lowerInput.includes('help')) {
    return 'I can help you with:\n• Market reports and pricing data\n• Trip planning and timing advice\n• Futures market analysis\n• Database queries\n• Regulatory information\n\nTry asking something like "What are current market conditions?" or "When should I plan my next trip?"';
  }

  return 'I\'m here to help with squid fishing operations! Try asking about market conditions, trip planning, or use specific tool names like "get market report" or "trip advisor".';
}