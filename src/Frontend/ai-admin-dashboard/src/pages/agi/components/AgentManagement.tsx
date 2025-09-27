/**
 * Agent Management Module
 * Comprehensive agent management with CRUD operations
 * Following SOLID principles and component composition
 */

import React, { useState, useCallback } from 'react';
import {
  useAgents,
  useAgentDetails,
  useAsyncData
} from '../hooks/useAGI';
import { agiApi } from '../services/agiApi';
import {
  Card, CardHeader, CardContent, CardFooter,
  Table, DataTable, Pagination,
  Button, IconButton,
  Badge, StatusDot,
  Modal, Tabs,
  Alert,
  LoadingState, Spinner, Skeleton
} from './ui';
import {
  IAgent, IAgentDetails, IAgentStats, IAgentTask, IAgentAction,
  AgentState, AgentType, TaskStatus
} from '../types';

/**
 * Main Agent Management Component
 */
export const AgentManagement: React.FC = () => {
  const { agents, loading, error, refetch } = useAgents();
  const [selectedAgent, setSelectedAgent] = useState<IAgent | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [filterState, setFilterState] = useState<AgentState | 'all'>('all');
  const [filterType, setFilterType] = useState<AgentType | 'all'>('all');

  // Filter agents based on state and type
  const filteredAgents = React.useMemo(() => {
    return agents.filter(agent => {
      const stateMatch = filterState === 'all' || agent.state === filterState;
      const typeMatch = filterType === 'all' || agent.type === filterType;
      return stateMatch && typeMatch;
    });
  }, [agents, filterState, filterType]);

  // Agent stats
  const agentStats = React.useMemo(() => {
    return {
      total: agents.length,
      active: agents.filter(a => a.state === AgentState.ACTIVE).length,
      idle: agents.filter(a => a.state === AgentState.IDLE).length,
      error: agents.filter(a => a.state === AgentState.ERROR).length,
      paused: agents.filter(a => a.state === AgentState.PAUSED).length
    };
  }, [agents]);

  const handleAgentClick = (agent: IAgent) => {
    setSelectedAgent(agent);
    setShowDetailsModal(true);
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        // API call to delete agent would go here
        await refetch();
      } catch (error) {
        console.error('Failed to delete agent:', error);
      }
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Agent Name',
      render: (value: string, agent: IAgent) => (
        <div className="flex items-center space-x-3">
          <StatusDot
            status={agent.state === AgentState.ACTIVE ? 'online' :
                   agent.state === AgentState.ERROR ? 'busy' : 'away'}
            size="sm"
          />
          <div>
            <p className="font-medium text-gray-900">{value}</p>
            <p className="text-xs text-gray-500">ID: {agent.id}</p>
          </div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'type',
      header: 'Type',
      render: (value: AgentType) => (
        <Badge variant="info" size="sm">{value}</Badge>
      ),
      sortable: true
    },
    {
      key: 'state',
      header: 'State',
      render: (value: AgentState) => {
        const stateColors = {
          [AgentState.ACTIVE]: 'success',
          [AgentState.IDLE]: 'warning',
          [AgentState.PAUSED]: 'default',
          [AgentState.ERROR]: 'danger',
          [AgentState.INITIALIZING]: 'info'
        };
        return (
          <Badge variant={stateColors[value] as any} size="sm">
            {value}
          </Badge>
        );
      },
      sortable: true
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (value: string[]) => (
        <div className="flex flex-wrap gap-1">
          {value.slice(0, 3).map(cap => (
            <Badge key={cap} variant="default" size="sm">{cap}</Badge>
          ))}
          {value.length > 3 && (
            <Badge variant="default" size="sm">+{value.length - 3}</Badge>
          )}
        </div>
      )
    },
    {
      key: 'metrics.success_rate',
      header: 'Success Rate',
      render: (value: number) => (
        <div className="flex items-center space-x-2">
          <div className="w-24 bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full"
              style={{ width: `${value}%` }}
            />
          </div>
          <span className="text-sm text-gray-600">{value}%</span>
        </div>
      ),
      sortable: true
    },
    {
      key: 'last_active',
      header: 'Last Active',
      render: (value: string) => (
        <span className="text-sm text-gray-600">
          {new Date(value).toLocaleString()}
        </span>
      ),
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (_: any, agent: IAgent) => (
        <div className="flex items-center justify-end space-x-2">
          <IconButton
            icon={<ViewIcon />}
            size="sm"
            onClick={() => handleAgentClick(agent)}
          />
          <IconButton
            icon={<EditIcon />}
            size="sm"
            onClick={() => handleAgentClick(agent)}
          />
          <IconButton
            icon={<DeleteIcon />}
            size="sm"
            variant="danger"
            onClick={() => handleDeleteAgent(agent.id)}
          />
        </div>
      )
    }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agent Management</h1>
          <p className="text-gray-600 mt-1">Monitor and manage all AGI agents</p>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowCreateModal(true)}
        >
          <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Agent
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <StatCard
          label="Total Agents"
          value={agentStats.total}
          color="blue"
          onClick={() => setFilterState('all')}
          active={filterState === 'all'}
        />
        <StatCard
          label="Active"
          value={agentStats.active}
          color="green"
          onClick={() => setFilterState(AgentState.ACTIVE)}
          active={filterState === AgentState.ACTIVE}
        />
        <StatCard
          label="Idle"
          value={agentStats.idle}
          color="yellow"
          onClick={() => setFilterState(AgentState.IDLE)}
          active={filterState === AgentState.IDLE}
        />
        <StatCard
          label="Paused"
          value={agentStats.paused}
          color="gray"
          onClick={() => setFilterState(AgentState.PAUSED)}
          active={filterState === AgentState.PAUSED}
        />
        <StatCard
          label="Error"
          value={agentStats.error}
          color="red"
          onClick={() => setFilterState(AgentState.ERROR)}
          active={filterState === AgentState.ERROR}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mr-2">Type:</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                {Object.values(AgentType).map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="flex-1" />

            <Button variant="ghost" size="sm" onClick={refetch}>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Agents Table */}
      <Card>
        <CardContent>
          <LoadingState
            loading={loading}
            error={error}
            loadingComponent={<Spinner size="lg" />}
          >
            <DataTable
              data={filteredAgents}
              columns={columns}
              pageSize={10}
              searchable
              searchPlaceholder="Search agents..."
            />
          </LoadingState>
        </CardContent>
      </Card>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateAgentModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            refetch();
          }}
        />
      )}

      {/* Agent Details Modal */}
      {showDetailsModal && selectedAgent && (
        <AgentDetailsModal
          agent={selectedAgent}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedAgent(null);
          }}
        />
      )}
    </div>
  );
};

