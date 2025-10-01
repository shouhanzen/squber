/**
 * Conversation Manager - Handles chat lifecycle and MCP tool integration
 */

import { v4 as uuidv4 } from 'uuid';

export class ConversationManager {
  constructor(mcpManager) {
    this.mcpManager = mcpManager;
    this.conversations = new Map();
  }

  async startConversation(clientId, eventCallback) {
    const conversationId = uuidv4();

    const conversation = {
      id: conversationId,
      clientId,
      messages: [],
      createdAt: new Date(),
      eventCallback
    };

    this.conversations.set(clientId, conversation);

    // Send initial system message
    await this.addSystemMessage(clientId,
      "🦑 Welcome to Squber! I'm your AI assistant for squid fishing operations. " +
      "I can help you with market intelligence, trip planning, futures trading, and regulatory compliance. " +
      "What would you like to know?"
    );

    // Send available tools
    const tools = this.mcpManager.getTools();
    eventCallback({
      type: 'tools_available',
      tools: tools.map(t => ({
        name: t.name,
        description: t.description
      }))
    });

    return conversation;
  }

  async addUserMessage(clientId, content) {
    const conversation = this.conversations.get(clientId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    // Add user message
    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date()
    };

    conversation.messages.push(userMessage);
    conversation.eventCallback({
      type: 'message_added',
      message: userMessage
    });

    // Process the message and generate response
    await this.processUserMessage(conversation, content);
  }

  async addSystemMessage(clientId, content) {
    const conversation = this.conversations.get(clientId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    const systemMessage = {
      id: uuidv4(),
      role: 'system',
      content,
      timestamp: new Date()
    };

    conversation.messages.push(systemMessage);
    conversation.eventCallback({
      type: 'message_added',
      message: systemMessage
    });
  }

  async addAssistantMessage(clientId, content, toolResults = null) {
    const conversation = this.conversations.get(clientId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    const assistantMessage = {
      id: uuidv4(),
      role: 'assistant',
      content,
      toolResults,
      timestamp: new Date()
    };

    conversation.messages.push(assistantMessage);
    conversation.eventCallback({
      type: 'message_added',
      message: assistantMessage
    });
  }

  async processUserMessage(conversation, userMessage) {
    try {
      // Send typing indicator
      conversation.eventCallback({
        type: 'assistant_typing',
        isTyping: true
      });

      // Simple keyword-based tool selection for demo
      const response = await this.generateResponse(userMessage);

      // Stop typing indicator
      conversation.eventCallback({
        type: 'assistant_typing',
        isTyping: false
      });

      await this.addAssistantMessage(conversation.clientId, response.content, response.toolResults);

    } catch (error) {
      console.error('Error processing message:', error);

      conversation.eventCallback({
        type: 'assistant_typing',
        isTyping: false
      });

      await this.addAssistantMessage(
        conversation.clientId,
        "Sorry, I encountered an error processing your request. Please try again."
      );
    }
  }

  async generateResponse(userMessage) {
    const message = userMessage.toLowerCase();

    // Simple keyword-based tool routing
    if (message.includes('market') || message.includes('price')) {
      return await this.handleMarketQuery();
    } else if (message.includes('trip') || message.includes('fishing')) {
      return await this.handleTripQuery();
    } else if (message.includes('tool') || message.includes('help')) {
      return await this.handleToolsQuery();
    } else if (message.includes('futures') || message.includes('hedge')) {
      return await this.handleFuturesQuery();
    } else {
      return {
        content: "I can help you with:\n" +
          "• 📊 **Market intelligence** - Current prices and trends\n" +
          "• 🚢 **Trip planning** - When to fish and where to land\n" +
          "• 📈 **Futures trading** - Hedging strategies\n" +
          "• 📋 **Tools and data** - Available MCP tools\n\n" +
          "What would you like to explore?"
      };
    }
  }

  async handleMarketQuery() {
    try {
      const result = await this.mcpManager.callTool('get_market_report', { days: 7 });

      return {
        content: "Here's the latest market intelligence:",
        toolResults: [{
          toolName: 'get_market_report',
          result: result
        }]
      };
    } catch (error) {
      return {
        content: "I couldn't fetch the market report right now. The MCP connection might be down."
      };
    }
  }

  async handleTripQuery() {
    try {
      const result = await this.mcpManager.callTool('trip_advisor', {});

      return {
        content: "Here are trip planning recommendations:",
        toolResults: [{
          toolName: 'trip_advisor',
          result: result
        }]
      };
    } catch (error) {
      return {
        content: "I couldn't get trip planning advice right now. Please try again later."
      };
    }
  }

  async handleFuturesQuery() {
    try {
      const result = await this.mcpManager.callTool('futures_contract_explorer', {});

      return {
        content: "Here's information about available futures contracts:",
        toolResults: [{
          toolName: 'futures_contract_explorer',
          result: result
        }]
      };
    } catch (error) {
      return {
        content: "I couldn't access futures data right now. Please check back later."
      };
    }
  }

  async handleToolsQuery() {
    const tools = this.mcpManager.getTools();

    const toolsList = tools.map(tool =>
      `• **${tool.name}** - ${tool.description}`
    ).join('\n');

    return {
      content: `I have access to ${tools.length} specialized tools:\n\n${toolsList}\n\n` +
        "Just ask me about markets, trips, futures, or regulations and I'll use the right tools!"
    };
  }

  getConversation(clientId) {
    return this.conversations.get(clientId);
  }

  getAllConversations() {
    return Array.from(this.conversations.values());
  }
}