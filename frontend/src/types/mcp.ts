// MCP (Model Context Protocol) type definitions for HTTP transport

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, any>;
    required?: string[];
  };
}

export interface MCPToolCall {
  name: string;
  arguments: Record<string, any>;
}

export interface MCPToolResult {
  content: Array<{
    type: 'text' | 'image' | 'resource';
    text?: string;
    data?: string;
    url?: string;
  }>;
  isError?: boolean;
}

export interface MCPMessage {
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  timestamp: Date;
  toolCall?: MCPToolCall;
  toolResult?: MCPToolResult;
  id: string;
}

export interface MCPServerInfo {
  name: string;
  version: string;
  description?: string;
  tools: MCPTool[];
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface MCPClientConfig {
  serverUrl: string;
  apiKey?: string;
  timeout?: number;
}

// HTTP-specific MCP message format
export interface MCPHttpRequest {
  method: string;
  params?: Record<string, any>;
  id?: string;
}

export interface MCPHttpResponse {
  result?: any;
  error?: {
    code: number;
    message: string;
  };
  id?: string;
}