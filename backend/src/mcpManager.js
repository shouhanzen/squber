/**
 * MCP Manager - Handles connection to Squber MCP server using official SDK
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

export class MCPManager {
  constructor(config) {
    this.config = config;
    this.client = null;
    this.transport = null;
    this.status = 'disconnected';
    this.tools = [];
  }

  async connect() {
    try {
      this.status = 'connecting';

      // Create transport
      this.transport = new StreamableHTTPTransport(
        new URL(`${this.config.serverUrl}/mcp`)
      );

      // Create client
      this.client = new Client(
        {
          name: 'squber-backend',
          version: '1.0.0',
        },
        {
          capabilities: {
            tools: {},
          },
        }
      );

      // Connect
      await this.client.connect(this.transport);

      // Get available tools
      const toolsResult = await this.client.request(
        { method: 'tools/list' }
      );

      this.tools = toolsResult.tools || [];
      this.status = 'connected';

      console.log(`✅ MCP connected - ${this.tools.length} tools available`);
    } catch (error) {
      this.status = 'error';
      console.error('❌ MCP connection failed:', error);
      throw error;
    }
  }

  async disconnect() {
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
    this.transport = null;
    this.status = 'disconnected';
  }

  getStatus() {
    return {
      status: this.status,
      toolCount: this.tools.length,
      tools: this.tools.map(t => ({ name: t.name, description: t.description }))
    };
  }

  getTools() {
    return this.tools;
  }

  async callTool(toolName, arguments = {}) {
    if (!this.client || this.status !== 'connected') {
      throw new Error('MCP client not connected');
    }

    try {
      const result = await this.client.request({
        method: 'tools/call',
        params: {
          name: toolName,
          arguments
        }
      });

      return result;
    } catch (error) {
      console.error(`❌ Tool call failed: ${toolName}`, error);
      throw error;
    }
  }

  // Helper method to get tool by name
  getTool(toolName) {
    return this.tools.find(tool => tool.name === toolName);
  }

  // Check if tool exists
  hassTool(toolName) {
    return this.tools.some(tool => tool.name === toolName);
  }
}