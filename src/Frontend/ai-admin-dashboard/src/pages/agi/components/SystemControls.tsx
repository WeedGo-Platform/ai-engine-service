/**
 * System Controls Component
 * Admin panel for system-wide operations and configuration
 * Provides critical system management capabilities
 */

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Card, CardHeader, CardContent, Button, Alert, Badge, Modal, LoadingState, Spinner } from './ui';

interface SystemAction {
  id: string;
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  requiresConfirmation: boolean;
  icon: React.ReactNode;
}

interface SystemConfig {
  maintenanceMode: boolean;
  debugMode: boolean;
  rateLimitEnabled: boolean;
  cacheEnabled: boolean;
  backupSchedule: string;
  maxConcurrentAgents: number;
  defaultTimeout: number;
  logLevel: 'debug' | 'info' | 'warning' | 'error';
}

export const SystemControls: React.FC = () => {
  const { user } = useAuth();
  const [config, setConfig] = useState<SystemConfig>({
    maintenanceMode: false,
    debugMode: false,
    rateLimitEnabled: true,
    cacheEnabled: true,
    backupSchedule: '0 2 * * *',
    maxConcurrentAgents: 10,
    defaultTimeout: 30000,
    logLevel: 'info'
  });

  const [loading, setLoading] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<SystemAction | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [lastBackup, setLastBackup] = useState<Date>(new Date());
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'degraded' | 'critical'>('healthy');

  // System actions definition
  const systemActions: SystemAction[] = [
    {
      id: 'restart_all_agents',
      name: 'Restart All Agents',
      description: 'Restart all AI agents across the system',
      severity: 'medium',
      requiresConfirmation: true,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )
    },
    {
      id: 'clear_cache',
      name: 'Clear Cache',
      description: 'Clear all system caches and temporary data',
      severity: 'low',
      requiresConfirmation: false,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      )
    },
    {
      id: 'backup_system',
      name: 'Backup System',
      description: 'Create a full system backup including configurations and data',
      severity: 'low',
      requiresConfirmation: false,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      )
    },
    {
      id: 'reset_models',
      name: 'Reset AI Models',
      description: 'Reset all AI models to their default configurations',
      severity: 'high',
      requiresConfirmation: true,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      )
    },
    {
      id: 'emergency_shutdown',
      name: 'Emergency Shutdown',
      description: 'Immediately shutdown all system operations',
      severity: 'critical',
      requiresConfirmation: true,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
      )
    },
    {
      id: 'optimize_database',
      name: 'Optimize Database',
      description: 'Run database optimization and cleanup routines',
      severity: 'medium',
      requiresConfirmation: true,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
      )
    }
  ];

  const handleSystemAction = async (action: SystemAction) => {
    if (action.requiresConfirmation && !confirmAction) {
      setConfirmAction(action);
      return;
    }

    setActionInProgress(action.id);
    setLoading(true);

    try {
      const response = await apiService.post(`/system/actions/${action.id}`, {
        userId: user?.id,
        timestamp: new Date().toISOString()
      });

      if (response.success) {
        // Show success notification
        console.log(`${action.name} completed successfully`);

        // Update relevant state based on action
        if (action.id === 'backup_system') {
          setLastBackup(new Date());
        }
      }
    } catch (error) {
      console.error(`Failed to execute ${action.name}:`, error);
    } finally {
      setLoading(false);
      setActionInProgress(null);
      setConfirmAction(null);
    }
  };

  const updateConfig = async (key: keyof SystemConfig, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);

    try {
      await apiService.put('/system/config', { [key]: value });
      console.log(`Configuration updated: ${key} = ${value}`);
    } catch (error) {
      console.error('Failed to update configuration:', error);
      // Revert on error
      setConfig(config);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200';
      case 'high': return 'bg-orange-100 text-orange-800 hover:bg-orange-200';
      case 'critical': return 'bg-red-100 text-red-800 hover:bg-red-200';
      default: return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'degraded': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Controls</h1>
          <p className="text-gray-600 mt-1">Administrative controls and system management</p>
        </div>
        <div className={`px-4 py-2 rounded-lg font-medium ${getHealthColor(systemHealth)}`}>
          System Status: {systemHealth.charAt(0).toUpperCase() + systemHealth.slice(1)}
        </div>
      </div>

      {/* Quick Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Maintenance Mode</p>
                <p className="text-lg font-semibold">
                  {config.maintenanceMode ? 'Active' : 'Inactive'}
                </p>
              </div>
              <button
                onClick={() => updateConfig('maintenanceMode', !config.maintenanceMode)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  config.maintenanceMode
                    ? 'bg-red-100 text-red-800 hover:bg-red-200'
                    : 'bg-green-100 text-green-800 hover:bg-green-200'
                }`}
              >
                {config.maintenanceMode ? 'Disable' : 'Enable'}
              </button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Debug Mode</p>
                <p className="text-lg font-semibold">
                  {config.debugMode ? 'Enabled' : 'Disabled'}
                </p>
              </div>
              <button
                onClick={() => updateConfig('debugMode', !config.debugMode)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  config.debugMode
                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {config.debugMode ? 'Disable' : 'Enable'}
              </button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Rate Limiting</p>
                <p className="text-lg font-semibold">
                  {config.rateLimitEnabled ? 'Active' : 'Inactive'}
                </p>
              </div>
              <Badge variant={config.rateLimitEnabled ? 'success' : 'warning'}>
                {config.rateLimitEnabled ? 'ON' : 'OFF'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div>
              <p className="text-sm text-gray-600">Last Backup</p>
              <p className="text-lg font-semibold">
                {lastBackup.toLocaleTimeString()}
              </p>
              <p className="text-xs text-gray-500">
                {lastBackup.toLocaleDateString()}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Actions */}
      <Card>
        <CardHeader
          title="System Actions"
          subtitle="Critical system operations - use with caution"
          action={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setConfigModalOpen(true)}
            >
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Advanced Settings
            </Button>
          }
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {systemActions.map((action) => (
              <button
                key={action.id}
                onClick={() => handleSystemAction(action)}
                disabled={actionInProgress !== null}
                className={`
                  p-4 rounded-lg border transition-all
                  ${getSeverityColor(action.severity)}
                  ${actionInProgress === action.id ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  flex flex-col items-start space-y-2
                `}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center space-x-2">
                    {action.icon}
                    <span className="font-medium">{action.name}</span>
                  </div>
                  {actionInProgress === action.id && <Spinner size="sm" />}
                </div>
                <p className="text-xs text-left opacity-75">
                  {action.description}
                </p>
                {action.severity === 'critical' && (
                  <Badge variant="danger" size="sm">
                    Requires Admin Approval
                  </Badge>
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Resource Limits" />
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Concurrent Agents
                </label>
                <input
                  type="number"
                  value={config.maxConcurrentAgents}
                  onChange={(e) => updateConfig('maxConcurrentAgents', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Timeout (ms)
                </label>
                <input
                  type="number"
                  value={config.defaultTimeout}
                  onChange={(e) => updateConfig('defaultTimeout', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1000"
                  max="120000"
                  step="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Log Level
                </label>
                <select
                  value={config.logLevel}
                  onChange={(e) => updateConfig('logLevel', e.target.value as SystemConfig['logLevel'])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Backup & Recovery" />
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Backup Schedule (Cron)
                </label>
                <input
                  type="text"
                  value={config.backupSchedule}
                  onChange={(e) => updateConfig('backupSchedule', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0 2 * * *"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Current: Daily at 2:00 AM
                </p>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Backups</h4>
                <div className="space-y-2">
                  {[0, 1, 2].map((days) => (
                    <div key={days} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-600">
                        {new Date(Date.now() - days * 24 * 60 * 60 * 1000).toLocaleDateString()}
                      </span>
                      <div className="flex items-center space-x-2">
                        <Badge variant="success" size="sm">Complete</Badge>
                        <button className="text-blue-600 hover:text-blue-800 text-sm">
                          Restore
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Modal */}
      {confirmAction && (
        <Modal
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          title="Confirm Action"
        >
          <div className="space-y-4">
            <Alert variant="warning">
              <p className="font-medium">Are you sure you want to {confirmAction.name.toLowerCase()}?</p>
              <p className="text-sm mt-1">{confirmAction.description}</p>
              {confirmAction.severity === 'critical' && (
                <p className="text-sm mt-2 font-semibold">
                  This action cannot be undone and may affect system availability.
                </p>
              )}
            </Alert>

            <div className="flex justify-end space-x-3">
              <Button
                variant="ghost"
                onClick={() => setConfirmAction(null)}
              >
                Cancel
              </Button>
              <Button
                variant={confirmAction.severity === 'critical' ? 'danger' : 'primary'}
                onClick={() => handleSystemAction(confirmAction)}
                disabled={loading}
              >
                {loading ? <Spinner size="sm" /> : 'Confirm'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Advanced Configuration Modal */}
      {configModalOpen && (
        <Modal
          isOpen={true}
          onClose={() => setConfigModalOpen(false)}
          title="Advanced System Configuration"
          size="lg"
        >
          <div className="space-y-6">
            <Alert variant="info">
              <p>Advanced settings should only be modified by system administrators.</p>
              <p className="text-sm mt-1">Changes may affect system performance and stability.</p>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Cache Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.cacheEnabled}
                      onChange={(e) => updateConfig('cacheEnabled', e.target.checked)}
                      className="mr-3"
                    />
                    <span className="text-sm">Enable Cache</span>
                  </label>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-3">Security Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.rateLimitEnabled}
                      onChange={(e) => updateConfig('rateLimitEnabled', e.target.checked)}
                      className="mr-3"
                    />
                    <span className="text-sm">Enable Rate Limiting</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setConfigModalOpen(false)}>
                Done
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default SystemControls;