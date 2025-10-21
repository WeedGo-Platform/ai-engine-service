import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Database, Server, Table, Trash2, Edit, Eye, Plus,
  RefreshCw, Search, AlertTriangle, Download, Upload,
  ChevronLeft, ChevronRight, Filter, Settings,
  Activity, HardDrive, Cpu, Info, X, Check, Code, Layers
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getAuthStorage, getStorageKey } from '../config/auth.config';
import { getApiEndpoint } from '../config/app.config';
import toast from 'react-hot-toast';
import { confirmToastAsync } from '../components/ConfirmToast';

interface TableInfo {
  name: string;
  type: string;
  comment?: string;
  size: string;
  column_count: number;
  row_count: number;
}

interface ColumnInfo {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default?: string;
  character_maximum_length?: number;
  numeric_precision?: number;
  numeric_scale?: number;
}

interface ConnectionInfo {
  host: string;
  port: number;
  database: string;
  user: string;
  version: string;
  size: string;
  active_connections: number;
  max_connections: number;
}

export default function DatabaseManagement() {
  const { t } = useTranslation(['database', 'common', 'errors']);
  const navigate = useNavigate();
  const { user, isSuperAdmin } = useAuth();
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any[]>([]);
  const [tableSchema, setTableSchema] = useState<ColumnInfo[]>([]);
  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [tableSearchTerm, setTableSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const [pageSize] = useState(50);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState<'add' | 'edit' | 'delete' | 'truncate' | 'query' | null>(null);
  const [editingRow, setEditingRow] = useState<any>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [customQuery, setCustomQuery] = useState('');
  const [queryResult, setQueryResult] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'data' | 'schema' | 'query'>('data');

  // Debounced search effect
  useEffect(() => {
    if (!selectedTable || !searchTerm) return;
    
    const timer = setTimeout(() => {
      fetchTableData(selectedTable, 1);
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm]); // Re-run when searchTerm changes

  // Get auth token
  const getAuthToken = () => {
    const storage = getAuthStorage();
    return storage.getItem(getStorageKey('access_token'));
  };

  // Check if user is super admin
  useEffect(() => {
    if (!isSuperAdmin()) {
      navigate('/dashboard');
    }
  }, [isSuperAdmin, navigate]);

  // Fetch connection info
  useEffect(() => {
    fetchConnectionInfo();
    fetchTables();
  }, []);

  const fetchConnectionInfo = async () => {
    try {
      const response = await fetch(getApiEndpoint('/database/connection-info'), {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnectionInfo(data.connection_info);
      }
    } catch (error) {
      console.error('Error fetching connection info:', error);
    }
  };

  const fetchTables = async () => {
    setLoading(true);
    try {
      const response = await fetch(getApiEndpoint('/database/tables'), {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTables(data.tables);
      }
    } catch (error) {
      console.error('Error fetching tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTableData = async (tableName: string, page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });

      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await fetch(
        getApiEndpoint(`/database/tables/${tableName}/data?${params}`),
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTableData(data.data);
        setTotalPages(data.pagination.total_pages);
        setTotalRows(data.pagination.total_count);
        setCurrentPage(data.pagination.page);
      }
    } catch (error) {
      console.error('Error fetching table data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTableSchema = async (tableName: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        getApiEndpoint(`/database/tables/${tableName}/schema`),
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTableSchema(data.columns);
      }
    } catch (error) {
      console.error('Error fetching table schema:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    setCurrentPage(1);
    setSearchTerm('');
    setActiveTab('data');
    fetchTableData(tableName, 1);
    fetchTableSchema(tableName);
  };

  const handleAddRow = async () => {
    if (!selectedTable) return;

    try {
      const response = await fetch(
        getApiEndpoint(`/database/tables/${selectedTable}/data`),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        }
      );

      if (response.ok) {
        setShowModal(false);
        setFormData({});
        fetchTableData(selectedTable, currentPage);
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error adding row:', error);
      alert(t('database:errors.addRow'));
    }
  };

  const handleUpdateRow = async () => {
    if (!selectedTable || !editingRow) return;

    try {
      // Extract primary key or unique identifier
      const whereConditions: Record<string, any> = {};
      if (editingRow.id) {
        whereConditions.id = editingRow.id;
      } else {
        // Use the first column as identifier if no id
        const firstKey = Object.keys(editingRow)[0];
        whereConditions[firstKey] = editingRow[firstKey];
      }

      const response = await fetch(
        getApiEndpoint(`/database/tables/${selectedTable}/data`),
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            where_conditions: whereConditions,
            update_data: formData
          })
        }
      );

      if (response.ok) {
        setShowModal(false);
        setFormData({});
        setEditingRow(null);
        fetchTableData(selectedTable, currentPage);
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating row:', error);
      alert(t('database:errors.updateRow'));
    }
  };

  const handleDeleteRow = async (row: any) => {
    if (!selectedTable) return;

    const confirmed = await confirmToastAsync(t('database:confirm.deleteRow'));
    if (!confirmed) return;

    try {
      const whereConditions: Record<string, any> = {};
      if (row.id) {
        whereConditions.id = row.id;
      } else {
        const firstKey = Object.keys(row)[0];
        whereConditions[firstKey] = row[firstKey];
      }

      const response = await fetch(
        getApiEndpoint(`/database/tables/${selectedTable}/data`),
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(whereConditions)
        }
      );

      if (response.ok) {
        fetchTableData(selectedTable, currentPage);
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting row:', error);
      alert(t('database:errors.deleteRow'));
    }
  };

  const handleTruncateTable = async () => {
    if (!selectedTable) return;

    const confirmed = await confirmToastAsync(t('database:confirm.truncateTable', { table: selectedTable }));
    if (!confirmed) return;

    try {
      const response = await fetch(
        getApiEndpoint(`/database/tables/${selectedTable}/truncate`),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ cascade: true })
        }
      );

      if (response.ok) {
        setShowModal(false);
        fetchTableData(selectedTable, 1);
        fetchTables();
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error truncating table:', error);
      alert(t('database:errors.truncateTable'));
    }
  };

  const handleDropTable = async () => {
    if (!selectedTable) return;

    try {
      const response = await fetch(
        getApiEndpoint(`/database/tables/${selectedTable}/drop`),
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ cascade: true })
        }
      );

      if (response.ok) {
        setShowModal(false);
        setSelectedTable(null);
        setTableData([]);
        setTableSchema([]);
        fetchTables();
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error dropping table:', error);
      alert(t('database:errors.dropTable'));
    }
  };

  const handleExecuteQuery = async () => {
    if (!customQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(
        getApiEndpoint('/database/query'),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ query: customQuery })
        }
      );

      if (response.ok) {
        const data = await response.json();
        setQueryResult(data.data);
      } else {
        const error = await response.json();
        toast.error(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error executing query:', error);
      alert(t('database:errors.executeQuery'));
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: any) => {
    if (value === null) return <span className="text-gray-400 dark:text-gray-500">NULL</span>;
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const getDataTypeColor = (dataType: string) => {
    if (dataType.includes('int')) return 'text-blue-600 dark:text-blue-400';
    if (dataType.includes('varchar') || dataType.includes('text')) return 'text-green-600 dark:text-green-400';
    if (dataType.includes('bool')) return 'text-purple-600 dark:text-purple-400';
    if (dataType.includes('timestamp') || dataType.includes('date')) return 'text-orange-600 dark:text-orange-400';
    if (dataType.includes('uuid')) return 'text-pink-600 dark:text-pink-400';
    if (dataType.includes('json')) return 'text-indigo-600 dark:text-indigo-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div className="p-3 sm:p-4 lg:p-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2 sm:gap-3 transition-colors">
            <Database className="h-6 w-6 sm:h-7 sm:w-7 lg:h-8 lg:w-8 text-primary-600 dark:text-primary-400" />
            {t('database:titles.main')}
          </h1>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-1 sm:mt-2 transition-colors">
            {t('database:descriptions.main')}
          </p>
        </div>

        {/* Connection Info */}
        {connectionInfo && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 mb-4 sm:mb-6 border border-gray-200 dark:border-gray-700 transition-colors">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3 sm:gap-4 lg:gap-6">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                  <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                    {connectionInfo.host}:{connectionInfo.port}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                  <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                    {connectionInfo.database} ({connectionInfo.size})
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                  <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                    {connectionInfo.active_connections}/{connectionInfo.max_connections} {t('database:connection.connections')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                  <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                    PostgreSQL {connectionInfo.version.split(' ')[1]}
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  fetchConnectionInfo();
                  fetchTables();
                }}
                className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all active:scale-95 touch-manipulation"
              >
                <RefreshCw className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
            </div>
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
          {/* Tables List */}
          <div className="w-full lg:w-80 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 max-h-96 lg:max-h-[calc(100vh-300px)] overflow-hidden border border-gray-200 dark:border-gray-700 transition-colors">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{t('database:titles.databaseObjects')}</h2>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <div>{tables.filter(t => t.type === 'BASE TABLE').length} {t('database:table.tables')}</div>
                <div>{tables.filter(t => t.type === 'VIEW').length} {t('database:table.views')}</div>
              </div>
            </div>

            {/* Add search bar for tables */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                value={tableSearchTerm}
                onChange={(e) => setTableSearchTerm(e.target.value)}
                placeholder={t('database:placeholders.filterTables')}
                className="w-full pl-10 pr-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-sm transition-colors"
              />
              {tableSearchTerm && (
                <button
                  onClick={() => setTableSearchTerm('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-full transition-colors"
                >
                  <X className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                </button>
              )}
            </div>

            <div className="space-y-1 max-h-[calc(100vh-380px)] overflow-y-auto">
              {/* Group tables first */}
              {tables.filter(t => t.type === 'BASE TABLE' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length > 0 && (
                <>
                  <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase px-3 py-1 sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    {t('database:table.tables')} ({tables.filter(t => t.type === 'BASE TABLE' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length})
                  </div>
                  {tables
                    .filter(t => t.type === 'BASE TABLE')
                    .filter(t => !tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))
                    .map((table, index) => (
                    <button
                      key={`table-${table.name}-${index}`}
                      onClick={() => handleTableSelect(table.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-all active:scale-95 touch-manipulation ${
                        selectedTable === table.name
                          ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 border border-primary-200 dark:border-primary-700'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <Table className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                          <span className="font-medium text-sm truncate">{table.name}</span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-2 flex-shrink-0">
                          {table.row_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {table.column_count} {t('database:table.columns')}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{table.size}</span>
                      </div>
                    </button>
                  ))}
                </>
              )}

              {/* Then group views */}
              {tables.filter(t => t.type === 'VIEW' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length > 0 && (
                <>
                  <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase px-3 py-1 mt-3 sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    {t('database:table.views')} ({tables.filter(t => t.type === 'VIEW' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length})
                  </div>
                  {tables
                    .filter(t => t.type === 'VIEW')
                    .filter(t => !tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))
                    .map((table, index) => (
                    <button
                      key={`view-${table.name}-${index}`}
                      onClick={() => handleTableSelect(table.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-all active:scale-95 touch-manipulation ${
                        selectedTable === table.name
                          ? 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 border border-purple-200 dark:border-purple-700'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <Layers className="h-4 w-4 text-purple-600 dark:text-purple-400 flex-shrink-0" />
                          <span className="font-medium text-sm truncate">{table.name}</span>
                          <span className="text-xs bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded flex-shrink-0">VIEW</span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-2 flex-shrink-0">
                          {table.row_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {table.column_count} {t('database:table.columns')}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{table.size}</span>
                      </div>
                    </button>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Table Content */}
          <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700 transition-colors">
            {selectedTable ? (
              <>
                {/* Table Header */}
                <div className="border-b border-gray-200 dark:border-gray-700 p-3 sm:p-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <h2 className="text-base sm:text-lg lg:text-xl font-semibold text-gray-900 dark:text-white">
                        {selectedTable}
                      </h2>
                      {tables.find(t => t.name === selectedTable)?.type === 'VIEW' && (
                        <span className="text-xs bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 px-2 py-1 rounded font-medium">VIEW</span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                      {/* Tab Buttons */}
                      <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 w-full sm:w-auto">
                        <button
                          onClick={() => setActiveTab('data')}
                          className={`flex-1 sm:flex-initial px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all active:scale-95 touch-manipulation ${
                            activeTab === 'data'
                              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                          }`}
                        >
                          {t('database:tabs.data')}
                        </button>
                        <button
                          onClick={() => setActiveTab('schema')}
                          className={`flex-1 sm:flex-initial px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all active:scale-95 touch-manipulation ${
                            activeTab === 'schema'
                              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                          }`}
                        >
                          {t('database:tabs.schema')}
                        </button>
                        <button
                          onClick={() => setActiveTab('query')}
                          className={`flex-1 sm:flex-initial px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all active:scale-95 touch-manipulation ${
                            activeTab === 'query'
                              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                          }`}
                        >
                          {t('database:tabs.query')}
                        </button>
                      </div>

                      <div className="hidden sm:block h-6 w-px bg-gray-300 dark:bg-gray-600" />

                      {/* Action Buttons - Hide some for views */}
                      {tables.find(t => t.name === selectedTable)?.type !== 'VIEW' && (
                        <>
                          <button
                            onClick={() => {
                              setModalType('add');
                              setFormData({});
                              setShowModal(true);
                            }}
                            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-all active:scale-95 touch-manipulation text-xs sm:text-sm"
                          >
                            <Plus className="h-3 sm:h-4 w-3 sm:w-4" />
                            <span className="hidden sm:inline">{t('database:actions.addRow')}</span>
                            <span className="sm:hidden">{t('database:actions.add')}</span>
                          </button>
                          <button
                            onClick={() => {
                              setModalType('truncate');
                              setShowModal(true);
                            }}
                            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-orange-600 dark:bg-orange-500 text-white rounded-lg hover:bg-orange-700 dark:hover:bg-orange-600 transition-all active:scale-95 touch-manipulation text-xs sm:text-sm"
                          >
                            <Trash2 className="h-3 sm:h-4 w-3 sm:w-4" />
                            <span className="hidden sm:inline">{t('database:actions.truncate')}</span>
                            <span className="sm:hidden">{t('database:actions.clear')}</span>
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => {
                          setModalType('drop');
                          setShowModal(true);
                        }}
                        className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 transition-all active:scale-95 touch-manipulation text-xs sm:text-sm"
                      >
                        <AlertTriangle className="h-3 sm:h-4 w-3 sm:w-4" />
                        <span className="hidden sm:inline">
                          {tables.find(t => t.name === selectedTable)?.type === 'VIEW' ? t('database:actions.dropView') : t('database:actions.dropTable')}
                        </span>
                        <span className="sm:hidden">{t('database:actions.drop')}</span>
                      </button>
                      <button
                        onClick={() => fetchTableData(selectedTable, currentPage)}
                        className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all active:scale-95 touch-manipulation"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Search and Stats */}
                  {activeTab === 'data' && (
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mt-3 sm:mt-4 gap-3">
                      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 w-full sm:w-auto">
                        <div className="relative w-full sm:w-auto">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500" />
                          <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                fetchTableData(selectedTable, 1);
                              }
                            }}
                            placeholder={t('database:placeholders.searchTable')}
                            className="w-full sm:w-auto pl-10 pr-20 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-sm transition-colors"
                          />
                          {searchTerm && (
                            <button
                              onClick={() => setSearchTerm('')}
                              className="absolute right-10 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-full transition-colors"
                              title={t('database:actions.clearSearch')}
                            >
                              <X className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                            </button>
                          )}
                          <button
                            onClick={() => fetchTableData(selectedTable, 1)}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 px-2 py-1 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded transition-colors"
                            title={t('database:actions.search')}
                          >
                            <Search className="h-4 w-4" />
                          </button>
                        </div>
                        <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                          {totalRows.toLocaleString()} {t('database:table.totalRows')}
                        </span>
                      </div>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              if (currentPage > 1) {
                                fetchTableData(selectedTable, currentPage - 1);
                              }
                            }}
                            disabled={currentPage === 1}
                            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-700 dark:text-gray-300"
                          >
                            <ChevronLeft className="h-5 w-5" />
                          </button>
                          <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                            {t('database:pagination.page')} {currentPage} {t('database:pagination.of')} {totalPages}
                          </span>
                          <button
                            onClick={() => {
                              if (currentPage < totalPages) {
                                fetchTableData(selectedTable, currentPage + 1);
                              }
                            }}
                            disabled={currentPage === totalPages}
                            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-700 dark:text-gray-300"
                          >
                            <ChevronRight className="h-5 w-5" />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Table Content Area */}
                <div className="p-3 sm:p-4">
                  {loading ? (
                    <div className="flex items-center justify-center h-64">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
                    </div>
                  ) : (
                    <>
                      {/* Data Tab */}
                      {activeTab === 'data' && (
                        <div className="overflow-x-auto -mx-3 sm:-mx-4">
                          <div className="inline-block min-w-full align-middle">
                            <div className="overflow-hidden border-b border-gray-200 dark:border-gray-700 sm:rounded-lg">
                              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700/50">
                              <tr className="border-b border-gray-200 dark:border-gray-700">
                                {tableData.length > 0 &&
                                  Object.keys(tableData[0]).map(key => (
                                    <th
                                      key={key}
                                      className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap"
                                    >
                                      {key}
                                    </th>
                                  ))}
                                <th className="px-2 sm:px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider sticky right-0 bg-gray-50 dark:bg-gray-700/50">
                                  {t('database:messages.actions')}
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                              {tableData.map((row, rowIndex) => (
                                <tr key={rowIndex} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                  {Object.values(row).map((value, colIndex) => (
                                    <td key={colIndex} className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                                      <div className="max-w-xs truncate" title={String(value)}>
                                        {formatValue(value)}
                                      </div>
                                    </td>
                                  ))}
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-right sticky right-0 bg-white dark:bg-gray-800">
                                    <div className="flex justify-end gap-1 sm:gap-2">
                                      <button
                                        onClick={() => {
                                          setEditingRow(row);
                                          setFormData(row);
                                          setModalType('edit');
                                          setShowModal(true);
                                        }}
                                        className="p-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-all active:scale-95 touch-manipulation"
                                      >
                                        <Edit className="h-3 sm:h-4 w-3 sm:w-4" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteRow(row)}
                                        className="p-1 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-all active:scale-95 touch-manipulation"
                                      >
                                        <Trash2 className="h-3 sm:h-4 w-3 sm:w-4" />
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                              </table>
                            </div>
                          </div>

                          {tableData.length === 0 && (
                            <div className="text-center py-8 sm:py-12 text-gray-500 dark:text-gray-400 text-sm">
                              {t('database:messages.noData')}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Schema Tab */}
                      {activeTab === 'schema' && (
                        <div className="overflow-x-auto -mx-3 sm:-mx-4">
                          <div className="inline-block min-w-full align-middle">
                            <div className="overflow-hidden border-b border-gray-200 dark:border-gray-700 sm:rounded-lg">
                              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700/50">
                              <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                  {t('database:schema.columnName')}
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                  {t('database:schema.dataType')}
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                  {t('database:schema.nullable')}
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">
                                  {t('database:schema.default')}
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">
                                  {t('database:schema.maxLength')}
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                              {tableSchema.map(column => (
                                <tr key={column.column_name} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-gray-900 dark:text-gray-100">
                                    {column.column_name}
                                  </td>
                                  <td className={`px-2 sm:px-3 py-2 text-xs sm:text-sm font-mono ${getDataTypeColor(column.data_type)}`}>
                                    {column.data_type}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm">
                                    {column.is_nullable === 'YES' ? (
                                      <span className="text-green-600 dark:text-green-400">✓</span>
                                    ) : (
                                      <span className="text-red-600 dark:text-red-400">✗</span>
                                    )}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 dark:text-gray-300 hidden sm:table-cell">
                                    {column.column_default || '-'}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 dark:text-gray-300 hidden md:table-cell">
                                    {column.character_maximum_length || '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Query Tab */}
                      {activeTab === 'query' && (
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              {t('database:placeholders.sqlQuery')}
                            </label>
                            <textarea
                              value={customQuery}
                              onChange={(e) => setCustomQuery(e.target.value)}
                              placeholder={`SELECT * FROM ${selectedTable} WHERE ...`}
                              className="w-full h-32 sm:h-40 px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 font-mono text-xs sm:text-sm transition-colors"
                            />
                          </div>

                          <button
                            onClick={handleExecuteQuery}
                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-all active:scale-95 touch-manipulation"
                          >
                            <Code className="h-4 w-4" />
                            {t('database:actions.executeQuery')}
                          </button>

                          {queryResult.length > 0 && (
                            <div className="overflow-x-auto -mx-3 sm:-mx-4 border border-gray-200 dark:border-gray-700 rounded-lg mt-4">
                              <div className="inline-block min-w-full align-middle">
                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700/50">
                                  <tr>
                                    {Object.keys(queryResult[0]).map(key => (
                                      <th
                                        key={key}
                                        className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap"
                                      >
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                                  {queryResult.map((row, index) => (
                                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                      {Object.values(row).map((value, colIndex) => (
                                        <td key={colIndex} className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                                          <div className="max-w-xs truncate" title={String(value)}>
                                            {formatValue(value)}
                                          </div>
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-96 text-gray-500 dark:text-gray-400">
                <Table className="h-10 w-10 sm:h-12 sm:w-12 mb-4" />
                <p className="text-base sm:text-lg font-medium">{t('database:descriptions.selectTable')}</p>
                <p className="text-xs sm:text-sm mt-2">{t('database:descriptions.chooseFromList')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] sm:max-h-[80vh] overflow-y-auto border border-gray-200 dark:border-gray-700">
              <div className="p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4 sticky top-0 bg-white dark:bg-gray-800 pb-3 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-base sm:text-lg lg:text-xl font-semibold text-gray-900 dark:text-white">
                    {modalType === 'add' && t('database:titles.addRow')}
                    {modalType === 'edit' && t('database:titles.editRow')}
                    {modalType === 'truncate' && t('database:titles.truncateTable')}
                    {modalType === 'drop' && t('database:titles.dropTable')}
                  </h3>
                  <button
                    onClick={() => {
                      setShowModal(false);
                      setFormData({});
                      setEditingRow(null);
                    }}
                    className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  >
                    <X className="h-5 w-5 sm:h-6 sm:w-6" />
                  </button>
                </div>

                {(modalType === 'truncate' || modalType === 'drop') ? (
                  <div className="space-y-4">
                    <div className="flex items-start sm:items-center gap-3 p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
                      <AlertTriangle className="h-5 sm:h-6 w-5 sm:w-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5 sm:mt-0" />
                      <div>
                        <p className="text-red-900 dark:text-red-200 font-medium text-sm sm:text-base">
                          {t('database:messages.warningCannotUndo')}
                        </p>
                        <p className="text-red-700 dark:text-red-300 text-xs sm:text-sm mt-1">
                          {modalType === 'truncate'
                            ? t('database:messages.truncateWarning', { table: selectedTable })
                            : t('database:messages.dropWarning', { table: selectedTable })}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3">
                      <button
                        onClick={() => setShowModal(false)}
                        className="w-full sm:w-auto px-4 py-2 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 text-sm transition-all active:scale-95 touch-manipulation"
                      >
                        {t('database:actions.cancel')}
                      </button>
                      <button
                        onClick={modalType === 'truncate' ? handleTruncateTable : handleDropTable}
                        className="w-full sm:w-auto px-4 py-2 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 text-sm transition-all active:scale-95 touch-manipulation"
                      >
                        {modalType === 'truncate' ? t('database:titles.truncateTable') : t('database:titles.dropTable')}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                    {tableSchema.map(column => (
                      <div key={column.column_name}>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          {column.column_name}
                          {column.is_nullable === 'NO' && (
                            <span className="text-red-500 dark:text-red-400 ml-1">*</span>
                          )}
                        </label>
                        <input
                          type="text"
                          value={formData[column.column_name] || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            [column.column_name]: e.target.value
                          })}
                          placeholder={column.data_type}
                          className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-sm transition-colors"
                        />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {t('database:messages.type')}: {column.data_type}
                        </span>
                      </div>
                    ))}

                    <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3 pt-4 sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 -mx-6 px-6 pb-0 mt-6">
                      <button
                        onClick={() => {
                          setShowModal(false);
                          setFormData({});
                          setEditingRow(null);
                        }}
                        className="w-full sm:w-auto px-4 py-2 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 text-sm transition-all active:scale-95 touch-manipulation"
                      >
                        {t('database:actions.cancel')}
                      </button>
                      <button
                        onClick={modalType === 'add' ? handleAddRow : handleUpdateRow}
                        className="w-full sm:w-auto px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 text-sm transition-all active:scale-95 touch-manipulation"
                      >
                        {modalType === 'add' ? t('database:actions.addRow') : t('database:actions.updateRow')}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}