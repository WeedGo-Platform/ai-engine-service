/**
 * Security Center Component
 * Comprehensive security monitoring and threat management
 * Following SOLID principles and security best practices
 */

import React, { useState, useMemo } from 'react';
import { useSecurity, useRateLimits, useAuditLogs } from '../hooks/useAGI';
import { agiApi } from '../services/agiApi';
import {
  Card, CardHeader, CardContent, CardFooter,
  Table, DataTable,
  Badge, StatusDot,
  Alert, Button, IconButton,
  LineChartComponent, AreaChartComponent, PieChartComponent,
  ProgressChart, ActivityChart,
  Modal, Tabs,
  LoadingState, Spinner
} from './ui';
import {
  ISecurityStatus, ISecurityEvent, ISecurityRule,
  IRateLimit, IRateLimitUpdate, IAuditLog,
  ThreatLevel, SecurityEventType
} from '../types';

/**
 * Main Security Center Component
 */
export const SecurityCenter: React.FC = () => {
  const { status, events, loading: securityLoading, error: securityError, refetch } = useSecurity();
  const { limits, loading: limitsLoading, updateLimit } = useRateLimits();
  const { logs, loading: logsLoading } = useAuditLogs({ severity: 'warning', limit: 100 });

  const [selectedEvent, setSelectedEvent] = useState<ISecurityEvent | null>(null);
  const [showEventDetails, setShowEventDetails] = useState(false);
  const [showRateLimitModal, setShowRateLimitModal] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<ThreatLevel | 'all'>('all');
  const [filterEventType, setFilterEventType] = useState<SecurityEventType | 'all'>('all');

  // Filter security events
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      const severityMatch = filterSeverity === 'all' || event.severity === filterSeverity;
      const typeMatch = filterEventType === 'all' || event.event_type === filterEventType;
      return severityMatch && typeMatch;
    });
  }, [events, filterSeverity, filterEventType]);

  // Calculate threat statistics
  const threatStats = useMemo(() => {
    const stats = {
      total: events.length,
      blocked: events.filter(e => e.blocked).length,
      critical: events.filter(e => e.severity === ThreatLevel.CRITICAL).length,
      high: events.filter(e => e.severity === ThreatLevel.HIGH).length,
      medium: events.filter(e => e.severity === ThreatLevel.MEDIUM).length,
      low: events.filter(e => e.severity === ThreatLevel.LOW).length
    };

    stats.blocked = status?.threatsBlocked || stats.blocked;
    return stats;
  }, [events, status]);

  // Prepare time series data for charts
  const timeSeriesData = useMemo(() => {
    const hourlyData: Record<string, { time: string; threats: number; blocked: number }> = {};

    events.forEach(event => {
      const hour = new Date(event.timestamp).toISOString().slice(0, 13);
      if (!hourlyData[hour]) {
        hourlyData[hour] = { time: hour, threats: 0, blocked: 0 };
      }
      hourlyData[hour].threats++;
      if (event.blocked) hourlyData[hour].blocked++;
    });

    return Object.values(hourlyData).sort((a, b) => a.time.localeCompare(b.time));
  }, [events]);

  // Event type distribution
  const eventTypeDistribution = useMemo(() => {
    const distribution: Record<string, number> = {};
    events.forEach(event => {
      distribution[event.event_type] = (distribution[event.event_type] || 0) + 1;
    });

    return Object.entries(distribution).map(([type, count]) => ({
      name: type.replace(/_/g, ' ').toUpperCase(),
      value: count
    }));
  }, [events]);

  const handleEventClick = (event: ISecurityEvent) => {
    setSelectedEvent(event);
    setShowEventDetails(true);
  };

  const handleUpdateSecurityRule = async (rule: string, value: any) => {
    try {
      await agiApi.updateSecurityRule(rule, value);
      refetch();
    } catch (error) {
      console.error('Failed to update security rule:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Security Center</h1>
          <p className="text-gray-600 mt-1">Monitor threats and manage security policies</p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusIndicator status={status} />
          <Button variant="primary" size="sm" onClick={refetch}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
      </div>

      {/* Critical Alert */}
      {threatStats.critical > 0 && (
        <Alert
          type="error"
          title="Critical Security Threats Detected"
          message={`${threatStats.critical} critical threat(s) require immediate attention`}
        />
      )}

      {/* Security Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Threats</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{threatStats.total}</p>
                <div className="flex items-center mt-2 text-sm">
                  <span className="text-green-600">
                    {threatStats.blocked} blocked
                  </span>
                </div>
              </div>
              <div className="p-3 bg-red-100 rounded-lg">
                <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Content Filtering</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">
                  {status?.contentFiltering || 'inactive'}
                </p>
                <StatusDot
                  status={status?.contentFiltering === 'active' ? 'online' : 'offline'}
                  label={status?.contentFiltering === 'active' ? 'Active' : 'Inactive'}
                  size="sm"
                />
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Rate Limiting</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">
                  {status?.rateLimiting || 'inactive'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {limits.length} rules active
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Access Control</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">
                  {status?.accessControl || 'Standard'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Level 2 Protection
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Threat Level Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Threat Timeline"
            subtitle="Hourly threat activity and blocked attempts"
          />
          <CardContent>
            {timeSeriesData.length > 0 ? (
              <AreaChartComponent
                data={timeSeriesData}
                areas={[
                  { dataKey: 'threats', color: '#EF4444', name: 'Total Threats' },
                  { dataKey: 'blocked', color: '#10B981', name: 'Blocked' }
                ]}
                xDataKey="time"
                height={250}
              />
            ) : (
              <div className="flex justify-center items-center h-64">
                <p className="text-gray-500">No threat data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Threat Categories"
            subtitle="Distribution by type"
          />
          <CardContent>
            {eventTypeDistribution.length > 0 ? (
              <PieChartComponent
                data={eventTypeDistribution}
                dataKey="value"
                nameKey="name"
                height={250}
              />
            ) : (
              <div className="flex justify-center items-center h-64">
                <p className="text-gray-500">No data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Events Table */}
      <Card>
        <CardHeader
          title="Security Events"
          subtitle="Real-time threat monitoring"
          action={
            <div className="flex items-center space-x-2">
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Severities</option>
                {Object.values(ThreatLevel).map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>

              <select
                value={filterEventType}
                onChange={(e) => setFilterEventType(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                {Object.values(SecurityEventType).map(type => (
                  <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
          }
        />
        <CardContent>
          <LoadingState loading={securityLoading} error={securityError}>
            <SecurityEventsTable
              events={filteredEvents}
              onEventClick={handleEventClick}
            />
          </LoadingState>
        </CardContent>
      </Card>

      {/* Rate Limiting Section */}
      <Card>
        <CardHeader
          title="Rate Limiting"
          subtitle="API rate limit configuration"
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowRateLimitModal(true)}
            >
              Configure Limits
            </Button>
          }
        />
        <CardContent>
          <LoadingState loading={limitsLoading}>
            <RateLimitsTable limits={limits} onUpdate={updateLimit} />
          </LoadingState>
        </CardContent>
      </Card>

      {/* Audit Logs Section */}
      <Card>
        <CardHeader
          title="Security Audit Logs"
          subtitle="Security-related system events"
        />
        <CardContent>
          <LoadingState loading={logsLoading}>
            <AuditLogsTable logs={logs.slice(0, 10)} />
          </LoadingState>
        </CardContent>
      </Card>

      {/* Event Details Modal */}
      {showEventDetails && selectedEvent && (
        <SecurityEventModal
          event={selectedEvent}
          onClose={() => {
            setShowEventDetails(false);
            setSelectedEvent(null);
          }}
        />
      )}

      {/* Rate Limit Configuration Modal */}
      {showRateLimitModal && (
        <RateLimitModal
          limits={limits}
          onUpdate={updateLimit}
          onClose={() => setShowRateLimitModal(false)}
        />
      )}
    </div>
  );
};

/**
 * Status Indicator Component
 */
const StatusIndicator: React.FC<{ status: ISecurityStatus | null }> = ({ status }) => {
  if (!status) return null;

  const isHealthy =
    status.contentFiltering === 'active' &&
    status.rateLimiting === 'active';

  return (
    <div className="flex items-center space-x-2">
      <StatusDot
        status={isHealthy ? 'online' : 'busy'}
        size="sm"
      />
      <span className="text-sm font-medium text-gray-700">
        System {isHealthy ? 'Secure' : 'Vulnerable'}
      </span>
    </div>
  );
};

/**
 * Security Events Table
 */
const SecurityEventsTable: React.FC<{
  events: ISecurityEvent[];
  onEventClick: (event: ISecurityEvent) => void;
}> = ({ events, onEventClick }) => {
  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      render: (value: string) => new Date(value).toLocaleString(),
      sortable: true
    },
    {
      key: 'event_type',
      header: 'Type',
      render: (value: string) => (
        <Badge variant="info" size="sm">
          {value.replace(/_/g, ' ')}
        </Badge>
      ),
      sortable: true
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (value: ThreatLevel) => {
        const colors = {
          [ThreatLevel.LOW]: 'default',
          [ThreatLevel.MEDIUM]: 'warning',
          [ThreatLevel.HIGH]: 'danger',
          [ThreatLevel.CRITICAL]: 'danger'
        };
        return <Badge variant={colors[value] as any} size="sm">{value}</Badge>;
      },
      sortable: true
    },
    {
      key: 'description',
      header: 'Description',
      render: (value: string) => (
        <span className="text-sm text-gray-700 line-clamp-2">{value}</span>
      )
    },
    {
      key: 'source_ip',
      header: 'Source IP',
      render: (value: string) => value || 'Unknown'
    },
    {
      key: 'blocked',
      header: 'Status',
      render: (value: boolean) => (
        <Badge variant={value ? 'success' : 'danger'} size="sm">
          {value ? 'Blocked' : 'Allowed'}
        </Badge>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right' as const,
      render: (_: any, event: ISecurityEvent) => (
        <Button variant="ghost" size="sm" onClick={() => onEventClick(event)}>
          Details
        </Button>
      )
    }
  ];

  return (
    <DataTable
      data={events}
      columns={columns}
      pageSize={10}
      searchable
      searchPlaceholder="Search events..."
    />
  );
};

/**
 * Rate Limits Table
 */
const RateLimitsTable: React.FC<{
  limits: IRateLimit[];
  onUpdate: (rule: string, limit: number, window?: number) => void;
}> = ({ limits, onUpdate }) => {
  const columns = [
    {
      key: 'rule',
      header: 'Rule',
      sortable: true
    },
    {
      key: 'limit',
      header: 'Limit',
      render: (value: number) => <span className="font-medium">{value}</span>
    },
    {
      key: 'window',
      header: 'Window',
      render: (value: number) => `${value}s`
    },
    {
      key: 'current',
      header: 'Current Usage',
      render: (value: number, item: IRateLimit) => (
        <div className="flex items-center space-x-2">
          <ProgressChart
            value={value}
            max={item.limit}
            size="sm"
            color={value > item.limit * 0.8 ? 'red' : 'green'}
          />
          <span className="text-sm">{value}/{item.limit}</span>
        </div>
      )
    },
    {
      key: 'remaining',
      header: 'Remaining',
      render: (value: number) => value || 0
    },
    {
      key: 'reset_at',
      header: 'Reset At',
      render: (value: string) => value ? new Date(value).toLocaleTimeString() : 'N/A'
    }
  ];

  return <Table data={limits} columns={columns} striped compact />;
};

/**
 * Audit Logs Table
 */
const AuditLogsTable: React.FC<{ logs: IAuditLog[] }> = ({ logs }) => {
  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      render: (value: string) => new Date(value).toLocaleString()
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (value: string) => {
        const colors = {
          info: 'info',
          warning: 'warning',
          error: 'danger',
          critical: 'danger'
        };
        return <Badge variant={colors[value as keyof typeof colors] as any} size="sm">{value}</Badge>;
      }
    },
    {
      key: 'event_type',
      header: 'Event',
      render: (value: string) => value.replace(/_/g, ' ')
    },
    {
      key: 'message',
      header: 'Message',
      render: (value: string) => (
        <span className="text-sm text-gray-700 line-clamp-2">{value}</span>
      )
    },
    {
      key: 'user_id',
      header: 'User',
      render: (value: string) => value || 'System'
    }
  ];

  return <Table data={logs} columns={columns} striped compact />;
};

/**
 * Security Event Details Modal
 */
const SecurityEventModal: React.FC<{
  event: ISecurityEvent;
  onClose: () => void;
}> = ({ event, onClose }) => {
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Security Event Details"
      size="lg"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Event ID</p>
            <p className="font-medium">{event.id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Timestamp</p>
            <p className="font-medium">{new Date(event.timestamp).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Type</p>
            <Badge variant="info">{event.event_type.replace(/_/g, ' ')}</Badge>
          </div>
          <div>
            <p className="text-sm text-gray-600">Severity</p>
            <Badge variant={event.severity === ThreatLevel.CRITICAL ? 'danger' : 'warning'}>
              {event.severity}
            </Badge>
          </div>
          <div>
            <p className="text-sm text-gray-600">Source IP</p>
            <p className="font-medium">{event.source_ip || 'Unknown'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <Badge variant={event.blocked ? 'success' : 'danger'}>
              {event.blocked ? 'Blocked' : 'Allowed'}
            </Badge>
          </div>
        </div>

        <div>
          <p className="text-sm text-gray-600 mb-2">Description</p>
          <p className="text-gray-900">{event.description}</p>
        </div>

        {event.details && (
          <div>
            <p className="text-sm text-gray-600 mb-2">Additional Details</p>
            <pre className="bg-gray-100 p-3 rounded-lg text-sm overflow-auto">
              {JSON.stringify(event.details, null, 2)}
            </pre>
          </div>
        )}

        {event.remediation && (
          <div>
            <p className="text-sm text-gray-600 mb-2">Remediation</p>
            <Alert type="info" message={event.remediation} />
          </div>
        )}
      </div>

      <div className="flex justify-end mt-6">
        <Button onClick={onClose}>Close</Button>
      </div>
    </Modal>
  );
};

/**
 * Rate Limit Configuration Modal
 */
const RateLimitModal: React.FC<{
  limits: IRateLimit[];
  onUpdate: (rule: string, limit: number, window?: number) => void;
  onClose: () => void;
}> = ({ limits, onUpdate, onClose }) => {
  const [selectedRule, setSelectedRule] = useState(limits[0]?.rule || '');
  const [newLimit, setNewLimit] = useState(limits[0]?.limit || 100);
  const [newWindow, setNewWindow] = useState(limits[0]?.window || 60);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdate(selectedRule, newLimit, newWindow);
    onClose();
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Configure Rate Limits"
      size="md"
    >
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rule
            </label>
            <select
              value={selectedRule}
              onChange={(e) => {
                const rule = limits.find(l => l.rule === e.target.value);
                setSelectedRule(e.target.value);
                if (rule) {
                  setNewLimit(rule.limit);
                  setNewWindow(rule.window);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {limits.map(limit => (
                <option key={limit.rule} value={limit.rule}>{limit.rule}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Request Limit
            </label>
            <input
              type="number"
              value={newLimit}
              onChange={(e) => setNewLimit(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Time Window (seconds)
            </label>
            <input
              type="number"
              value={newWindow}
              onChange={(e) => setNewWindow(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              required
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit">
            Update Limit
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default SecurityCenter;