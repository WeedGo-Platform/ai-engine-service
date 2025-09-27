import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, Lock, Activity, TrendingUp } from 'lucide-react';
import { SecurityData, SecurityEvent } from '../../types';
import { agiApi } from '../../services/api';
import SecurityTrendsChart from '../charts/SecurityTrendsChart';

interface SecurityTabProps {
  securityData: SecurityData | null;
  onRefresh: () => void;
}

const SecurityTab: React.FC<SecurityTabProps> = ({ securityData, onRefresh }) => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [threats, setThreats] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);

  useEffect(() => {
    loadSecurityData();
    const interval = setInterval(loadSecurityData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadSecurityData = async () => {
    try {
      const [eventsData, threatsData] = await Promise.all([
        agiApi.getSecurityEvents(50),
        agiApi.getThreats()
      ]);
      setEvents(eventsData);
      setThreats(threatsData);

      const trends = eventsData.slice(0, 20).reverse().map((event: any, idx: number) => ({
        time: event.timestamp || new Date(Date.now() - (20 - idx) * 300000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        threats: event.threat_count || 0,
        blocked: event.blocked_count || 0,
        severity: event.severity_score || 0
      }));
      setTrendData(trends);
    } catch (error) {
      console.error('Failed to load security data:', error);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Security Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Security Status</h3>
            <Shield className={`h-6 w-6 ${
              securityData?.contentFiltering === 'active' ? 'text-green-500' : 'text-yellow-500'
            }`} />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Content Filtering</span>
              <span className="text-sm font-semibold capitalize">{securityData?.contentFiltering || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Rate Limiting</span>
              <span className="text-sm font-semibold capitalize">{securityData?.rateLimiting || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Access Control</span>
              <span className="text-sm font-semibold">{securityData?.accessControl || '--'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Threat Monitoring</h3>
            <AlertTriangle className="h-6 w-6 text-red-500" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Threats Blocked</span>
              <span className="text-2xl font-bold text-red-600">{securityData?.threatsBlocked || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Events</span>
              <span className="text-sm font-semibold">{securityData?.totalEvents || 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Active Rules</h3>
            <Lock className="h-6 w-6 text-blue-500" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Content Filters</span>
              <span className="text-sm font-semibold">{securityData?.activeRules?.content_filter || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Rate Limits</span>
              <span className="text-sm font-semibold">{securityData?.activeRules?.rate_limits || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Trends Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Trends</h3>
        <SecurityTrendsChart data={trendData} />
      </div>

      {/* Security Events */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Security Events</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {events.map((event) => (
            <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{event.message}</p>
                <p className="text-xs text-gray-500">{event.timestamp}</p>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                event.severity === 'critical' ? 'bg-red-100 text-red-700' :
                event.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                event.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-green-100 text-green-700'
              }`}>
                {event.severity}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SecurityTab;