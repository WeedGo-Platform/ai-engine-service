import React, { useEffect, useState } from 'react';
import { Settings, Download, RefreshCw, Database, Shield, Clock } from 'lucide-react';
import { RateLimit, AuditLog } from '../../types';
import { agiApi } from '../../services/api';

interface SystemTabProps {
  onRefresh: () => void;
}

const SystemTab: React.FC<SystemTabProps> = ({ onRefresh }) => {
  const [rateLimits, setRateLimits] = useState<RateLimit[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      const [limitsData, logsData] = await Promise.all([
        agiApi.getRateLimits(),
        agiApi.getAuditLogs({ limit: 50 })
      ]);
      setRateLimits(limitsData);
      setAuditLogs(logsData);
    } catch (error) {
      console.error('Failed to load system data:', error);
    }
  };

  const handleSystemAction = async (action: string) => {
    setLoading(true);
    try {
      switch (action) {
        case 'restart':
          await agiApi.restartAgents();
          break;
        case 'clear-cache':
          await agiApi.clearCache();
          break;
        case 'backup':
          await agiApi.createBackup();
          break;
      }
      onRefresh();
    } catch (error) {
      console.error(`Failed to execute ${action}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportLogs = async (format: 'json' | 'csv') => {
    try {
      const blob = await agiApi.exportLogs(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agi-logs-${new Date().toISOString()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* System Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Controls</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => handleSystemAction('restart')}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className="h-6 w-6 text-blue-600 mb-2" />
            <span className="text-sm font-medium">Restart Agents</span>
          </button>

          <button
            onClick={() => handleSystemAction('clear-cache')}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <Database className="h-6 w-6 text-yellow-600 mb-2" />
            <span className="text-sm font-medium">Clear Cache</span>
          </button>

          <button
            onClick={() => handleSystemAction('backup')}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <Shield className="h-6 w-6 text-green-600 mb-2" />
            <span className="text-sm font-medium">Create Backup</span>
          </button>

          <button
            onClick={() => handleExportLogs('json')}
            className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Download className="h-6 w-6 text-purple-600 mb-2" />
            <span className="text-sm font-medium">Export Logs</span>
          </button>
        </div>
      </div>

      {/* Rate Limits */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Limits</h3>
        <div className="space-y-3">
          {rateLimits.map((limit) => (
            <div key={limit.rule} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">{limit.rule.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-500">{limit.window}s window</p>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">{limit.current} / {limit.limit}</span>
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      (limit.current / limit.limit) > 0.9 ? 'bg-red-500' :
                      (limit.current / limit.limit) > 0.7 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(100, (limit.current / limit.limit) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Audit Logs</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => handleExportLogs('csv')}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Export CSV
            </button>
          </div>
        </div>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {auditLogs.map((log) => (
            <div key={log.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <Clock className="h-4 w-4 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{log.event_type}</p>
                <p className="text-xs text-gray-500">{log.timestamp} • User: {log.user_id}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemTab;