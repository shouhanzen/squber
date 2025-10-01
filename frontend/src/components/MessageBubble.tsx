import React from 'react';
import type { MCPMessage } from '../types/mcp';
import { User, Bot, Settings, AlertTriangle, Wrench } from 'lucide-react';

interface MessageBubbleProps {
  message: MCPMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { role, content, toolCall, toolResult } = message;

  const getBubbleClass = () => {
    switch (role) {
      case 'user':
        return 'chat-bubble chat-bubble-user';
      case 'assistant':
        return 'chat-bubble chat-bubble-assistant';
      case 'system':
        return 'chat-bubble chat-bubble-system';
      case 'tool':
        return 'tool-result';
      default:
        return 'chat-bubble chat-bubble-assistant';
    }
  };

  const getIcon = () => {
    switch (role) {
      case 'user':
        return <User className="w-4 h-4" />;
      case 'assistant':
        return <Bot className="w-4 h-4" />;
      case 'system':
        return <Settings className="w-4 h-4" />;
      case 'tool':
        return <Wrench className="w-4 h-4" />;
      default:
        return <Bot className="w-4 h-4" />;
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`${getBubbleClass()} relative`}>
        {/* Icon for non-user messages */}
        {role !== 'user' && (
          <div className="flex items-center gap-2 mb-1">
            {getIcon()}
            <span className="text-xs font-medium capitalize">
              {role === 'tool' ? toolCall?.name || 'Tool' : role}
            </span>
            <span className="text-xs opacity-60">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>
        )}

        {/* Message content */}
        <div className="whitespace-pre-wrap">
          {content}
        </div>

        {/* Tool call indicator */}
        {toolCall && (
          <div className="mt-2 text-xs opacity-75">
            <div className="flex items-center gap-1">
              <Wrench className="w-3 h-3" />
              Calling: {toolCall.name}
            </div>
            {Object.keys(toolCall.arguments).length > 0 && (
              <div className="mt-1 text-xs font-mono bg-black bg-opacity-10 rounded px-2 py-1">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </div>
            )}
          </div>
        )}

        {/* Tool result indicator */}
        {toolResult && (
          <div className="mt-2">
            {toolResult.isError ? (
              <div className="flex items-center gap-1 text-red-600 text-xs">
                <AlertTriangle className="w-3 h-3" />
                Tool Error
              </div>
            ) : (
              <div className="flex items-center gap-1 text-green-600 text-xs">
                <Wrench className="w-3 h-3" />
                Tool Success
              </div>
            )}
          </div>
        )}

        {/* Timestamp for user messages */}
        {role === 'user' && (
          <div className="text-xs opacity-60 mt-1 text-right">
            {formatTimestamp(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};