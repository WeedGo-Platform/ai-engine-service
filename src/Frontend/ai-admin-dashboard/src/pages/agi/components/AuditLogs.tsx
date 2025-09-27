/**
 * Audit Logs Component
 * Comprehensive audit trail and activity logging interface
 * Provides detailed tracking of all system activities and user actions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useActivities } from '../hooks/useAGI';
import { apiService } from '../services/api';
import {
  Card, CardHeader, CardContent,
  DataTable, Badge, Button,
  LoadingState, Spinner, Alert,
  Modal
} from './ui';
import { IActivity } from '../types';

interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId?: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  status: 'success' | 'failure' | 'warning';
  ipAddress: string;
  userAgent: string;
  duration: number;
  details?: any;
  errorMessage?: string;
}

interface ActivityFilter {
  dateRange: 'today' | 'week' | 'month' | 'custom';
  activityType: string;
  userId?: string;
  status?: 'all' | 'success' | 'failure' | 'warning';
  searchTerm: string;
}

export const AuditLogs: React.FC = () => {
  const { activities, loading: activitiesLoading } = useActivities(100);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [filter, setFilter] = useState<ActivityFilter>({
    dateRange: 'today',
    activityType: 'all',
    status: 'all',
    searchTerm: ''
  });
  const [exportLoading, setExportLoading] = useState(false);
  const [stats, setStats] = useState({
    totalActions: 0,
    successRate: 0,
    averageResponseTime: 0,
    activeUsers: 0
  });

  // Fetch audit logs
  const fetchAuditLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.dateRange !== 'custom') {
        params.append('range', filter.dateRange);
      }
      if (filter.activityType !== 'all') {
        params.append('type', filter.activityType);
      }
      if (filter.status !== 'all') {
        params.append('status', filter.status);
      }
      if (filter.searchTerm) {
        params.append('search', filter.searchTerm);
      }

      const response = await apiService.get(`/audit/logs?${params.toString()}`);
      setAuditLogs(response.logs || []);
      setStats(response.stats || stats);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  // Export logs
  const handleExport = async (format: 'csv' | 'json') => {
    setExportLoading(true);
    try {
      const response = await apiService.get(`/audit/export?format=${format}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit-logs-${Date.now()}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export logs:', error);
    } finally {
      setExportLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'failure': return 'danger';
      case 'warning': return 'warning';
      default: return 'info';
    }
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-blue-100 text-blue-800';
      case 'POST': return 'bg-green-100 text-green-800';
      case 'PUT': return 'bg-yellow-100 text-yellow-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      case 'PATCH': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'auth':
        return '🔐';
      case 'agent':
        return '🤖';
      case 'model':
        return '🧠';
      case 'system':
        return '⚙️';
      case 'security':
        return '🛡️';
      case 'data':
        return '💾';
      default:
        return '📝';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit & Activity Logs</h1>
          <p className="text-gray-600 mt-1">Complete audit trail of system activities</p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={exportLoading}
          >
            {exportLoading ? <Spinner size="sm" /> : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export CSV
              </>
            )}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={fetchAuditLogs}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600">Total Actions</p>
            <p className="text-2xl font-bold text-gray-900">{stats.totalActions.toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-2xl font-bold text-green-600">{stats.successRate}%</p>
            <p className="text-xs text-gray-500 mt-1">All operations</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600">Avg Response Time</p>
            <p className="text-2xl font-bold text-gray-900">{stats.averageResponseTime}ms</p>
            <p className="text-xs text-gray-500 mt-1">API calls</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600">Active Users</p>
            <p className="text-2xl font-bold text-gray-900">{stats.activeUsers}</p>
            <p className="text-xs text-gray-500 mt-1">Current session</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
              <select
                value={filter.dateRange}
                onChange={(e) => setFilter({ ...filter, dateRange: e.target.value as any })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="today">Today</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Activity Type</label>
              <select
                value={filter.activityType}
                onChange={(e) => setFilter({ ...filter, activityType: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="auth">Authentication</option>
                <option value="agent">Agent Operations</option>
                <option value="model">Model Management</option>
                <option value="system">System Actions</option>
                <option value="security">Security Events</option>
                <option value="data">Data Operations</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filter.status}
                onChange={(e) => setFilter({ ...filter, status: e.target.value as any })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="warning">Warning</option>
              </select>
            </div>

            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                value={filter.searchTerm}
                onChange={(e) => setFilter({ ...filter, searchTerm: e.target.value })}
                placeholder="Search logs..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Logs Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader
              title="Audit Logs"
              subtitle="Detailed system audit trail"
            />
            <CardContent>
              <LoadingState loading={loading} loadingComponent={<Spinner />}>
                {auditLogs.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Timestamp</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">User</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Action</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Resource</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Method</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Status</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Duration</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-700"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {auditLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="py-3 px-4 text-sm text-gray-900">
                              {new Date(log.timestamp).toLocaleString()}
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900">
                              {log.userName}
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900">
                              {log.action}
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900">
                              {log.resource}
                              {log.resourceId && (
                                <span className="text-gray-500 ml-1">#{log.resourceId}</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <span className={`px-2 py-1 text-xs font-medium rounded ${getMethodColor(log.method)}`}>
                                {log.method}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <Badge variant={getStatusColor(log.status)} size="sm">
                                {log.status}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900">
                              {log.duration}ms
                            </td>
                            <td className="py-3 px-4">
                              <button
                                onClick={() => setSelectedLog(log)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No audit logs found
                  </div>
                )}
              </LoadingState>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activities */}
        <Card>
          <CardHeader
            title="Recent Activities"
            subtitle="Live activity stream"
          />
          <CardContent>
            <LoadingState loading={activitiesLoading} loadingComponent={<Spinner />}>
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
                    <div className="text-2xl">{getActivityIcon(activity.type)}</div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleTimeString()}
                        </span>
                        {activity.userId && (
                          <span className="text-xs text-gray-500">
                            by {activity.userId}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {activities.length === 0 && (
                  <p className="text-center text-gray-500 py-4">No recent activities</p>
                )}
              </div>
            </LoadingState>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Log Modal */}
      {selectedLog && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedLog(null)}
          title="Log Details"
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Timestamp</p>
                <p className="font-medium">{new Date(selectedLog.timestamp).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">User</p>
                <p className="font-medium">{selectedLog.userName} ({selectedLog.userId})</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Action</p>
                <p className="font-medium">{selectedLog.action}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Resource</p>
                <p className="font-medium">
                  {selectedLog.resource}
                  {selectedLog.resourceId && ` #${selectedLog.resourceId}`}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Method</p>
                <span className={`px-2 py-1 text-sm font-medium rounded ${getMethodColor(selectedLog.method)}`}>
                  {selectedLog.method}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <Badge variant={getStatusColor(selectedLog.status)}>
                  {selectedLog.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600">Duration</p>
                <p className="font-medium">{selectedLog.duration}ms</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">IP Address</p>
                <p className="font-medium">{selectedLog.ipAddress}</p>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-600 mb-2">User Agent</p>
              <p className="text-sm font-mono bg-gray-100 p-2 rounded">{selectedLog.userAgent}</p>
            </div>

            {selectedLog.details && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Additional Details</p>
                <pre className="text-sm bg-gray-100 p-3 rounded overflow-x-auto">
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.errorMessage && (
              <Alert variant="danger">
                <p className="font-medium">Error Message</p>
                <p className="text-sm mt-1">{selectedLog.errorMessage}</p>
              </Alert>
            )}

            <div className="flex justify-end">
              <Button onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default AuditLogs;