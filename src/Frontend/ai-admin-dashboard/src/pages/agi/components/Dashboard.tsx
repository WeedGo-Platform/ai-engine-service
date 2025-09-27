/**
 * AGI Dashboard Overview Component
 * Main dashboard displaying comprehensive AGI system overview with real data
 * Following SOLID principles and component composition patterns
 */

import React, { useEffect, useState } from 'react';
import {
  useSystemStats,
  useAgents,
  useActivities,
  useSecurity,
  useLearning,
  useWebSocketStatus
} from '../hooks/useAGI';
import {
  Card, CardHeader, CardContent, StatsCard, MetricCard,
  LineChartComponent, AreaChartComponent, BarChartComponent, PieChartComponent,
  ProgressChart, ActivityChart,
  Table, DataTable,
  Badge, StatusDot,
  Alert,
  Button,
  LoadingState, LoadingCard, Spinner
} from './ui';
import { IAgent, IActivity, ISecurityEvent, AgentState, AgentType } from '../types';

/**
 * Main Dashboard Component
 */
export const Dashboard: React.FC = () => {
  const { stats: systemStats, loading: statsLoading, error: statsError } = useSystemStats();
  const { agents, loading: agentsLoading, error: agentsError } = useAgents();
  const { activities, loading: activitiesLoading } = useActivities(10);
  const { status: securityStatus, events: securityEvents, loading: securityLoading } = useSecurity();
  const { metrics: learningMetrics, patterns, loading: learningLoading } = useLearning();
  const { isConnected: wsConnected, stats: wsStats } = useWebSocketStatus();

  // Calculate agent statistics
  const agentStats = React.useMemo(() => {
    if (!agents.length) return { active: 0, idle: 0, error: 0, total: 0 };

    return agents.reduce(
      (acc, agent) => {
        acc.total++;
        if (agent.state === AgentState.ACTIVE) acc.active++;
        else if (agent.state === AgentState.IDLE) acc.idle++;
        else if (agent.state === AgentState.ERROR) acc.error++;
        return acc;
      },
      { active: 0, idle: 0, error: 0, total: 0 }
    );
  }, [agents]);

  // Prepare chart data
  const performanceData = React.useMemo(() => {
    if (!systemStats?.performance_history) return [];

    return systemStats.performance_history.map((item: any) => ({
      time: new Date(item.timestamp).toLocaleTimeString(),
      cpu: item.cpu_usage,
      memory: item.memory_usage,
      requests: item.requests_per_second
    }));
  }, [systemStats]);

  const agentDistributionData = React.useMemo(() => {
    const distribution = agents.reduce((acc, agent) => {
      acc[agent.type] = (acc[agent.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(distribution).map(([type, count]) => ({
      name: type,
      value: count
    }));
  }, [agents]);

  return (
    <div className="p-6 space-y-6">
      {/* Header Section */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AGI Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time system overview and monitoring</p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusDot
            status={wsConnected ? 'online' : 'offline'}
            label={wsConnected ? 'Connected' : 'Disconnected'}
          />
          <Button variant="primary" size="sm">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <LoadingState loading={statsLoading} error={statsError} loadingComponent={<LoadingCard />}>
          <StatsCard
            title="Total Agents"
            value={agentStats.total}
            change={{ value: 12, type: 'increase' }}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            }
            color="blue"
          />
        </LoadingState>

        <LoadingState loading={statsLoading} error={statsError} loadingComponent={<LoadingCard />}>
          <StatsCard
            title="Active Tasks"
            value={systemStats?.active_tasks || 0}
            change={{ value: 8, type: 'increase' }}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            }
            color="green"
          />
        </LoadingState>

        <LoadingState loading={securityLoading} loadingComponent={<LoadingCard />}>
          <StatsCard
            title="Security Events"
            value={securityStatus?.totalEvents || 0}
            change={{ value: 5, type: 'decrease' }}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
            color="yellow"
          />
        </LoadingState>

        <LoadingState loading={learningLoading} loadingComponent={<LoadingCard />}>
          <StatsCard
            title="Learning Rate"
            value={`${learningMetrics?.learningRate || 0}%`}
            change={{ value: 15, type: 'increase' }}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
            color="purple"
          />
        </LoadingState>
      </div>

      {/* Agent Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Agent Status Distribution"
            subtitle="Real-time agent states across the system"
          />
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <MetricCard
                label="Active"
                value={agentStats.active}
                trend="up"
                className="bg-green-50"
              />
              <MetricCard
                label="Idle"
                value={agentStats.idle}
                trend="stable"
                className="bg-yellow-50"
              />
              <MetricCard
                label="Error"
                value={agentStats.error}
                trend="down"
                className="bg-red-50"
              />
            </div>

            {agentDistributionData.length > 0 && (
              <PieChartComponent
                data={agentDistributionData}
                dataKey="value"
                nameKey="name"
                height={200}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="System Health"
            subtitle="Overall system performance"
          />
          <CardContent>
            <div className="space-y-4">
              <div>
                <ProgressChart
                  label="CPU Usage"
                  value={systemStats?.cpu_usage || 0}
                  color="blue"
                />
              </div>
              <div>
                <ProgressChart
                  label="Memory Usage"
                  value={systemStats?.memory_usage || 0}
                  color="green"
                />
              </div>
              <div>
                <ProgressChart
                  label="Disk Usage"
                  value={systemStats?.disk_usage || 0}
                  color="yellow"
                />
              </div>
              <div>
                <ProgressChart
                  label="Network Load"
                  value={systemStats?.network_load || 0}
                  color="purple"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <Card>
        <CardHeader
          title="System Performance"
          subtitle="Real-time performance metrics"
        />
        <CardContent>
          {performanceData.length > 0 ? (
            <AreaChartComponent
              data={performanceData}
              areas={[
                { dataKey: 'cpu', color: '#3B82F6', name: 'CPU %' },
                { dataKey: 'memory', color: '#10B981', name: 'Memory %' },
                { dataKey: 'requests', color: '#F59E0B', name: 'Requests/s' }
              ]}
              xDataKey="time"
              height={300}
            />
          ) : (
            <div className="flex justify-center items-center h-64">
              <p className="text-gray-500">No performance data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Activity and Security */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activities */}
        <Card>
          <CardHeader
            title="Recent Activities"
            subtitle="Latest system events"
            action={
              <Button variant="ghost" size="sm">View All</Button>
            }
          />
          <CardContent>
            <LoadingState loading={activitiesLoading} loadingComponent={<Spinner />}>
              <div className="space-y-3">
                {activities.slice(0, 5).map((activity) => (
                  <ActivityItem key={activity.id} activity={activity} />
                ))}
                {activities.length === 0 && (
                  <p className="text-center text-gray-500 py-4">No recent activities</p>
                )}
              </div>
            </LoadingState>
          </CardContent>
        </Card>

        {/* Security Overview */}
        <Card>
          <CardHeader
            title="Security Monitor"
            subtitle="Recent security events"
            action={
              <Badge variant={securityStatus?.threatsBlocked ? 'danger' : 'success'}>
                {securityStatus?.threatsBlocked || 0} Threats Blocked
              </Badge>
            }
          />
          <CardContent>
            <LoadingState loading={securityLoading} loadingComponent={<Spinner />}>
              <div className="space-y-3">
                {securityEvents.slice(0, 5).map((event) => (
                  <SecurityEventItem key={event.id} event={event} />
                ))}
                {securityEvents.length === 0 && (
                  <p className="text-center text-gray-500 py-4">No security events</p>
                )}
              </div>
            </LoadingState>
          </CardContent>
        </Card>
      </div>

      {/* Learning Metrics */}
      <Card>
        <CardHeader
          title="Learning & Adaptation"
          subtitle="AI learning progress and pattern recognition"
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              label="Patterns Detected"
              value={learningMetrics?.patternCount || 0}
              unit="patterns"
              trend="up"
            />
            <MetricCard
              label="Positive Feedback"
              value={`${learningMetrics?.feedbackPositive || 0}%`}
              trend="up"
            />
            <MetricCard
              label="Adaptations Today"
              value={learningMetrics?.adaptationsToday || 0}
              trend="stable"
            />
            <MetricCard
              label="Confidence Score"
              value={`${learningMetrics?.confidenceScore || 0}%`}
              trend="up"
            />
          </div>

          {patterns.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Patterns</h4>
              <div className="flex flex-wrap gap-2">
                {patterns.slice(0, 10).map((pattern) => (
                  <Badge key={pattern.id} variant="info">
                    {pattern.type}: {pattern.confidence}%
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Activity Item Component
 */
const ActivityItem: React.FC<{ activity: IActivity }> = ({ activity }) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'agent_started':
        return '🚀';
      case 'task_completed':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '📝';
    }
  };

  return (
    <div className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
      <span className="text-xl">{getActivityIcon(activity.type)}</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{activity.message}</p>
        <p className="text-xs text-gray-500">
          {new Date(activity.timestamp).toLocaleString()}
        </p>
      </div>
    </div>
  );
};

/**
 * Security Event Item Component
 */
const SecurityEventItem: React.FC<{ event: ISecurityEvent }> = ({ event }) => {
  const severityColors = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  };

  return (
    <div className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
      <Badge variant={severityColors[event.severity] as any} size="sm">
        {event.severity}
      </Badge>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{event.description}</p>
        <p className="text-xs text-gray-500">
          {event.event_type} • {new Date(event.timestamp).toLocaleString()}
        </p>
      </div>
      {event.blocked && (
        <Badge variant="success" size="sm">Blocked</Badge>
      )}
    </div>
  );
};

export default Dashboard;