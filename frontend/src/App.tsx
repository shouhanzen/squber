import { useState, useEffect } from 'react';
import { ChatInterface } from './components/SimpleChatInterface';
import { SquberWebSocketClient } from './lib/websocketClient';
import './index.css';

function App() {
  const [client, setClient] = useState<SquberWebSocketClient | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    // Initialize WebSocket client - use the ngrok URL for backend WebSocket
    const wsClient = new SquberWebSocketClient('wss://unmeaningly-nonexpiring-ladonna.ngrok-free.dev/api');

    // Set up connection event handlers
    wsClient.on('connected', () => {
      setIsConnecting(false);
      setConnectionError(null);
      wsClient.startConversation();
    });

    wsClient.on('disconnected', () => {
      setIsConnecting(true);
    });

    wsClient.on('connectionFailed', () => {
      setIsConnecting(false);
      setConnectionError('Failed to connect to Squber backend');
    });

    wsClient.on('error', (data) => {
      setConnectionError(data.error || 'Connection error');
    });

    // Connect to backend
    wsClient.connect().catch((error) => {
      console.error('Failed to connect:', error);
      setIsConnecting(false);
      setConnectionError('Failed to connect to backend');
    });

    setClient(wsClient);

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  if (isConnecting) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to Squber...</p>
        </div>
      </div>
    );
  }

  if (connectionError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️</div>
          <p className="text-red-600 mb-4">{connectionError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Initializing...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <ChatInterface client={client} />
    </div>
  );
}

export default App
