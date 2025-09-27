import React from 'react';
import { Search, BarChart2, PlayCircle, CheckSquare, Command } from 'lucide-react';

export interface Agent {
  id: string;
  name: string;
  type: 'research' | 'analyst' | 'executor' | 'validator' | 'coordinator';
  model: string;
  status: 'active' | 'idle' | 'error';
  tasks: number;
  successRate: number;
  currentLoad: number;
}

interface AgentCardProps {
  agent: Agent;
  isSelected: boolean;
  onClick: () => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, isSelected, onClick }) => {
  const getIcon = () => {
    switch (agent.type) {
      case 'research':
        return <Search className="w-5 h-5 text-green-400" />;
      case 'analyst':
        return <BarChart2 className="w-5 h-5 text-blue-400" />;
      case 'executor':
        return <PlayCircle className="w-5 h-5 text-purple-400" />;
      case 'validator':
        return <CheckSquare className="w-5 h-5 text-yellow-400" />;
      case 'coordinator':
        return <Command className="w-5 h-5 text-pink-400" />;
      default:
        return null;
    }
  };

  const getIconBgColor = () => {
    switch (agent.type) {
      case 'research':
        return 'bg-green-500/20';
      case 'analyst':
        return 'bg-blue-500/20';
      case 'executor':
        return 'bg-purple-500/20';
      case 'validator':
        return 'bg-yellow-500/20';
      case 'coordinator':
        return 'bg-pink-500/20';
      default:
        return 'bg-gray-500/20';
    }
  };

  const getBorderColor = () => {
    if (agent.status === 'error') return 'border-red-500/30';
    if (agent.status === 'active') {
      switch (agent.type) {
        case 'research':
          return 'border-green-500/30';
        case 'analyst':
          return 'border-blue-500/30';
        case 'executor':
          return 'border-purple-500/30';
        case 'validator':
          return 'border-yellow-500/30';
        case 'coordinator':
          return 'border-pink-500/30';
        default:
          return 'border-gray-500/30';
      }
    }
    return 'border-gray-500/30';
  };

  const getStatusColor = () => {
    switch (agent.status) {
      case 'active':
        return 'bg-green-500/20 text-green-400';
      case 'idle':
        return 'bg-gray-500/20 text-gray-400';
      case 'error':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div
      onClick={onClick}
      className={`bg-gray-700/50 rounded-lg p-4 border cursor-pointer transition-all ${
        getBorderColor()
      } ${isSelected ? 'ring-2 ring-purple-500' : ''} ${
        agent.status === 'active' ? 'animate-pulse-glow' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <div className={`w-10 h-10 ${getIconBgColor()} rounded-lg flex items-center justify-center mr-3`}>
            {getIcon()}
          </div>
          <div>
            <div className="font-semibold">{agent.name}</div>
            <div className="text-xs text-gray-400">{agent.model}</div>
          </div>
        </div>
        <span className={`px-2 py-1 rounded text-xs ${getStatusColor()}`}>
          {agent.status === 'active' ? 'Active' : agent.status === 'idle' ? 'Idle' : 'Error'}
        </span>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Tasks:</span>
          <span>{agent.tasks}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Success:</span>
          <span className={agent.successRate > 95 ? 'text-green-400' : 'text-yellow-400'}>
            {agent.successRate}%
          </span>
        </div>
        <div className="w-full bg-gray-600 rounded-full h-1.5 mt-2">
          <div
            className={`h-1.5 rounded-full ${
              agent.type === 'research' ? 'bg-green-400' :
              agent.type === 'analyst' ? 'bg-blue-400' :
              agent.type === 'executor' ? 'bg-purple-400' :
              agent.type === 'validator' ? 'bg-yellow-400' :
              'bg-pink-400'
            }`}
            style={{ width: `${agent.currentLoad}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default AgentCard;