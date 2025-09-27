import React from 'react';
import { Shield, AlertTriangle } from 'lucide-react';

interface SecurityData {
  contentFiltering: 'active' | 'inactive';
  rateLimiting: 'active' | 'inactive';
  accessControl: string;
  totalEvents: number;
  threatsBlocked: number;
  lastThreat?: {
    type: string;
    timestamp: string;
  };
}

interface SecurityMonitorProps {
  security?: SecurityData;
}

const SecurityMonitor: React.FC<SecurityMonitorProps> = ({ security }) => {
  const defaultSecurity: SecurityData = {
    contentFiltering: 'active',
    rateLimiting: 'active',
    accessControl: 'RBAC',
    totalEvents: 14,
    threatsBlocked: 2,
    lastThreat: {
      type: 'SQL injection attempt',
      timestamp: new Date().toISOString()
    }
  };

  const data = security || defaultSecurity;

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="font-semibold flex items-center">
          <Shield className="w-4 h-4 mr-2" />
          Security Monitor
        </h3>
      </div>
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Content Filtering</span>
          <span className={`px-2 py-1 rounded text-xs ${
            data.contentFiltering === 'active'
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            {data.contentFiltering === 'active' ? 'Active' : 'Inactive'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Rate Limiting</span>
          <span className={`px-2 py-1 rounded text-xs ${
            data.rateLimiting === 'active'
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            {data.rateLimiting === 'active' ? 'Active' : 'Inactive'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Access Control</span>
          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">
            {data.accessControl}
          </span>
        </div>
        {data.threatsBlocked > 0 && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-center text-red-400 text-sm mb-1">
              <AlertTriangle className="w-4 h-4 mr-2" />
              {data.threatsBlocked} Threats Blocked Today
            </div>
            {data.lastThreat && (
              <div className="text-xs text-gray-400">
                Last: {data.lastThreat.type}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityMonitor;