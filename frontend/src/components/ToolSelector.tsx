import React, { useState } from 'react';
import type { MCPTool } from '../types/mcp';
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react';

interface ToolSelectorProps {
  tools: MCPTool[];
  onToolSelect: (tool: MCPTool, args: Record<string, any>) => void;
}

export const ToolSelector: React.FC<ToolSelectorProps> = ({ tools, onToolSelect }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [toolArgs, setToolArgs] = useState<Record<string, any>>({});

  const handleToolSelect = (tool: MCPTool) => {
    setSelectedTool(tool);
    setToolArgs({});
  };

  const handleArgChange = (argName: string, value: any) => {
    setToolArgs(prev => ({
      ...prev,
      [argName]: value
    }));
  };

  const handleExecute = () => {
    if (selectedTool) {
      onToolSelect(selectedTool, toolArgs);
      setSelectedTool(null);
      setToolArgs({});
      setIsExpanded(false);
    }
  };

  const getToolDescription = (tool: MCPTool) => {
    const descriptions: Record<string, string> = {
      'get_market_report': 'Get current market conditions and pricing',
      'trip_advisor': 'Get trip planning recommendations',
      'futures_contract_explorer': 'Explore available futures contracts',
      'futures_market_data': 'Get futures market data and pricing',
      'futures_hedge_advisor': 'Get hedging advice for your catch',
      'futures_position_tracker': 'Track your futures positions',
      'futures_basis_analysis': 'Analyze basis between spot and futures',
      'query_data': 'Query the maritime database directly',
      'squber_howto': 'Get help and documentation'
    };
    return descriptions[tool.name] || tool.description;
  };

  const renderArgInput = (argName: string, argSchema: any) => {
    if (argSchema.type === 'string') {
      return (
        <input
          type="text"
          placeholder={argSchema.description || argName}
          value={toolArgs[argName] || ''}
          onChange={(e) => handleArgChange(argName, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-squber-blue"
        />
      );
    } else if (argSchema.type === 'number') {
      return (
        <input
          type="number"
          placeholder={argSchema.description || argName}
          value={toolArgs[argName] || ''}
          onChange={(e) => handleArgChange(argName, parseFloat(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-squber-blue"
        />
      );
    } else if (argSchema.enum) {
      return (
        <select
          value={toolArgs[argName] || ''}
          onChange={(e) => handleArgChange(argName, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-squber-blue"
        >
          <option value="">Select {argName}</option>
          {argSchema.enum.map((option: string) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }
    return null;
  };

  if (tools.length === 0) return null;

  return (
    <div className="bg-white border-t border-gray-200">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4" />
          <span>Available Tools ({tools.length})</span>
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 p-4">
          {!selectedTool ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {tools.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => handleToolSelect(tool)}
                  className="p-3 text-left border border-gray-200 rounded-lg hover:border-squber-blue hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm text-gray-900">{tool.name}</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {getToolDescription(tool)}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">{selectedTool.name}</h3>
                <button
                  onClick={() => setSelectedTool(null)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Back
                </button>
              </div>

              <p className="text-sm text-gray-600">{getToolDescription(selectedTool)}</p>

              {selectedTool.inputSchema.properties && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-700">Parameters:</h4>
                  {Object.entries(selectedTool.inputSchema.properties).map(([argName, argSchema]: [string, any]) => (
                    <div key={argName}>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        {argName}
                        {selectedTool.inputSchema.required?.includes(argName) && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </label>
                      {renderArgInput(argName, argSchema)}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleExecute}
                  className="px-4 py-2 bg-squber-blue text-white rounded-md text-sm hover:bg-squber-navy"
                >
                  Execute Tool
                </button>
                <button
                  onClick={() => setSelectedTool(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};