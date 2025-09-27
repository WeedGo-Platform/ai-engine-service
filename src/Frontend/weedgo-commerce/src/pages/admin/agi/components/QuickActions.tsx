import React from 'react';
import { Zap, RefreshCw, Download, Sliders, Database } from 'lucide-react';

interface QuickActionsProps {
  onAction: (action: string) => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({ onAction }) => {
  const actions = [
    {
      id: 'restart',
      icon: <RefreshCw className="w-5 h-5 mb-2 text-blue-400" />,
      title: 'Restart Agents',
      description: 'Restart all active agents',
      color: 'text-blue-400'
    },
    {
      id: 'export',
      icon: <Download className="w-5 h-5 mb-2 text-green-400" />,
      title: 'Export Logs',
      description: 'Download audit logs',
      color: 'text-green-400'
    },
    {
      id: 'configure',
      icon: <Sliders className="w-5 h-5 mb-2 text-purple-400" />,
      title: 'Configure Rules',
      description: 'Adjust security rules',
      color: 'text-purple-400'
    },
    {
      id: 'clear-cache',
      icon: <Database className="w-5 h-5 mb-2 text-yellow-400" />,
      title: 'Clear Cache',
      description: 'Clear system cache',
      color: 'text-yellow-400'
    }
  ];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700">
      <div className="p-6 border-b border-gray-700">
        <h3 className="font-semibold flex items-center">
          <Zap className="w-4 h-4 mr-2" />
          Quick Actions
        </h3>
      </div>
      <div className="p-6 grid grid-cols-2 gap-4">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={() => onAction(action.id)}
            className="p-4 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
          >
            {action.icon}
            <div className="font-medium">{action.title}</div>
            <div className="text-xs text-gray-400">{action.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;