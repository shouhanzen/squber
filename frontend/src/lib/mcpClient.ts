/**
 * MCP HTTP Client for connecting to Squber MCP server
 * Uses the official @modelcontextprotocol/sdk
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type {
  MCPTool,
  MCPToolCall,
  MCPToolResult,
  MCPServerInfo,
  ConnectionStatus,
  MCPClientConfig
} from '../types/mcp';

export class MCPHttpClient {
  private config: MCPClientConfig;
  private status: ConnectionStatus = 'disconnected';
  private tools: MCPTool[] = [];
  private serverInfo: MCPServerInfo | null = null;
  private client: Client | null = null;
  private transport: StreamableHTTPTransport | null = null;

  constructor(config: MCPClientConfig) {
    this.config = {
      timeout: 30000,
      ...config
    };
  }

  public getStatus(): ConnectionStatus {
    return this.status;
  }

  public getTools(): MCPTool[] {
    return this.tools;
  }

  public getServerInfo(): MCPServerInfo | null {
    return this.serverInfo;
  }

  /**
   * Connect to the MCP server and initialize
   */
  public async connect(): Promise<void> {
    this.status = 'connecting';

    try {
      // Create Streamable HTTP transport
      this.transport = new StreamableHTTPTransport(
        new URL(`${this.config.serverUrl}/mcp`)
      );

      // Create MCP client
      this.client = new Client(
        {
          name: 'squber-frontend',
          version: '1.0.0',
        },
        {
          capabilities: {
            tools: {},
          },
        }
      );

      // Connect to the server
      await this.client.connect(this.transport);

      // List available tools
      const toolsResult = await this.client.request(
        { method: 'tools/list' },
        // Schema validation can be added here
      );

      if (toolsResult.tools) {
        this.tools = toolsResult.tools.map((tool: any) => ({
          name: tool.name,
          description: tool.description || '',
          inputSchema: tool.inputSchema
        }));
      }

      // Set server info
      this.serverInfo = {
        name: 'Squber - Squid Fishing AI Assistant',
        version: '1.0.0',
        description: 'AI Assistant for Squid Fishers with Futures Market',
        tools: this.tools
      };

      this.status = 'connected';
    } catch (error) {
      this.status = 'error';
      this.cleanup();
      throw new Error(`Failed to connect to MCP server: ${error}`);
    }
  }

  /**
   * Disconnect from the server
   */
  public disconnect(): void {
    this.cleanup();
    this.status = 'disconnected';
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    if (this.client) {
      this.client.close();
      this.client = null;
    }
    this.transport = null;
    this.tools = [];
    this.serverInfo = null;
  }

  /**
   * Call an MCP tool
   */
  public async callTool(toolCall: MCPToolCall): Promise<MCPToolResult> {
    if (this.status !== 'connected' || !this.client) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const result = await this.client.request(
        {
          method: 'tools/call',
          params: {
            name: toolCall.name,
            arguments: toolCall.arguments || {}
          }
        }
      );

      return {
        content: result.content || [{
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }],
        isError: result.isError || false
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error calling tool ${toolCall.name}: ${error}`
        }],
        isError: true
      };
    }
  }

  /**
   * Test connection to server
   */
  public async testConnection(): Promise<{ success: boolean; error?: string }> {
    try {
      if (!this.client) {
        return { success: false, error: 'No client connection' };
      }

      // Try to ping the server
      await this.client.request({ method: 'ping' });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: `Connection test failed: ${error}`
      };
    }
  }

  /**
   * Get detailed server info
   */
  public async getServerDetails(): Promise<any> {
    if (!this.client) {
      throw new Error('Not connected to server');
    }

    try {
      return await this.client.request({ method: 'initialize' });
    } catch (error) {
      throw new Error(`Failed to get server details: ${error}`);
    }
  }
}