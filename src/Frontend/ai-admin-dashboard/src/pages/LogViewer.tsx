import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search, Filter, RefreshCw, Download, X, ChevronDown, ChevronRight,
  AlertCircle, Info, AlertTriangle, XCircle, Calendar, Clock, User,
  Building2, Store, Smartphone, Activity, FileText, Eye, EyeOff
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

// API configuration from environment
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5024';

// Helper function to parse UTC timestamps properly
const parseUTCTimestamp = (timestamp: string): Date => {
  // If timestamp doesn't end with 'Z' (UTC indicator), add it
  // This ensures JavaScript treats it as UTC rather than local time
  const utcTimestamp = timestamp.endsWith('Z') || timestamp.includes('+') || timestamp.includes('-')
    ? timestamp
    : timestamp + 'Z';
  return new Date(utcTimestamp);
};

interface LogEntry {
  _id: string;
  _source: {
    '@timestamp': string;
    level: string;
    logger: string;
    message: string;
    correlation_id?: string;
    tenant_id?: string;
    store_id?: string;
    user_id?: string;
    session_id?: string;
    client_host?: string;
    method?: string;
    path?: string;
    status_code?: number;
    duration_ms?: number;
    service?: string;
    environment?: string;
    module?: string;
    function?: string;
    line?: number;
    exception?: string;
    [key: string]: any;
  };
}

interface FilterState {
  search: string;
  level: string;
  correlationId: string;
  tenantId: string;
  storeId: string;
  userId: string;
  sessionId: string;
  service: string;
  startDate: string;
  endDate: string;
  showAdvanced: boolean;
}