/**
 * Stat Card Component
 */
const StatCard: React.FC<{
  label: string;
  value: number;
  color: string;
  onClick?: () => void;
  active?: boolean;
}> = ({ label, value, color, onClick, active }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
    red: 'bg-red-100 text-red-800 border-red-200'
  };

  return (
    <div
      onClick={onClick}
      className={`
        p-4 rounded-lg border-2 transition-all cursor-pointer
        ${active ? colorClasses[color as keyof typeof colorClasses] : 'bg-white border-gray-200 hover:border-gray-300'}
      `}
    >
      <p className="text-sm font-medium text-gray-600">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
};

/**
 * Create Agent Modal
 */
const CreateAgentModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: AgentType.CONVERSATIONAL,
    capabilities: [] as string[],
    config: {}
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // API call to create agent would go here
      await new Promise(resolve => setTimeout(resolve, 1000));
      onSuccess();
    } catch (error) {
      console.error('Failed to create agent:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Create New Agent"
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter agent name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as AgentType })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(AgentType).map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capabilities
            </label>
            <div className="space-y-2">
              {['NLP', 'Vision', 'Code Generation', 'Data Analysis', 'Planning'].map(cap => (
                <label key={cap} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.capabilities.includes(cap)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({
                          ...formData,
                          capabilities: [...formData.capabilities, cap]
                        });
                      } else {
                        setFormData({
                          ...formData,
                          capabilities: formData.capabilities.filter(c => c !== cap)
                        });
                      }
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">{cap}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Create Agent
          </Button>
        </div>
      </form>
    </Modal>
  );
};

/**
 * Agent Details Modal
 */
const AgentDetailsModal: React.FC<{
  agent: IAgent;
  onClose: () => void;
}> = ({ agent, onClose }) => {
  const { details, stats, tasks, loading, error } = useAgentDetails(agent.id);
  const [activeTab, setActiveTab] = useState('overview');

  const handleAction = async (action: IAgentAction) => {
    try {
      await agiApi.executeAgentAction(agent.id, action);
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      content: (
        <AgentOverviewTab
          agent={agent}
          details={details}
          stats={stats}
          onAction={handleAction}
        />
      )
    },
    {
      id: 'tasks',
      label: 'Tasks',
      badge: tasks?.length || 0,
      content: <AgentTasksTab tasks={tasks || []} />
    },
    {
      id: 'metrics',
      label: 'Metrics',
      content: <AgentMetricsTab stats={stats} />
    },
    {
      id: 'config',
      label: 'Configuration',
      content: <AgentConfigTab agent={agent} details={details} />
    }
  ];

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={`Agent: ${agent.name}`}
      size="xl"
    >
      <LoadingState loading={loading} error={error}>
        <Tabs tabs={tabs} defaultTab={activeTab} />
      </LoadingState>
    </Modal>
  );
};

