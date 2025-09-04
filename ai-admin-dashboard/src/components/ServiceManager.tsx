import { endpoints } from '../config/endpoints';
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import apiService from '../services/api';

interface Service {
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded';
  health: {
    cpu: number;
    memory: number;
    requests: number;
    errors: number;
    latency: number;
  };
  version: string;
  lastChecked: string;
  dependencies: string[];
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  service: string;
  message: string;
  metadata?: any;
}

export default function ServiceManager() {
  const queryClient = useQueryClient();
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [logsService, setLogsService] = useState<string>('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [logFilters, setLogFilters] = useState({
    level: 'all',
    search: '',
    dateRange: {
      start: format(new Date(Date.now() - 24 * 60 * 60 * 1000), 'yyyy-MM-dd\'T\'HH:mm'),
      end: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm')
    }
  });
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  // Fetch real service health data from API
  const { data: servicesData, isLoading: isLoadingServices, error: servicesError, refetch: refetchServices } = useQuery({
    queryKey: ['services', 'health'],
    queryFn: () => apiService.getAllServicesHealth(),
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 3,
  });

  // Transform API data to match Service interface
  const services: Service[] = servicesData?.services ? servicesData.services.map((service: any) => ({
    name: service.name,
    endpoint: service.endpoint || service.url || 'Unknown',
    status: service.status === 'healthy' || service.status === 'running' ? 'online' : 
             service.status === 'unhealthy' || service.status === 'error' ? 'offline' : 'degraded',
    health: {
      cpu: service.health?.cpu || service.cpu || 0,
      memory: service.health?.memory || service.memory || 0,
      requests: service.health?.requests || service.requests_per_minute || 0,
      errors: service.health?.errors || service.error_count || 0,
      latency: service.health?.latency || service.response_time || 0,
    },
    version: service.version || '1.0.0',
    lastChecked: service.last_checked || service.lastChecked || new Date().toISOString(),
    dependencies: service.dependencies || [],
  })) : [];

  // Restart service mutation
  const restartService = useMutation({
    mutationFn: (serviceName: string) => apiService.restartService(serviceName),
    onSuccess: (data, serviceName) => {
      toast.success(`${serviceName} restarted successfully`);
      queryClient.invalidateQueries({ queryKey: ['services', 'health'] });
    },
    onError: () => {
      toast.error('Failed to restart service');
    },
  });

  // Scale service mutation
  const scaleService = useMutation({
    mutationFn: ({ serviceName, replicas }: { serviceName: string; replicas: number }) => 
      apiService.scaleService(serviceName, replicas),
    onSuccess: (data) => {
      toast.success(`Service scaled successfully`);
      queryClient.invalidateQueries({ queryKey: ['services', 'health'] });
    },
    onError: () => {
      toast.error('Failed to scale service');
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800 border-green-200';
      case 'offline': return 'bg-red-100 text-red-800 border-red-200';
      case 'degraded': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getHealthColor = (value: number, type: 'cpu' | 'memory' | 'errors') => {
    if (type === 'errors') {
      if (value === 0) return 'text-green-600';
      if (value < 10) return 'text-yellow-600';
      return 'text-red-600';
    }
    if (value < 50) return 'text-green-600';
    if (value < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'debug': return 'bg-gray-100 text-gray-700';
      case 'info': return 'bg-blue-100 text-blue-700';
      case 'warning': return 'bg-yellow-100 text-yellow-700';
      case 'error': return 'bg-red-100 text-red-700';
      case 'critical': return 'bg-red-600 text-white';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const fetchLogs = async (serviceName: string) => {
    setIsLoadingLogs(true);
    try {
      const response = await fetch(
        endpoints.services.logs(serviceName, logFilters.dateRange.start, logFilters.dateRange.end)
      );
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
        setFilteredLogs(data.logs || []);
      } else {
        // No logs available - show empty state
        setLogs([]);
        setFilteredLogs([]);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      // Show empty state on error
      setLogs([]);
      setFilteredLogs([]);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const openLogsViewer = (serviceName: string) => {
    setLogsService(serviceName);
    setShowLogs(true);
    fetchLogs(serviceName);
  };

  useEffect(() => {
    if (autoRefresh && showLogs && logsService) {
      const interval = setInterval(() => {
        fetchLogs(logsService);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, showLogs, logsService]);

  useEffect(() => {
    let filtered = [...logs];

    // Filter by level
    if (logFilters.level !== 'all') {
      filtered = filtered.filter(log => log.level === logFilters.level);
    }

    // Filter by search
    if (logFilters.search) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(logFilters.search.toLowerCase()) ||
        log.service.toLowerCase().includes(logFilters.search.toLowerCase())
      );
    }

    // Filter by date range
    filtered = filtered.filter(log => {
      const logDate = new Date(log.timestamp);
      const startDate = new Date(logFilters.dateRange.start);
      const endDate = new Date(logFilters.dateRange.end);
      return logDate >= startDate && logDate <= endDate;
    });

    setFilteredLogs(filtered);
  }, [logs, logFilters]);

  const exportLogs = () => {
    const data = JSON.stringify(filteredLogs, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${logsService}-logs-${format(new Date(), 'yyyy-MM-dd-HH-mm')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Logs exported successfully');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Service Manager</h2>
            <p className="text-gray-600 mt-1">Monitor and manage AI engine dependencies</p>
          </div>
          <div className="flex space-x-3">
            <button 
              onClick={() => refetchServices()}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              disabled={isLoadingServices}
            >
              {isLoadingServices ? 'Checking...' : 'Health Check All'}
            </button>
            <button className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600">
              Deploy Update
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoadingServices && (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-weed-green-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading service health data...</p>
        </div>
      )}

      {/* Error State */}
      {servicesError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center space-x-2 text-red-800 mb-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <h3 className="text-lg font-semibold">Failed to load service data</h3>
          </div>
          <p className="text-red-700 mb-4">{servicesError.message}</p>
          <button 
            onClick={() => refetchServices()}
            className="px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      )}

      {/* Services Grid */}
      {!isLoadingServices && !servicesError && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {services.map((service) => (
          <div
            key={service.name}
            className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedService(service)}
          >
            {/* Service Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                <p className="text-sm text-gray-500">v{service.version}</p>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(service.status)}`}>
                {service.status}
              </span>
            </div>

            {/* Health Metrics */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">CPU</span>
                <span className={`text-sm font-medium ${getHealthColor(service.health.cpu, 'cpu')}`}>
                  {service.health.cpu}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Memory</span>
                <span className={`text-sm font-medium ${getHealthColor(service.health.memory, 'memory')}`}>
                  {service.health.memory}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Requests/min</span>
                <span className="text-sm font-medium text-gray-900">{service.health.requests}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Errors</span>
                <span className={`text-sm font-medium ${getHealthColor(service.health.errors, 'errors')}`}>
                  {service.health.errors}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Latency</span>
                <span className="text-sm font-medium text-gray-900">{service.health.latency}ms</span>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 flex space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  restartService.mutate(service.name);
                }}
                className="flex-1 px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
              >
                Restart
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openLogsViewer(service.name);
                }}
                className="flex-1 px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
              >
                Logs
              </button>
            </div>
          </div>
        ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoadingServices && !servicesError && services.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No services found</h3>
          <p className="text-gray-600">No service health data is available at the moment.</p>
        </div>
      )}

      {/* Service Details Modal */}
      {selectedService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{selectedService.name}</h3>
                <p className="text-gray-600">{selectedService.endpoint}</p>
              </div>
              <button
                onClick={() => setSelectedService(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Configuration */}
            <div className="space-y-6">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Configuration</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Version</span>
                    <span className="text-sm font-medium">{selectedService.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Endpoint</span>
                    <span className="text-sm font-medium font-mono">{selectedService.endpoint}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Last Health Check</span>
                    <span className="text-sm font-medium">
                      {new Date(selectedService.lastChecked).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Dependencies */}
              {selectedService.dependencies.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Dependencies</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedService.dependencies.map((dep) => (
                      <span
                        key={dep}
                        className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                      >
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Scaling */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Scaling</h4>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">Replicas:</span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => scaleService.mutate({ serviceName: selectedService.name, replicas: 1 })}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      1
                    </button>
                    <button
                      onClick={() => scaleService.mutate({ serviceName: selectedService.name, replicas: 3 })}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      3
                    </button>
                    <button
                      onClick={() => scaleService.mutate({ serviceName: selectedService.name, replicas: 5 })}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      5
                    </button>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    restartService.mutate(selectedService.name);
                    setSelectedService(null);
                  }}
                  className="flex-1 px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                >
                  Restart Service
                </button>
                <button 
                  onClick={() => {
                    setSelectedService(null);
                    openLogsViewer(selectedService.name);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                  View Logs
                </button>
                <button className="flex-1 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">
                  Stop Service
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Logs Viewer Modal */}
      {showLogs && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{logsService} Logs</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Showing {filteredLogs.length} of {logs.length} log entries
                </p>
              </div>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Filters */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-5 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
                  <select
                    value={logFilters.level}
                    onChange={(e) => setLogFilters(prev => ({ ...prev, level: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
                  >
                    <option value="all">All Levels</option>
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                  <input
                    type="text"
                    value={logFilters.search}
                    onChange={(e) => setLogFilters(prev => ({ ...prev, search: e.target.value }))}
                    placeholder="Search logs..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={logFilters.dateRange.start}
                    onChange={(e) => setLogFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, start: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={logFilters.dateRange.end}
                    onChange={(e) => setLogFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, end: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-end space-x-2">
                  <button
                    onClick={() => fetchLogs(logsService)}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => {
                      setLogFilters({
                        level: 'all',
                        search: '',
                        dateRange: {
                          start: format(new Date(Date.now() - 24 * 60 * 60 * 1000), 'yyyy-MM-dd\'T\'HH:mm'),
                          end: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm')
                        }
                      });
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Actions Bar */}
              <div className="flex justify-between items-center mt-4 pt-4 border-t">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={autoRefresh}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                      className="rounded border-gray-300 text-weed-green-600 focus:ring-weed-green-500"
                    />
                    <span className="text-sm text-gray-700">Auto-refresh (5s)</span>
                  </label>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => fetchLogs(logsService)}
                    className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
                  >
                    <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                  </button>
                  <button
                    onClick={exportLogs}
                    className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
                  >
                    <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Export
                  </button>
                </div>
              </div>
            </div>

            {/* Logs List */}
            <div className="flex-1 overflow-y-auto bg-gray-900 rounded-lg p-4">
              {isLoadingLogs ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                </div>
              ) : filteredLogs.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  No logs found matching filters
                </div>
              ) : (
                <div className="space-y-1 font-mono text-sm">
                  {filteredLogs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start space-x-3 p-2 hover:bg-gray-800 rounded"
                    >
                      <span className="text-gray-500 text-xs whitespace-nowrap">
                        {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLogLevelColor(log.level)}`}>
                        {log.level.toUpperCase()}
                      </span>
                      <span className="text-gray-300 flex-1">
                        {log.message}
                        {log.metadata && (
                          <span className="text-gray-500 ml-2">
                            {JSON.stringify(log.metadata)}
                          </span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer Stats */}
            <div className="mt-4 pt-4 border-t flex justify-between text-sm text-gray-600">
              <div className="flex space-x-4">
                <span>Total: {logs.length}</span>
                <span>Filtered: {filteredLogs.length}</span>
                {logs.length > 0 && (
                  <>
                    <span className="text-red-600">
                      Errors: {logs.filter(l => l.level === 'error' || l.level === 'critical').length}
                    </span>
                    <span className="text-yellow-600">
                      Warnings: {logs.filter(l => l.level === 'warning').length}
                    </span>
                  </>
                )}
              </div>
              <div>
                Last updated: {format(new Date(), 'HH:mm:ss')}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}