export default function LogViewer() {
  const { t } = useTranslation(['tools', 'common']);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [totalHits, setTotalHits] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(10);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    level: 'all',
    correlationId: '',
    tenantId: '',
    storeId: '',
    userId: '',
    sessionId: '',
    service: '',
    startDate: '',
    endDate: '',
    showAdvanced: false
  });

  // Fetch logs from backend API
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();

      // Add filters as query parameters
      if (filters.search) params.append('search', filters.search);
      if (filters.level && filters.level !== 'all') params.append('level', filters.level);
      if (filters.correlationId) params.append('correlation_id', filters.correlationId);
      if (filters.tenantId) params.append('tenant_id', filters.tenantId);
      if (filters.storeId) params.append('store_id', filters.storeId);
      if (filters.userId) params.append('user_id', filters.userId);
      if (filters.sessionId) params.append('session_id', filters.sessionId);
      if (filters.service) params.append('service', filters.service);

      // Add date filters
      if (filters.startDate) params.append('start_date', new Date(filters.startDate).toISOString());
      if (filters.endDate) params.append('end_date', new Date(filters.endDate).toISOString());

      // Add pagination
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());

      // Generate standard UUID v4 correlation ID for this request
      const correlationId = crypto.randomUUID();

      const response = await fetch(`${API_URL}/api/logs/search?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': correlationId
        }
      });

      if (!response.ok) {
        throw new Error(`Backend API query failed: ${response.statusText}`);
      }

      const data = await response.json();
      setLogs(data.hits);
      setTotalHits(data.total);
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error(t('tools:logs.messages.fetchFailed'));
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize, t]);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchLogs]);

  // Export logs to JSON
  const exportLogs = () => {
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs-${format(new Date(), 'yyyy-MM-dd-HH-mm-ss')}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success(t('tools:logs.messages.exportSuccess'));
  };

  // Get log level badge color
  const getLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'INFO':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'DEBUG':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  // Get log level icon
  const getLevelIcon = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return <XCircle className="h-4 w-4" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4" />;
      case 'INFO':
        return <Info className="h-4 w-4" />;
      case 'DEBUG':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const totalPages = Math.ceil(totalHits / pageSize);

  return (
    <div className="p-6 max-w-full">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('tools:logs.title')}</h1>
        <p className="mt-1 text-sm text-gray-600">
          {t('tools:logs.description')}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('tools:logs.filters.search')}
            </label>
            <div className="relative">
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                placeholder={t('tools:logs.filters.searchPlaceholder')}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Log Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('tools:logs.filters.logLevel')}
            </label>
            <select
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">{t('tools:logs.filters.allLevels')}</option>
              <option value="ERROR">{t('tools:logs.filters.error')}</option>
              <option value="WARNING">{t('tools:logs.filters.warning')}</option>
              <option value="INFO">{t('tools:logs.filters.info')}</option>
              <option value="DEBUG">{t('tools:logs.filters.debug')}</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('tools:logs.filters.timeRange')}
            </label>
            <div className="flex gap-2">
              <input
                type="datetime-local"
                value={filters.startDate}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                className="w-full px-2 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Advanced Filters Toggle */}
        <button
          onClick={() => setFilters({ ...filters, showAdvanced: !filters.showAdvanced })}
          className="flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium mb-2"
        >
          {filters.showAdvanced ? <ChevronDown className="h-4 w-4 mr-1" /> : <ChevronRight className="h-4 w-4 mr-1" />}
          {t('tools:logs.filters.advancedFilters')}
        </button>

        {/* Advanced Filters */}
        {filters.showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Activity className="inline h-4 w-4 mr-1" />
                {t('tools:logs.filters.correlationId')}
              </label>
              <input
                type="text"
                value={filters.correlationId}
                onChange={(e) => setFilters({ ...filters, correlationId: e.target.value })}
                placeholder={t('tools:logs.filters.correlationIdPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Building2 className="inline h-4 w-4 mr-1" />
                {t('tools:logs.filters.tenantId')}
              </label>
              <input
                type="text"
                value={filters.tenantId}
                onChange={(e) => setFilters({ ...filters, tenantId: e.target.value })}
                placeholder={t('tools:logs.filters.tenantIdPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Store className="inline h-4 w-4 mr-1" />
                {t('tools:logs.filters.storeId')}
              </label>
              <input
                type="text"
                value={filters.storeId}
                onChange={(e) => setFilters({ ...filters, storeId: e.target.value })}
                placeholder={t('tools:logs.filters.storeIdPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <User className="inline h-4 w-4 mr-1" />
                {t('tools:logs.filters.userId')}
              </label>
              <input
                type="text"
                value={filters.userId}
                onChange={(e) => setFilters({ ...filters, userId: e.target.value })}
                placeholder={t('tools:logs.filters.userIdPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Smartphone className="inline h-4 w-4 mr-1" />
                {t('tools:logs.filters.sessionId')}
              </label>
              <input
                type="text"
                value={filters.sessionId}
                onChange={(e) => setFilters({ ...filters, sessionId: e.target.value })}
                placeholder={t('tools:logs.filters.sessionIdPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('tools:logs.filters.service')}
              </label>
              <input
                type="text"
                value={filters.service}
                onChange={(e) => setFilters({ ...filters, service: e.target.value })}
                placeholder={t('tools:logs.filters.servicePlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('tools:logs.filters.endDate')}
              </label>
              <input
                type="datetime-local"
                value={filters.endDate}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilters({
                    search: '',
                    level: 'all',
                    correlationId: '',
                    tenantId: '',
                    storeId: '',
                    userId: '',
                    sessionId: '',
                    service: '',
                    startDate: '',
                    endDate: '',
                    showAdvanced: filters.showAdvanced
                  });
                  setPage(1);
                }}
                className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {t('tools:logs.filters.clearAll')}
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              {t('tools:logs.actions.refresh')}
            </button>

            <button
              onClick={exportLogs}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Download className="h-4 w-4" />
              {t('tools:logs.actions.export')}
            </button>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              {t('tools:logs.actions.autoRefresh')}
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                disabled={!autoRefresh}
                className="px-2 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
              >
                <option value={5}>5s</option>
                <option value={10}>10s</option>
                <option value={30}>30s</option>
                <option value={60}>60s</option>
              </select>
            </label>

            <div className="text-sm text-gray-600">
              {totalHits.toLocaleString()} {t('tools:logs.table.totalLogs')}
            </div>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <FileText className="h-12 w-12 mb-2" />
            <p>{t('tools:logs.table.noLogs')}</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.timestamp')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.level')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.serviceLogger')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.message')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.correlationId')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('tools:logs.table.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log._id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-gray-400" />
                          {format(parseUTCTimestamp(log._source['@timestamp']), 'MMM dd, HH:mm:ss.SSS')}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getLevelColor(log._source.level)}`}>
                          {getLevelIcon(log._source.level)}
                          {log._source.level}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div className="max-w-xs">
                          <div className="font-medium truncate">{log._source.service || 'N/A'}</div>
                          <div className="text-xs text-gray-500 truncate">{log._source.logger}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div className="max-w-md truncate">{log._source.message}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs font-mono text-gray-600">
                        {log._source.correlation_id || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="text-primary-600 hover:text-primary-900 flex items-center gap-1"
                        >
                          <Eye className="h-4 w-4" />
                          {t('tools:logs.actions.details')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
              <div className="flex-1 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">
                    {t('tools:logs.pagination.showing', { from: ((page - 1) * pageSize) + 1, to: Math.min(page * pageSize, totalHits), total: totalHits.toLocaleString() })}
                  </span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value={25}>25 {t('tools:logs.pagination.perPage')}</option>
                    <option value={50}>50 {t('tools:logs.pagination.perPage')}</option>
                    <option value={100}>100 {t('tools:logs.pagination.perPage')}</option>
                    <option value={200}>200 {t('tools:logs.pagination.perPage')}</option>
                  </select>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('tools:logs.pagination.previous')}
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-700">
                    {t('tools:logs.pagination.page', { current: page, total: totalPages })}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('tools:logs.pagination.next')}
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setSelectedLog(null)} />

            <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">{t('tools:logs.details.title')}</h3>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Content */}
              <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-8rem)]">
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                    <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium border ${getLevelColor(selectedLog._source.level)}`}>
                      {getLevelIcon(selectedLog._source.level)}
                      {selectedLog._source.level}
                    </span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{selectedLog._source.message}</div>
                      <div className="mt-1 text-xs text-gray-500">
                        {format(parseUTCTimestamp(selectedLog._source['@timestamp']), 'MMM dd, yyyy HH:mm:ss.SSS')}
                      </div>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-4">
                    {selectedLog._source.correlation_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.correlationId')}</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog._source.correlation_id}</dd>
                      </div>
                    )}
                    {selectedLog._source.session_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.sessionId')}</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog._source.session_id}</dd>
                      </div>
                    )}
                    {selectedLog._source.tenant_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.tenantId')}</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog._source.tenant_id}</dd>
                      </div>
                    )}
                    {selectedLog._source.store_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.storeId')}</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog._source.store_id}</dd>
                      </div>
                    )}
                    {selectedLog._source.user_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.userId')}</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog._source.user_id}</dd>
                      </div>
                    )}
                    {selectedLog._source.service && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.service')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.service}</dd>
                      </div>
                    )}
                    {selectedLog._source.environment && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.environment')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.environment}</dd>
                      </div>
                    )}
                    {selectedLog._source.logger && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.logger')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.logger}</dd>
                      </div>
                    )}
                    {selectedLog._source.module && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.module')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.module}</dd>
                      </div>
                    )}
                    {selectedLog._source.function && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.function')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.function}</dd>
                      </div>
                    )}
                    {selectedLog._source.line && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.lineNumber')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.line}</dd>
                      </div>
                    )}
                    {selectedLog._source.duration_ms && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.duration')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.duration_ms}ms</dd>
                      </div>
                    )}
                    {selectedLog._source.status_code && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.statusCode')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.status_code}</dd>
                      </div>
                    )}
                    {selectedLog._source.method && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.method')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.method}</dd>
                      </div>
                    )}
                    {selectedLog._source.path && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.path')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.path}</dd>
                      </div>
                    )}
                    {selectedLog._source.client_host && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('tools:logs.details.clientHost')}</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog._source.client_host}</dd>
                      </div>
                    )}
                  </div>

                  {/* Exception */}
                  {selectedLog._source.exception && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">{t('tools:logs.details.exception')}</dt>
                      <dd className="text-sm text-red-900 bg-red-50 p-3 rounded-lg font-mono whitespace-pre-wrap">
                        {selectedLog._source.exception}
                      </dd>
                    </div>
                  )}

                  {/* Raw JSON */}
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                      {t('tools:logs.details.viewRawJson')}
                    </summary>
                    <pre className="mt-2 p-4 bg-gray-900 text-green-400 rounded-lg overflow-x-auto text-xs">
                      {JSON.stringify(selectedLog._source, null, 2)}
                    </pre>
                  </details>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
                <button
                  onClick={() => {
                    const dataStr = JSON.stringify(selectedLog._source, null, 2);
                    const dataBlob = new Blob([dataStr], { type: 'application/json' });
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `log-${selectedLog._id}.json`;
                    link.click();
                    URL.revokeObjectURL(url);
                    toast.success(t('tools:logs.messages.logExported'));
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  <Download className="inline h-4 w-4 mr-1" />
                  {t('tools:logs.actions.export')}
                </button>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
                >
                  {t('tools:logs.actions.close')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
