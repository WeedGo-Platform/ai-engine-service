import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, RefreshCw, BarChart3, CheckCircle, XCircle, AlertCircle, Clock, Database, TrendingUp, Store, FileText, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

interface CRSARecord {
  license_number: string;
  municipality: string;
  store_name: string;
  address: string;
  status: string;
  website: string;
  last_updated: string;
}

interface SyncStats {
  total_records: number;
  active_stores: number;
  authorized_stores: number;
  in_progress_stores: number;
  public_notice_stores: number;
  cancelled_stores: number;
  linked_tenants: number;
  last_sync: string;
  sync_history: Array<{
    timestamp: string;
    status: string;
    records_processed: number;
    duration_seconds: number;
  }>;
}

const CRSAManagement: React.FC = () => {
  const { t } = useTranslation('common');
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'import' | 'sync' | 'statistics'>('statistics');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [previewData, setPreviewData] = useState<string[][] | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [municipalityFilter, setMunicipalityFilter] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Fetch CRSA statistics
  const { data: stats, isLoading: statsLoading } = useQuery<SyncStats>({
    queryKey: ['crsa-stats'],
    queryFn: async () => {
      const response = await fetch('/api/crsa/sync/stats');
      if (!response.ok) throw new Error('Failed to fetch CRSA statistics');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch recent CRSA records for preview
  const { data: records, isLoading: recordsLoading } = useQuery<CRSARecord[]>({
    queryKey: ['crsa-records', searchTerm, statusFilter, municipalityFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: '100',
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status_filter: statusFilter }),
        ...(municipalityFilter && { municipality_filter: municipalityFilter }),
      });
      const response = await fetch(`/api/crsa/records?${params}`);
      if (!response.ok) throw new Error('Failed to fetch CRSA records');
      return response.json();
    },
  });

  // Manual sync mutation
  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/crsa/sync/manual', {
        method: 'POST',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to trigger sync');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('CRSA sync completed successfully');
      queryClient.invalidateQueries({ queryKey: ['crsa-stats'] });
      queryClient.invalidateQueries({ queryKey: ['crsa-records'] });
    },
    onError: (error: Error) => {
      toast.error(`Sync failed: ${error.message}`);
    },
  });

  // CSV upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/crsa/upload-csv', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload CSV');
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`CSV imported successfully: ${data.records_imported} records processed`);
      queryClient.invalidateQueries({ queryKey: ['crsa-stats'] });
      queryClient.invalidateQueries({ queryKey: ['crsa-records'] });
      setSelectedFile(null);
      setPreviewData(null);
    },
    onError: (error: Error) => {
      toast.error(`Upload failed: ${error.message}`);
    },
  });

  // File upload handlers
  const handleFileSelect = useCallback((file: File) => {
    if (!file.name.endsWith('.csv')) {
      toast.error('Please select a CSV file');
      return;
    }

    setSelectedFile(file);

    // Preview first few rows
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').slice(0, 6); // Header + 5 rows
      const parsed = lines.map(line => line.split(',').map(cell => cell.trim()));
      setPreviewData(parsed);
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">CRSA Management</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Manage Ontario Cannabis Retail Store Authorization (CRSA) data
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('statistics')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'statistics'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <BarChart3 className="inline-block h-5 w-5 mr-2" />
            Statistics
          </button>
          <button
            onClick={() => setActiveTab('sync')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'sync'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <RefreshCw className="inline-block h-5 w-5 mr-2" />
            Sync
          </button>
          <button
            onClick={() => setActiveTab('import')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'import'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Upload className="inline-block h-5 w-5 mr-2" />
            Import
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <Database className="h-10 w-10 text-primary-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Records</p>
                  <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
                    {statsLoading ? '...' : stats?.total_records || 0}
                  </p>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <CheckCircle className="h-10 w-10 text-green-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Authorized</p>
                  <p className="mt-1 text-2xl font-bold text-green-600 dark:text-green-400">
                    {statsLoading ? '...' : stats?.authorized_stores || 0}
                  </p>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <Clock className="h-10 w-10 text-yellow-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">In Progress</p>
                  <p className="mt-1 text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                    {statsLoading ? '...' : stats?.in_progress_stores || 0}
                  </p>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <AlertCircle className="h-10 w-10 text-blue-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Public Notice</p>
                  <p className="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {statsLoading ? '...' : stats?.public_notice_stores || 0}
                  </p>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <XCircle className="h-10 w-10 text-red-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Cancelled</p>
                  <p className="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">
                    {statsLoading ? '...' : stats?.cancelled_stores || 0}
                  </p>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col items-center justify-center text-center">
                  <TrendingUp className="h-10 w-10 text-purple-500 mb-2" />
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Linked Tenants</p>
                  <p className="mt-1 text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {statsLoading ? '...' : stats?.linked_tenants || 0}
                  </p>
                </div>
              </div>
            </div>

            {/* Last Sync Info */}
            {stats?.last_sync && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                  <Clock className="h-4 w-4" />
                  <span>Last synced: {new Date(stats.last_sync).toLocaleString()}</span>
                </div>
              </div>
            )}

            {/* Recent Records Table */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent CRSA Records</h3>
                
                {/* Search and Filters */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <input
                      type="text"
                      placeholder="Search by license, name, address..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      <option value="">All Statuses</option>
                      <option value="Authorized to Open">Authorized to Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Public Notice">Public Notice</option>
                      <option value="Cancelled">Cancelled</option>
                    </select>
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="Filter by municipality..."
                      value={municipalityFilter}
                      onChange={(e) => setMunicipalityFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0 z-10">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                          onClick={() => {
                            if (sortColumn === 'license_number') {
                              setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setSortColumn('license_number');
                              setSortDirection('asc');
                            }
                          }}>
                        License Number {sortColumn === 'license_number' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                          onClick={() => {
                            if (sortColumn === 'store_name') {
                              setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setSortColumn('store_name');
                              setSortDirection('asc');
                            }
                          }}>
                        Store Name {sortColumn === 'store_name' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                          onClick={() => {
                            if (sortColumn === 'municipality') {
                              setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setSortColumn('municipality');
                              setSortDirection('asc');
                            }
                          }}>
                        Municipality {sortColumn === 'municipality' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                          onClick={() => {
                            if (sortColumn === 'status') {
                              setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setSortColumn('status');
                              setSortDirection('asc');
                            }
                          }}>
                        Status {sortColumn === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Website
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Last Updated
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {recordsLoading ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                          Loading...
                        </td>
                      </tr>
                    ) : records && records.length > 0 ? (
                      (() => {
                        const sortedRecords = [...records];
                        if (sortColumn) {
                          sortedRecords.sort((a, b) => {
                            let aVal = a[sortColumn as keyof CRSARecord] || '';
                            let bVal = b[sortColumn as keyof CRSARecord] || '';
                            
                            if (typeof aVal === 'string' && typeof bVal === 'string') {
                              return sortDirection === 'asc' 
                                ? aVal.localeCompare(bVal)
                                : bVal.localeCompare(aVal);
                            }
                            return 0;
                          });
                        }
                        return sortedRecords.map((record) => (
                        <tr key={record.license_number} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                            {record.license_number}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                            {record.store_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {record.municipality}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                            {record.address}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              record.status.toLowerCase().includes('authorized')
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                            }`}>
                              {record.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                            {record.website ? (
                              <a href={record.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                                {record.website.replace(/^https?:\/\//, '').replace(/\/$/, '').substring(0, 30)}
                              </a>
                            ) : (
                              <span className="text-gray-400 italic">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {new Date(record.last_updated).toLocaleDateString()}
                          </td>
                        </tr>
                      ));
                      })()
                    ) : (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                          No records found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sync History */}
            {stats?.sync_history && stats.sync_history.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Sync History</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Records
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Duration
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {stats.sync_history.map((sync, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                            {new Date(sync.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              sync.status === 'success'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                            }`}>
                              {sync.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {sync.records_processed}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {sync.duration_seconds}s
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sync Tab */}
        {activeTab === 'sync' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Manual Sync</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Trigger a manual sync to download the latest CRSA data from the AGCO website. This process will:
              </p>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-2 mb-6">
                <li>Download the latest CRSA data from AGCO</li>
                <li>Parse and validate the CSV data</li>
                <li>Update the database with new/changed records</li>
                <li>Update sync statistics</li>
              </ul>

              <button
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
                className="flex items-center justify-center px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
              >
                {syncMutation.isPending ? (
                  <>
                    <RefreshCw className="animate-spin h-5 w-5 mr-2" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-5 w-5 mr-2" />
                    Run Manual Sync
                  </>
                )}
              </button>

              {stats?.last_sync && (
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Calendar className="h-4 w-4 mr-2" />
                    <span>Last sync: {new Date(stats.last_sync).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Info Alert */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300">Automatic Sync Schedule</h3>
                  <p className="mt-1 text-sm text-blue-700 dark:text-blue-400">
                    The system automatically syncs CRSA data daily at 3:00 AM EST. Manual sync is only needed if you require immediate updates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Import Tab */}
        {activeTab === 'import' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Import CSV File</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Upload a CSV file to manually update the CRSA database. The file must contain the following columns:
              </p>
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 mb-6">
                <code className="text-xs text-gray-700 dark:text-gray-300">
                  License Number, Municipality or First Nation, Store Name, Address, Store Application Status, Website
                </code>
              </div>

              {/* File Upload Dropzone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  isDragging
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}
              >
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-4 text-sm font-medium text-gray-900 dark:text-white">
                  Drop CSV file here or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  CSV files only, max 10MB
                </p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileInputChange}
                  className="hidden"
                  id="csv-upload"
                />
                <label
                  htmlFor="csv-upload"
                  className="mt-4 inline-block px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 cursor-pointer"
                >
                  Select File
                </label>
              </div>

              {/* File Preview */}
              {selectedFile && previewData && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                      <FileText className="h-4 w-4 mr-2" />
                      <span className="font-medium">{selectedFile.name}</span>
                      <span className="ml-2 text-gray-500">({(selectedFile.size / 1024).toFixed(2)} KB)</span>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        setPreviewData(null);
                      }}
                      className="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
                    >
                      Remove
                    </button>
                  </div>

                  {/* Preview Table */}
                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                          <tr>
                            {previewData[0]?.map((header, idx) => (
                              <th
                                key={idx}
                                className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase"
                              >
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {previewData.slice(1, 6).map((row, rowIdx) => (
                            <tr key={rowIdx}>
                              {row.map((cell, cellIdx) => (
                                <td
                                  key={cellIdx}
                                  className="px-4 py-2 text-sm text-gray-900 dark:text-gray-300 whitespace-nowrap"
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Import Button */}
                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
                      disabled={uploadMutation.isPending}
                      className="flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
                    >
                      {uploadMutation.isPending ? (
                        <>
                          <RefreshCw className="animate-spin h-5 w-5 mr-2" />
                          Importing...
                        </>
                      ) : (
                        <>
                          <Upload className="h-5 w-5 mr-2" />
                          Import Data
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Warning Alert */}
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Important</h3>
                  <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-400">
                    Importing a CSV file will update existing records and add new ones. This operation cannot be undone. 
                    Make sure your CSV file is properly formatted before importing.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CRSAManagement;
