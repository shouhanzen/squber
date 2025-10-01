import React from 'react';
import type { ConnectionStatus } from '../types/mcp';
import { Wifi, WifiOff, Loader2, AlertTriangle } from 'lucide-react';

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: <Wifi className="w-4 h-4" />,
          text: 'Connected',
          className: 'connection-status connected'
        };
      case 'connecting':
        return {
          icon: <Loader2 className="w-4 h-4 animate-spin" />,
          text: 'Connecting',
          className: 'connection-status connecting'
        };
      case 'disconnected':
        return {
          icon: <WifiOff className="w-4 h-4" />,
          text: 'Disconnected',
          className: 'connection-status disconnected'
        };
      case 'error':
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          text: 'Error',
          className: 'connection-status disconnected'
        };
      default:
        return {
          icon: <WifiOff className="w-4 h-4" />,
          text: 'Unknown',
          className: 'connection-status disconnected'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={config.className}>
      {config.icon}
      <span>{config.text}</span>
    </div>
  );
};