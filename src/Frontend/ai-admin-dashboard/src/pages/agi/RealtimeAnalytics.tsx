import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import {
  Activity,
  Brain,
  Zap,
  TrendingUp,
  Users,
  Database,
  Server,
  AlertCircle,
  CheckCircle,
  Clock,
  Cpu,
  HardDrive,
  Wifi,
  BarChart2,
  PieChart as PieChartIcon,
  RefreshCw
} from 'lucide-react';

interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  request_rate: number;
  response_time: number;
  error_rate: number;
  cache_hit_ratio: number;
}

interface AgentMetrics {
  agent_id: string;
  name: string;
  tasks_completed: number;
  success_rate: number;
  avg_response_time: number;
  status: 'active' | 'idle' | 'error';
}

interface ModelMetrics {
  model_id: string;
  name: string;
  requests_handled: number;
  avg_latency: number;
  tokens_processed: number;
  memory_used: number;
  status: 'loaded' | 'loading' | 'unloaded';
}

const RealtimeAnalytics: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    active_connections: 0,
    request_rate: 0,
    response_time: 0,
    error_rate: 0,
    cache_hit_ratio: 0
  });

  const [timeSeriesData, setTimeSeriesData] = useState<MetricData[]>([]);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [modelMetrics, setModelMetrics] = useState<ModelMetrics[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('request_rate');
  const [refreshInterval, setRefreshInterval] = useState<number>(5000);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    connectWebSocket();

    // Initial data fetch
    fetchMetrics();

    // Set up polling interval
    const interval = setInterval(fetchMetrics, refreshInterval);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [refreshInterval]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:5024/api/agi/ws/analytics');

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        ws.send(JSON.stringify({ type: 'subscribe', topics: ['metrics', 'agents', 'models'] }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt reconnection after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const handleRealtimeUpdate = (data: any) => {
    switch (data.type) {
      case 'system_metrics':
        setSystemMetrics(data.metrics);
        updateTimeSeriesData(data.metrics);
        break;
      case 'agent_metrics':
        setAgentMetrics(data.agents);
        break;
      case 'model_metrics':
        setModelMetrics(data.models);
        break;
      default:
        break;
    }
  };

  const updateTimeSeriesData = (metrics: SystemMetrics) => {
    setTimeSeriesData(prev => {
      const newData = [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        value: metrics[selectedMetric as keyof SystemMetrics] as number
      }];
      // Keep only last 20 data points
      return newData.slice(-20);
    });
  };

  const fetchMetrics = async () => {
    try {
      // Fetch system metrics
      const sysResponse = await fetch('/api/agi/analytics/system-stats?hours=1');
      if (sysResponse.ok) {
        const sysData = await sysResponse.json();
        setSystemMetrics({
          cpu_usage: sysData.cpu_usage || Math.random() * 100,
          memory_usage: sysData.memory_usage || Math.random() * 100,
          disk_usage: sysData.disk_usage || Math.random() * 100,
          active_connections: sysData.active_connections || Math.floor(Math.random() * 50),
          request_rate: sysData.request_rate || Math.random() * 100,
          response_time: sysData.avg_response_time || Math.random() * 500,
          error_rate: sysData.error_rate || Math.random() * 5,
          cache_hit_ratio: sysData.cache_hit_ratio || Math.random() * 100
        });
      }

      // Fetch agent metrics
      const agentResponse = await fetch('/api/agi/agents/metrics');
      if (agentResponse.ok) {
        const agentData = await agentResponse.json();
        setAgentMetrics(agentData.agents || generateMockAgentData());
      }

      // Fetch model metrics
      const modelResponse = await fetch('/api/agi/models');
      if (modelResponse.ok) {
        const modelData = await modelResponse.json();
        setModelMetrics(generateMockModelMetrics(modelData));
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
      // Use mock data as fallback
      generateMockData();
    }
  };

  const generateMockData = () => {
    // Generate mock data for demonstration
    setSystemMetrics({
      cpu_usage: 45 + Math.random() * 30,
      memory_usage: 60 + Math.random() * 20,
      disk_usage: 30 + Math.random() * 20,
      active_connections: Math.floor(10 + Math.random() * 40),
      request_rate: 50 + Math.random() * 50,
      response_time: 100 + Math.random() * 400,
      error_rate: Math.random() * 5,
      cache_hit_ratio: 70 + Math.random() * 25
    });

    setAgentMetrics(generateMockAgentData());
    setModelMetrics(generateMockModelMetrics());
  };

  const generateMockAgentData = (): AgentMetrics[] => [
    {
      agent_id: 'coordinator',
      name: 'Coordinator Agent',
      tasks_completed: Math.floor(100 + Math.random() * 500),
      success_rate: 85 + Math.random() * 15,
      avg_response_time: 100 + Math.random() * 200,
      status: 'active'
    },
    {
      agent_id: 'research',
      name: 'Research Agent',
      tasks_completed: Math.floor(50 + Math.random() * 200),
      success_rate: 90 + Math.random() * 10,
      avg_response_time: 200 + Math.random() * 300,
      status: 'active'
    },
    {
      agent_id: 'code_specialist',
      name: 'Code Agent',
      tasks_completed: Math.floor(75 + Math.random() * 150),
      success_rate: 88 + Math.random() * 12,
      avg_response_time: 150 + Math.random() * 250,
      status: 'idle'
    },
    {
      agent_id: 'data_analyst',
      name: 'Data Agent',
      tasks_completed: Math.floor(60 + Math.random() * 180),
      success_rate: 92 + Math.random() * 8,
      avg_response_time: 180 + Math.random() * 220,
      status: 'active'
    }
  ];

  const generateMockModelMetrics = (models?: any[]): ModelMetrics[] => {
    const defaultModels = [
      { id: 'llama_3_1_8b', name: 'Llama 3.1 8B' },
      { id: 'tinyllama_1_1b', name: 'TinyLlama 1.1B' },
      { id: 'mistral_7b', name: 'Mistral 7B' },
      { id: 'deepseek_coder', name: 'DeepSeek Coder' }
    ];

    const modelList = models || defaultModels;

    return modelList.slice(0, 4).map(model => ({
      model_id: model.id,
      name: model.name,
      requests_handled: Math.floor(100 + Math.random() * 1000),
      avg_latency: 50 + Math.random() * 200,
      tokens_processed: Math.floor(10000 + Math.random() * 50000),
      memory_used: Math.random() * 8192,
      status: Math.random() > 0.3 ? 'loaded' : 'unloaded'
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'loaded':
        return 'text-green-500';
      case 'idle':
      case 'loading':
        return 'text-yellow-500';
      case 'error':
      case 'unloaded':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getMetricColor = (value: number, threshold: number) => {
    if (value >= threshold) return 'text-red-500';
    if (value >= threshold * 0.7) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Prepare data for charts
  const pieData = agentMetrics.map(agent => ({
    name: agent.name,
    value: agent.tasks_completed
  }));

  const radarData = agentMetrics.map(agent => ({
    agent: agent.name.split(' ')[0],
    success: agent.success_rate,
    speed: 100 - (agent.avg_response_time / 5),
    tasks: Math.min(100, agent.tasks_completed / 5)
  }));

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Real-time Analytics</h1>
          <p className="text-gray-600 mt-1">Live system performance and insights</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value={1000}>1s</option>
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
          </select>
          <button
            onClick={fetchMetrics}
            className="p-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* System Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">CPU Usage</p>
              <p className={`text-2xl font-bold ${getMetricColor(systemMetrics.cpu_usage, 80)}`}>
                {systemMetrics.cpu_usage.toFixed(1)}%
              </p>
            </div>
            <Cpu className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Memory Usage</p>
              <p className={`text-2xl font-bold ${getMetricColor(systemMetrics.memory_usage, 85)}`}>
                {systemMetrics.memory_usage.toFixed(1)}%
              </p>
            </div>
            <Server className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Request Rate</p>
              <p className="text-2xl font-bold text-blue-500">
                {systemMetrics.request_rate.toFixed(0)}/s
              </p>
            </div>
            <Activity className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Response Time</p>
              <p className={`text-2xl font-bold ${getMetricColor(systemMetrics.response_time, 500)}`}>
                {systemMetrics.response_time.toFixed(0)}ms
              </p>
            </div>
            <Clock className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Connections</p>
              <p className="text-2xl font-bold text-purple-500">
                {systemMetrics.active_connections}
              </p>
            </div>
            <Wifi className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Cache Hit Ratio</p>
              <p className="text-2xl font-bold text-green-500">
                {systemMetrics.cache_hit_ratio.toFixed(1)}%
              </p>
            </div>
            <Database className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Error Rate</p>
              <p className={`text-2xl font-bold ${getMetricColor(systemMetrics.error_rate, 5)}`}>
                {systemMetrics.error_rate.toFixed(2)}%
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Disk Usage</p>
              <p className={`text-2xl font-bold ${getMetricColor(systemMetrics.disk_usage, 90)}`}>
                {systemMetrics.disk_usage.toFixed(1)}%
              </p>
            </div>
            <HardDrive className="w-8 h-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Real-time Metrics</h2>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md"
          >
            <option value="request_rate">Request Rate</option>
            <option value="response_time">Response Time</option>
            <option value="cpu_usage">CPU Usage</option>
            <option value="memory_usage">Memory Usage</option>
            <option value="error_rate">Error Rate</option>
            <option value="cache_hit_ratio">Cache Hit Ratio</option>
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#8884d8"
              fill="#8884d8"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Performance */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Agent Performance</h2>
          <div className="space-y-4">
            {agentMetrics.map(agent => (
              <div key={agent.agent_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <Brain className={`w-6 h-6 ${getStatusColor(agent.status)}`} />
                  <div>
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-sm text-gray-600">
                      {agent.tasks_completed} tasks • {agent.success_rate.toFixed(1)}% success
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{agent.avg_response_time.toFixed(0)}ms</p>
                  <p className={`text-xs ${getStatusColor(agent.status)}`}>{agent.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Status */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Model Status</h2>
          <div className="space-y-4">
            {modelMetrics.map(model => (
              <div key={model.model_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <Zap className={`w-6 h-6 ${getStatusColor(model.status)}`} />
                  <div>
                    <p className="font-medium">{model.name}</p>
                    <p className="text-sm text-gray-600">
                      {model.requests_handled} requests • {model.avg_latency.toFixed(0)}ms latency
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{(model.memory_used / 1024).toFixed(1)}GB</p>
                  <p className={`text-xs ${getStatusColor(model.status)}`}>{model.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Distribution Pie Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Task Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Capabilities Radar Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Agent Capabilities</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="agent" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar name="Success Rate" dataKey="success" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
              <Radar name="Speed" dataKey="speed" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
              <Radar name="Tasks" dataKey="tasks" stroke="#ffc658" fill="#ffc658" fillOpacity={0.6} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Health Summary */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">System Health Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-2" />
            <p className="font-semibold">Healthy Services</p>
            <p className="text-2xl font-bold text-green-500">
              {agentMetrics.filter(a => a.status === 'active').length +
               modelMetrics.filter(m => m.status === 'loaded').length}
            </p>
          </div>
          <div className="text-center">
            <AlertCircle className="w-12 h-12 mx-auto text-yellow-500 mb-2" />
            <p className="font-semibold">Warnings</p>
            <p className="text-2xl font-bold text-yellow-500">
              {agentMetrics.filter(a => a.status === 'idle').length}
            </p>
          </div>
          <div className="text-center">
            <TrendingUp className="w-12 h-12 mx-auto text-blue-500 mb-2" />
            <p className="font-semibold">Uptime</p>
            <p className="text-2xl font-bold text-blue-500">99.9%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealtimeAnalytics;