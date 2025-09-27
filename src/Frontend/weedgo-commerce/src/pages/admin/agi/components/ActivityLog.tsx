import React from 'react';
import { Activity } from 'lucide-react';

export interface ActivityEntry {
  id: string;
  timestamp: string;
  type: 'MODEL' | 'TOOL' | 'AGENT' | 'AUTH' | 'SECURITY';
  message: string;
}

interface ActivityLogProps {
  activities?: ActivityEntry[];
}

const ActivityLog: React.FC<ActivityLogProps> = ({ activities }) => {
  const defaultActivities: ActivityEntry[] = [
    {
      id: '1',
      timestamp: '14:32:01',
      type: 'MODEL',
      message: 'Claude-3-Opus invoked by Research Agent'
    },
    {
      id: '2',
      timestamp: '14:31:45',
      type: 'TOOL',
      message: 'Web search executed successfully'
    },
    {
      id: '3',
      timestamp: '14:31:12',
      type: 'AGENT',
      message: 'Coordinator delegated task to Analyst'
    },
    {
      id: '4',
      timestamp: '14:30:58',
      type: 'AUTH',
      message: 'User authenticated via API key'
    },
    {
      id: '5',
      timestamp: '14:30:32',
      type: 'SECURITY',
      message: 'Content filtered: PII detected and redacted'
    }
  ];

  const data = activities || defaultActivities;

  const getTypeColor = (type: ActivityEntry['type']) => {
    switch (type) {
      case 'MODEL':
        return 'bg-blue-500/20 text-blue-400';
      case 'TOOL':
        return 'bg-green-500/20 text-green-400';
      case 'AGENT':
        return 'bg-purple-500/20 text-purple-400';
      case 'AUTH':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'SECURITY':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700">
      <div className="p-6 border-b border-gray-700">
        <h3 className="font-semibold flex items-center">
          <Activity className="w-4 h-4 mr-2" />
          Real-time Activity
        </h3>
      </div>
      <div className="p-4 space-y-2 max-h-64 overflow-y-auto">
        {data.map((activity) => (
          <div key={activity.id} className="flex items-center space-x-3 text-sm">
            <span className="text-gray-500 min-w-[60px]">{activity.timestamp}</span>
            <span className={`px-2 py-1 rounded text-xs ${getTypeColor(activity.type)}`}>
              {activity.type}
            </span>
            <span className="text-gray-300">{activity.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityLog;