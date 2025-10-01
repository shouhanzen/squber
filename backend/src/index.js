/**
 * Squber Backend - Conversation Lifecycle Manager
 * Handles MCP integration and real-time chat events
 */

import express from 'express';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import { MCPManager } from './mcpManager.js';
import { ConversationManager } from './conversationManager.js';

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server });

// Middleware
app.use(cors());
app.use(express.json());

// Initialize managers
const mcpManager = new MCPManager({
  serverUrl: 'http://localhost:8000'
});

const conversationManager = new ConversationManager(mcpManager);

// Store active WebSocket connections
const clients = new Map();

// WebSocket connection handling
wss.on('connection', (ws) => {
  const clientId = uuidv4();
  clients.set(clientId, ws);

  console.log(`Client connected: ${clientId}`);

  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connected',
    clientId,
    message: 'Connected to Squber chat backend'
  }));

  // Handle incoming messages
  ws.on('message', async (data) => {
    try {
      const message = JSON.parse(data.toString());
      await handleClientMessage(clientId, message, ws);
    } catch (error) {
      console.error('Error handling message:', error);
      ws.send(JSON.stringify({
        type: 'error',
        error: 'Failed to process message'
      }));
    }
  });

  // Handle disconnection
  ws.on('close', () => {
    console.log(`Client disconnected: ${clientId}`);
    clients.delete(clientId);
  });
});

// Handle client messages
async function handleClientMessage(clientId, message, ws) {
  const { type, data } = message;

  switch (type) {
    case 'start_conversation':
      await conversationManager.startConversation(clientId, (event) => {
        ws.send(JSON.stringify(event));
      });
      break;

    case 'send_message':
      await conversationManager.addUserMessage(clientId, data.message);
      break;

    case 'get_tools':
      const tools = await mcpManager.getTools();
      ws.send(JSON.stringify({
        type: 'tools_list',
        tools
      }));
      break;

    default:
      ws.send(JSON.stringify({
        type: 'error',
        error: `Unknown message type: ${type}`
      }));
  }
}

// REST API endpoints
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'squber-backend',
    mcp_status: mcpManager.getStatus()
  });
});

app.get('/api/conversations/:id', async (req, res) => {
  try {
    const conversation = conversationManager.getConversation(req.params.id);
    res.json(conversation || { error: 'Conversation not found' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Initialize MCP connection and start server
async function start() {
  try {
    console.log('🔌 Connecting to MCP server...');
    await mcpManager.connect();
    console.log('✅ Connected to MCP server');

    const PORT = process.env.PORT || 3001;
    server.listen(PORT, () => {
      console.log(`🚀 Squber backend running on port ${PORT}`);
      console.log(`💬 WebSocket server ready for connections`);
    });
  } catch (error) {
    console.error('❌ Failed to start backend:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down backend...');
  await mcpManager.disconnect();
  server.close(() => {
    console.log('✅ Backend shut down gracefully');
    process.exit(0);
  });
});

start();