/**
 * Agent Overview Tab
 */
const AgentOverviewTab: React.FC<{
  agent: IAgent;
  details: IAgentDetails | null;
  stats: IAgentStats | null;
  onAction: (action: IAgentAction) => void;
}> = ({ agent, details, stats, onAction }) => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Status</p>
          <div className="flex items-center space-x-2 mt-1">
            <StatusDot
              status={agent.state === AgentState.ACTIVE ? 'online' : 'away'}
            />
            <Badge variant={agent.state === AgentState.ACTIVE ? 'success' : 'warning'}>
              {agent.state}
            </Badge>
          </div>
        </div>
        <div>
          <p className="text-sm text-gray-600">Type</p>
          <p className="font-medium mt-1">{agent.type}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Version</p>
          <p className="font-medium mt-1">{details?.version || 'Unknown'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Last Active</p>
          <p className="font-medium mt-1">
            {new Date(agent.last_active).toLocaleString()}
          </p>
        </div>
      </div>

      <div>
        <p className="text-sm text-gray-600 mb-2">Capabilities</p>
        <div className="flex flex-wrap gap-2">
          {agent.capabilities.map(cap => (
            <Badge key={cap} variant="info">{cap}</Badge>
          ))}
        </div>
      </div>

      <div>
        <p className="text-sm text-gray-600 mb-2">Quick Actions</p>
        <div className="flex space-x-2">
          {agent.state === AgentState.ACTIVE ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onAction({ type: 'pause' })}
            >
              Pause
            </Button>
          ) : (
            <Button
              variant="success"
              size="sm"
              onClick={() => onAction({ type: 'resume' })}
            >
              Resume
            </Button>
          )}
          <Button
            variant="danger"
            size="sm"
            onClick={() => onAction({ type: 'restart' })}
          >
            Restart
          </Button>
        </div>
      </div>
    </div>
  );
};

/**
 * Agent Tasks Tab
 */
const AgentTasksTab: React.FC<{ tasks: IAgentTask[] }> = ({ tasks }) => {
  const taskColumns = [
    {
      key: 'name',
      header: 'Task',
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      render: (value: TaskStatus) => {
        const statusColors = {
          [TaskStatus.PENDING]: 'default',
          [TaskStatus.RUNNING]: 'info',
          [TaskStatus.COMPLETED]: 'success',
          [TaskStatus.FAILED]: 'danger',
          [TaskStatus.CANCELLED]: 'warning'
        };
        return <Badge variant={statusColors[value] as any}>{value}</Badge>;
      },
      sortable: true
    },
    {
      key: 'progress',
      header: 'Progress',
      render: (value: number) => (
        <div className="flex items-center space-x-2">
          <div className="w-24 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${value}%` }}
            />
          </div>
          <span className="text-sm">{value}%</span>
        </div>
      )
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (value: string) => new Date(value).toLocaleString(),
      sortable: true
    }
  ];

  return (
    <div>
      {tasks.length > 0 ? (
        <Table data={tasks} columns={taskColumns} compact />
      ) : (
        <p className="text-center text-gray-500 py-8">No tasks available</p>
      )}
    </div>
  );
};

/**
 * Agent Metrics Tab
 */
const AgentMetricsTab: React.FC<{ stats: IAgentStats | null }> = ({ stats }) => {
  if (!stats) return <p className="text-center text-gray-500">No metrics available</p>;

  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <p className="text-sm text-gray-600">Tasks Completed</p>
        <p className="text-2xl font-bold">{stats.tasks_completed}</p>
      </div>
      <div>
        <p className="text-sm text-gray-600">Success Rate</p>
        <p className="text-2xl font-bold">{stats.success_rate}%</p>
      </div>
      <div>
        <p className="text-sm text-gray-600">Average Response Time</p>
        <p className="text-2xl font-bold">{stats.avg_response_time}ms</p>
      </div>
      <div>
        <p className="text-sm text-gray-600">Total Processing Time</p>
        <p className="text-2xl font-bold">{stats.total_processing_time}s</p>
      </div>
    </div>
  );
};

/**
 * Agent Config Tab
 */
const AgentConfigTab: React.FC<{
  agent: IAgent;
  details: IAgentDetails | null;
}> = ({ agent, details }) => {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Configuration</p>
        <pre className="bg-gray-100 p-3 rounded-lg text-sm overflow-auto">
          {JSON.stringify(details?.config || agent.config, null, 2)}
        </pre>
      </div>
    </div>
  );
};

// Icon components
const ViewIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const EditIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const DeleteIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

export default AgentManagement;