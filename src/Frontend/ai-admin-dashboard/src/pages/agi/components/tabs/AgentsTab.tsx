import React, { useEffect, useState } from 'react';
import { Play, Pause, RefreshCw, Settings, MoreVertical, Cpu, TrendingUp, CheckCircle } from 'lucide-react';
import { Agent, AgentStats } from '../../types';
import { agiApi } from '../../services/api';

interface AgentsTabProps {
  agents: Agent[];
  onAgentAction: (agentId: string, action: string) => void;
}

const AgentsTab: React.FC<AgentsTabProps> = ({ agents, onAgentAction }) => {
  const [agentStats, setAgentStats] = useState<Record<string, AgentStats>>({});

  useEffect(() => {
    agents.forEach(agent => {
      agiApi.getAgentStats(agent.id).then(stats => {
        setAgentStats(prev => ({ ...prev, [agent.id]: stats }));
      }).catch(console.error);
    });
  }, [agents]);

  return (
    <div className="p-6 overflow-y-auto h-full">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                <p className="text-sm text-gray-500">{agent.type} • {agent.model}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                agent.status === 'active' ? 'bg-green-100 text-green-800' :
                agent.status === 'idle' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {agent.status}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Success Rate</span>
                <span className="text-sm font-semibold">{agent.successRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Tasks</span>
                <span className="text-sm font-semibold">{agent.tasks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Load</span>
                <span className="text-sm font-semibold">{agent.currentLoad}%</span>
              </div>
            </div>

            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => onAgentAction(agent.id, 'restart')}
                className="flex-1 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
              >
                <RefreshCw className="h-4 w-4 inline mr-1" />
                Restart
              </button>
              <button className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                <Settings className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentsTab;