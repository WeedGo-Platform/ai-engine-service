import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Database, Server, Table, Trash2, Edit, Eye, Plus,
  RefreshCw, Search, AlertTriangle, Download, Upload,
  ChevronLeft, ChevronRight, Filter, Settings,
  Activity, HardDrive, Cpu, Info, X, Check, Code, Layers
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getAuthStorage, getStorageKey } from '../config/auth.config';

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
      const response = await fetch('http://localhost:5024/api/database/connection-info', {
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
      const response = await fetch('http://localhost:5024/api/database/tables', {
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
        `http://localhost:5024/api/database/tables/${tableName}/data?${params}`,
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
        `http://localhost:5024/api/database/tables/${tableName}/schema`,
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
        `http://localhost:5024/api/database/tables/${selectedTable}/data`,
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error adding row:', error);
      alert('Failed to add row');
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
        `http://localhost:5024/api/database/tables/${selectedTable}/data`,
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating row:', error);
      alert('Failed to update row');
    }
  };

  const handleDeleteRow = async (row: any) => {
    if (!selectedTable) return;

    if (!confirm('Are you sure you want to delete this row?')) return;

    try {
      const whereConditions: Record<string, any> = {};
      if (row.id) {
        whereConditions.id = row.id;
      } else {
        const firstKey = Object.keys(row)[0];
        whereConditions[firstKey] = row[firstKey];
      }

      const response = await fetch(
        `http://localhost:5024/api/database/tables/${selectedTable}/data`,
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting row:', error);
      alert('Failed to delete row');
    }
  };

  const handleTruncateTable = async () => {
    if (!selectedTable) return;

    if (!confirm(`Are you sure you want to TRUNCATE table ${selectedTable}? This will delete ALL rows!`)) return;

    try {
      const response = await fetch(
        `http://localhost:5024/api/database/tables/${selectedTable}/truncate`,
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error truncating table:', error);
      alert('Failed to truncate table');
    }
  };

  const handleDropTable = async () => {
    if (!selectedTable) return;

    try {
      const response = await fetch(
        `http://localhost:5024/api/database/tables/${selectedTable}/drop`,
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error dropping table:', error);
      alert('Failed to drop table');
    }
  };

  const handleExecuteQuery = async () => {
    if (!customQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(
        'http://localhost:5024/api/database/query',
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
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error executing query:', error);
      alert('Failed to execute query');
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: any) => {
    if (value === null) return <span className="text-gray-400">NULL</span>;
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const getDataTypeColor = (dataType: string) => {
    if (dataType.includes('int')) return 'text-blue-600';
    if (dataType.includes('varchar') || dataType.includes('text')) return 'text-green-600';
    if (dataType.includes('bool')) return 'text-purple-600';
    if (dataType.includes('timestamp') || dataType.includes('date')) return 'text-orange-600';
    if (dataType.includes('uuid')) return 'text-pink-600';
    if (dataType.includes('json')) return 'text-indigo-600';
    return 'text-gray-600';
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Database className="h-8 w-8 text-primary-600" />
            Database Management
          </h1>
          <p className="text-gray-600 mt-2">
            Super admin access to database tables and operations
          </p>
        </div>

        {/* Connection Info */}
        {connectionInfo && (
          <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4 mb-4 sm:mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2 sm:gap-4 lg:gap-6">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    {connectionInfo.host}:{connectionInfo.port}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    {connectionInfo.database} ({connectionInfo.size})
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    {connectionInfo.active_connections}/{connectionInfo.max_connections} connections
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    PostgreSQL {connectionInfo.version.split(' ')[1]}
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  fetchConnectionInfo();
                  fetchTables();
                }}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
          {/* Tables List */}
          <div className="w-full lg:w-80 bg-white rounded-lg shadow-sm p-3 sm:p-4 max-h-96 lg:max-h-[calc(100vh-300px)] overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Database Objects</h2>
              <div className="text-xs text-gray-500">
                <div>{tables.filter(t => t.type === 'BASE TABLE').length} tables</div>
                <div>{tables.filter(t => t.type === 'VIEW').length} views</div>
              </div>
            </div>

            {/* Add search bar for tables */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={tableSearchTerm}
                onChange={(e) => setTableSearchTerm(e.target.value)}
                placeholder="Filter tables and views..."
                className="w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
              />
              {tableSearchTerm && (
                <button
                  onClick={() => setTableSearchTerm('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded-full"
                >
                  <X className="h-3 w-3 text-gray-400" />
                </button>
              )}
            </div>

            <div className="space-y-1 max-h-[calc(100vh-380px)] overflow-y-auto">
              {/* Group tables first */}
              {tables.filter(t => t.type === 'BASE TABLE' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length > 0 && (
                <>
                  <div className="text-xs font-semibold text-gray-500 uppercase px-3 py-1 sticky top-0 bg-white border-b">
                    Tables ({tables.filter(t => t.type === 'BASE TABLE' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length})
                  </div>
                  {tables
                    .filter(t => t.type === 'BASE TABLE')
                    .filter(t => !tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))
                    .map((table, index) => (
                    <button
                      key={`table-${table.name}-${index}`}
                      onClick={() => handleTableSelect(table.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        selectedTable === table.name
                          ? 'bg-primary-50 text-primary-700 border border-primary-200'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Table className="h-4 w-4 text-blue-600" />
                          <span className="font-medium text-sm">{table.name}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {table.row_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500">
                          {table.column_count} columns
                        </span>
                        <span className="text-xs text-gray-500">{table.size}</span>
                      </div>
                    </button>
                  ))}
                </>
              )}

              {/* Then group views */}
              {tables.filter(t => t.type === 'VIEW' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length > 0 && (
                <>
                  <div className="text-xs font-semibold text-gray-500 uppercase px-3 py-1 mt-3 sticky top-0 bg-white border-b">
                    Views ({tables.filter(t => t.type === 'VIEW' && (!tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))).length})
                  </div>
                  {tables
                    .filter(t => t.type === 'VIEW')
                    .filter(t => !tableSearchTerm || t.name.toLowerCase().includes(tableSearchTerm.toLowerCase()))
                    .map((table, index) => (
                    <button
                      key={`view-${table.name}-${index}`}
                      onClick={() => handleTableSelect(table.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        selectedTable === table.name
                          ? 'bg-purple-50 text-purple-700 border border-purple-200'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Layers className="h-4 w-4 text-purple-600" />
                          <span className="font-medium text-sm">{table.name}</span>
                          <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">VIEW</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {table.row_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500">
                          {table.column_count} columns
                        </span>
                        <span className="text-xs text-gray-500">{table.size}</span>
                      </div>
                    </button>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Table Content */}
          <div className="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
            {selectedTable ? (
              <>
                {/* Table Header */}
                <div className="border-b border-gray-200 p-3 sm:p-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900">
                        {selectedTable}
                      </h2>
                      {tables.find(t => t.name === selectedTable)?.type === 'VIEW' && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded font-medium">VIEW</span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {/* Tab Buttons */}
                      <div className="flex bg-gray-100 rounded-lg p-1">
                        <button
                          onClick={() => setActiveTab('data')}
                          className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            activeTab === 'data'
                              ? 'bg-white text-gray-900 shadow-sm'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          Data
                        </button>
                        <button
                          onClick={() => setActiveTab('schema')}
                          className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            activeTab === 'schema'
                              ? 'bg-white text-gray-900 shadow-sm'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          Schema
                        </button>
                        <button
                          onClick={() => setActiveTab('query')}
                          className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            activeTab === 'query'
                              ? 'bg-white text-gray-900 shadow-sm'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          Query
                        </button>
                      </div>

                      <div className="hidden sm:block h-6 w-px bg-gray-300" />

                      {/* Action Buttons - Hide some for views */}
                      {tables.find(t => t.name === selectedTable)?.type !== 'VIEW' && (
                        <>
                          <button
                            onClick={() => {
                              setModalType('add');
                              setFormData({});
                              setShowModal(true);
                            }}
                            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-xs sm:text-sm"
                          >
                            <Plus className="h-3 sm:h-4 w-3 sm:w-4" />
                            <span className="hidden sm:inline">Add Row</span>
                            <span className="sm:hidden">Add</span>
                          </button>
                          <button
                            onClick={() => {
                              setModalType('truncate');
                              setShowModal(true);
                            }}
                            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-xs sm:text-sm"
                          >
                            <Trash2 className="h-3 sm:h-4 w-3 sm:w-4" />
                            <span className="hidden sm:inline">Truncate</span>
                            <span className="sm:hidden">Clear</span>
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => {
                          setModalType('drop');
                          setShowModal(true);
                        }}
                        className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs sm:text-sm"
                      >
                        <AlertTriangle className="h-3 sm:h-4 w-3 sm:w-4" />
                        <span className="hidden sm:inline">
                          {tables.find(t => t.name === selectedTable)?.type === 'VIEW' ? 'Drop View' : 'Drop Table'}
                        </span>
                        <span className="sm:hidden">Drop</span>
                      </button>
                      <button
                        onClick={() => fetchTableData(selectedTable, currentPage)}
                        className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
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
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                fetchTableData(selectedTable, 1);
                              }
                            }}
                            placeholder="Search table..."
                            className="w-full sm:w-auto pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
                          />
                        </div>
                        <span className="text-xs sm:text-sm text-gray-600">
                          {totalRows.toLocaleString()} total rows
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
                            className="p-1 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <ChevronLeft className="h-5 w-5" />
                          </button>
                          <span className="text-sm text-gray-600">
                            Page {currentPage} of {totalPages}
                          </span>
                          <button
                            onClick={() => {
                              if (currentPage < totalPages) {
                                fetchTableData(selectedTable, currentPage + 1);
                              }
                            }}
                            disabled={currentPage === totalPages}
                            className="p-1 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
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
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                  ) : (
                    <>
                      {/* Data Tab */}
                      {activeTab === 'data' && (
                        <div className="overflow-x-auto -mx-3 sm:-mx-4">
                          <div className="inline-block min-w-full align-middle">
                            <div className="overflow-hidden border-b border-gray-200 sm:rounded-lg">
                              <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                              <tr className="border-b border-gray-200">
                                {tableData.length > 0 &&
                                  Object.keys(tableData[0]).map(key => (
                                    <th
                                      key={key}
                                      className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                                    >
                                      {key}
                                    </th>
                                  ))}
                                <th className="px-2 sm:px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider sticky right-0 bg-gray-50">
                                  Actions
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {tableData.map((row, rowIndex) => (
                                <tr key={rowIndex} className="hover:bg-gray-50">
                                  {Object.values(row).map((value, colIndex) => (
                                    <td key={colIndex} className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-900 whitespace-nowrap">
                                      <div className="max-w-xs truncate" title={String(value)}>
                                        {formatValue(value)}
                                      </div>
                                    </td>
                                  ))}
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-right sticky right-0 bg-white">
                                    <div className="flex justify-end gap-1 sm:gap-2">
                                      <button
                                        onClick={() => {
                                          setEditingRow(row);
                                          setFormData(row);
                                          setModalType('edit');
                                          setShowModal(true);
                                        }}
                                        className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                                      >
                                        <Edit className="h-3 sm:h-4 w-3 sm:w-4" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteRow(row)}
                                        className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
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
                            <div className="text-center py-8 sm:py-12 text-gray-500 text-sm">
                              No data found in this table
                            </div>
                          )}
                        </div>
                      )}

                      {/* Schema Tab */}
                      {activeTab === 'schema' && (
                        <div className="overflow-x-auto -mx-3 sm:-mx-4">
                          <div className="inline-block min-w-full align-middle">
                            <div className="overflow-hidden border-b border-gray-200 sm:rounded-lg">
                              <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                              <tr className="border-b border-gray-200">
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Column Name
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Data Type
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Nullable
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                                  Default
                                </th>
                                <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">
                                  Max Length
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {tableSchema.map(column => (
                                <tr key={column.column_name} className="hover:bg-gray-50">
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-gray-900">
                                    {column.column_name}
                                  </td>
                                  <td className={`px-2 sm:px-3 py-2 text-xs sm:text-sm font-mono ${getDataTypeColor(column.data_type)}`}>
                                    {column.data_type}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm">
                                    {column.is_nullable === 'YES' ? (
                                      <span className="text-green-600">✓</span>
                                    ) : (
                                      <span className="text-red-600">✗</span>
                                    )}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 hidden sm:table-cell">
                                    {column.column_default || '-'}
                                  </td>
                                  <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 hidden md:table-cell">
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              SQL Query (SELECT only)
                            </label>
                            <textarea
                              value={customQuery}
                              onChange={(e) => setCustomQuery(e.target.value)}
                              placeholder={`SELECT * FROM ${selectedTable} WHERE ...`}
                              className="w-full h-32 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                            />
                          </div>

                          <button
                            onClick={handleExecuteQuery}
                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                          >
                            <Code className="h-4 w-4" />
                            Execute Query
                          </button>

                          {queryResult.length > 0 && (
                            <div className="overflow-x-auto -mx-3 sm:-mx-4 border border-gray-200 rounded-lg mt-4">
                              <div className="inline-block min-w-full align-middle">
                                <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                  <tr>
                                    {Object.keys(queryResult[0]).map(key => (
                                      <th
                                        key={key}
                                        className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                                      >
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 bg-white">
                                  {queryResult.map((row, index) => (
                                    <tr key={index} className="hover:bg-gray-50">
                                      {Object.values(row).map((value, colIndex) => (
                                        <td key={colIndex} className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-900 whitespace-nowrap">
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
              <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                <Table className="h-12 w-12 mb-4" />
                <p className="text-lg font-medium">Select a table to view data</p>
                <p className="text-sm mt-2">Choose from the list on the left</p>
              </div>
            )}
          </div>
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] sm:max-h-[80vh] overflow-y-auto">
              <div className="p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-900">
                    {modalType === 'add' && 'Add New Row'}
                    {modalType === 'edit' && 'Edit Row'}
                    {modalType === 'truncate' && 'Truncate Table'}
                    {modalType === 'drop' && 'Drop Table'}
                  </h3>
                  <button
                    onClick={() => {
                      setShowModal(false);
                      setFormData({});
                      setEditingRow(null);
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                {(modalType === 'truncate' || modalType === 'drop') ? (
                  <div className="space-y-4">
                    <div className="flex items-start sm:items-center gap-3 p-3 sm:p-4 bg-red-50 border border-red-200 rounded-lg">
                      <AlertTriangle className="h-5 sm:h-6 w-5 sm:w-6 text-red-600 flex-shrink-0 mt-0.5 sm:mt-0" />
                      <div>
                        <p className="text-red-900 font-medium text-sm sm:text-base">
                          Warning: This action cannot be undone!
                        </p>
                        <p className="text-red-700 text-xs sm:text-sm mt-1">
                          {modalType === 'truncate'
                            ? `All data in table "${selectedTable}" will be permanently deleted.`
                            : `The entire table "${selectedTable}" and all its data will be permanently removed from the database.`}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3">
                      <button
                        onClick={() => setShowModal(false)}
                        className="w-full sm:w-auto px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={modalType === 'truncate' ? handleTruncateTable : handleDropTable}
                        className="w-full sm:w-auto px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                      >
                        {modalType === 'truncate' ? 'Truncate Table' : 'Drop Table'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {tableSchema.map(column => (
                      <div key={column.column_name}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {column.column_name}
                          {column.is_nullable === 'NO' && (
                            <span className="text-red-500 ml-1">*</span>
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
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                        <span className="text-xs text-gray-500">
                          Type: {column.data_type}
                        </span>
                      </div>
                    ))}

                    <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3 pt-4">
                      <button
                        onClick={() => {
                          setShowModal(false);
                          setFormData({});
                          setEditingRow(null);
                        }}
                        className="w-full sm:w-auto px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={modalType === 'add' ? handleAddRow : handleUpdateRow}
                        className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
                      >
                        {modalType === 'add' ? 'Add Row' : 'Update Row'}
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