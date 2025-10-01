import React, { useState } from 'react';
import { Settings, Save, X } from 'lucide-react';

interface ServerConfigProps {
  currentConfig: {
    serverUrl: string;
    apiKey: string;
  };
  onConfigUpdate: (config: { serverUrl: string; apiKey: string }) => void;
}

export const ServerConfig: React.FC<ServerConfigProps> = ({ currentConfig, onConfigUpdate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [serverUrl, setServerUrl] = useState(currentConfig.serverUrl);
  const [apiKey, setApiKey] = useState(currentConfig.apiKey);

  const handleSave = () => {
    onConfigUpdate({ serverUrl, apiKey });
    setIsOpen(false);
  };

  const handleReset = () => {
    setServerUrl(currentConfig.serverUrl);
    setApiKey(currentConfig.apiKey);
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
        title="Server Configuration"
      >
        <Settings className="w-4 h-4" />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Server Configuration</h2>
          <button
            onClick={handleReset}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Server URL
            </label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="https://your-server.ngrok-free.dev/mcp"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-squber-blue focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-squber-blue focus:border-transparent"
            />
          </div>

          <div className="text-xs text-gray-500">
            <p>Default configuration connects to the Squber demo server.</p>
            <p>Update these values if you're running your own MCP server.</p>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-squber-blue text-white rounded-md hover:bg-squber-navy flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save & Reconnect
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};