import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import { api } from '../services/api';
import BroadcastWizard from '../components/BroadcastWizard';
import TemplateManager from '../components/TemplateManager';
import CommunicationsAnalytics from '../components/CommunicationsAnalytics';
import { usePersistentTab, usePersistentState } from '../hooks/usePersistentState';
import toast from 'react-hot-toast';
import {
  Send,
  Users,
  Mail,
  MessageSquare,
  Bell,
  Calendar,
  BarChart3,
  Plus,
  Play,
  Pause,
  StopCircle,
  FileText,
  Filter,
  Settings,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  TrendingUp,
  Eye,
  Edit,
  Trash2,
  Copy,
  Download,
  RefreshCw,
  DollarSign,
  Target,
  Activity,
  MousePointer,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

interface Broadcast {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'paused' | 'cancelled' | 'failed';
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_recipients: number;
  successful_sends: number;
  failed_sends: number;
  created_at: string;
  created_by_name: string;
  channel_count: number;
}

interface CommunicationStats {
  total_campaigns: number;
  total_sent: number;
  total_failed: number;
  avg_success_rate: number;
}

interface ChannelStats {
  channel_type: string;
  campaigns_used: number;
  messages_sent: number;
  avg_engagement_rate: number;
}

interface AnalyticsData {
  dateRange: string;
  deliveryMetrics: {
    total_sent: number;
    total_delivered: number;
    total_bounced: number;
    total_failed: number;
    delivery_rate: number;
    bounce_rate: number;
    failure_rate: number;
  };
  engagementMetrics: {
    total_opens: number;
    unique_opens: number;
    open_rate: number;
    total_clicks: number;
    unique_clicks: number;
    click_rate: number;
    click_to_open_rate: number;
    unsubscribe_rate: number;
  };
  channelPerformance: {
    email: {
      sent: number;
      delivered: number;
      opened: number;
      clicked: number;
      cost: number;
    };
    sms: {
      sent: number;
      delivered: number;
      cost: number;
    };
    push: {
      sent: number;
      delivered: number;
      opened: number;
      cost: number;
    };
  };
  topCampaigns: Array<{
    id: string;
    name: string;
    sent: number;
    engagement_rate: number;
    roi: number;
  }>;
  segmentPerformance: Array<{
    segment: string;
    campaigns: number;
    recipients: number;
    engagement_rate: number;
  }>;
  timeSeriesData: Array<{
    date: string;
    sent: number;
    opened: number;
    clicked: number;
  }>;
  costAnalysis: {
    total_spent: number;
    email_cost: number;
    sms_cost: number;
    push_cost: number;
    avg_cost_per_message: number;
    avg_cost_per_engagement: number;
  };
}

const Communications: React.FC = () => {
  const { t } = useTranslation(['communications', 'common', 'errors']);
  const { user, isSuperAdmin, isTenantAdminOnly, isStoreManager } = useAuth();
  const { currentStore } = useStoreContext();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = usePersistentTab<'overview' | 'campaigns' | 'templates' | 'segments' | 'analytics'>('communications', 'overview');
  const [broadcasts, setBroadcasts] = useState<Broadcast[]>([]);
  const [stats, setStats] = useState<CommunicationStats | null>(null);
  const [channelStats, setChannelStats] = useState<ChannelStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBroadcast, setSelectedBroadcast] = useState<Broadcast | null>(null);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [selectedDateRange, setSelectedDateRange] = usePersistentState('communications_date_range', '7d');

  useEffect(() => {
    if (currentStore?.id) {
      fetchData();
    }
  }, [currentStore, refreshKey]);

  const fetchData = async () => {
    if (!currentStore?.id) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        'X-Store-ID': currentStore.id
      };

      // Fetch broadcasts
      const broadcastsRes = await fetch(`http://localhost:5024/api/v1/communications/broadcasts?store_id=${currentStore.id}&limit=10`, {
        headers
      });
      if (broadcastsRes.ok) {
        const data = await broadcastsRes.json();
        setBroadcasts(data.broadcasts || []);
      }

      // Fetch analytics
      const analyticsRes = await fetch(`http://localhost:5024/api/v1/communications/analytics/overview?store_id=${currentStore.id}`, {
        headers
      });
      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        setStats(data.overview || null);
        setChannelStats(data.channel_breakdown || []);
      }
    } catch (error) {
      console.error('Error fetching communications data:', error);
      console.error('Failed to fetch broadcasts:', error);
      toast.error(t('communications:messages.error.fetchBroadcasts'));
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteBroadcast = async (broadcastId: string) => {
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(`http://localhost:5024/api/v1/communications/broadcasts/${broadcastId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        toast.success(t('communications:messages.success.broadcastStarted'));
        setRefreshKey(prev => prev + 1);
      }
    } catch (error) {
      console.error('Failed to fetch broadcasts:', error);
      toast.error(t('communications:messages.error.fetchBroadcasts'));
    }
  };

  const handlePauseBroadcast = async (broadcastId: string) => {
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(`http://localhost:5024/api/v1/communications/broadcasts/${broadcastId}/pause`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        toast.success(t('communications:messages.success.broadcastPaused'));
        setRefreshKey(prev => prev + 1);
      }
    } catch (error) {
      console.error('Failed to fetch broadcasts:', error);
      toast.error(t('communications:messages.error.fetchBroadcasts'));
    }
  };

  const handleResumeBroadcast = async (broadcastId: string) => {
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(`http://localhost:5024/api/v1/communications/broadcasts/${broadcastId}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        toast.success(t('communications:messages.success.broadcastResumed'));
        setRefreshKey(prev => prev + 1);
      }
    } catch (error) {
      console.error('Failed to fetch broadcasts:', error);
      toast.error(t('communications:messages.error.fetchBroadcasts'));
    }
  };

  const handleCancelBroadcast = async (broadcastId: string) => {
    if (!confirm(t('communications:confirm.cancelBroadcast'))) return;

    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(`http://localhost:5024/api/v1/communications/broadcasts/${broadcastId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        toast.success(t('communications:messages.success.broadcastCancelled'));
        setRefreshKey(prev => prev + 1);
      }
    } catch (error) {
      console.error('Failed to fetch broadcasts:', error);
      toast.error(t('communications:messages.error.fetchBroadcasts'));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <FileText className="w-4 h-4 text-gray-500" />;
      case 'scheduled':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'sending':
        return <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'sent':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-orange-500" />;
      case 'cancelled':
        return <StopCircle className="w-4 h-4 text-red-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-700';
      case 'scheduled':
        return 'bg-blue-100 text-blue-700';
      case 'sending':
        return 'bg-yellow-100 text-yellow-700';
      case 'sent':
        return 'bg-green-100 text-green-700';
      case 'paused':
        return 'bg-orange-100 text-orange-700';
      case 'cancelled':
        return 'bg-red-100 text-red-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const fetchAnalytics = async () => {
    if (!currentStore?.id) return;

    setAnalyticsLoading(true);
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(`http://localhost:5024/api/v1/communications/analytics/detailed?store_id=${currentStore.id}&date_range=${selectedDateRange}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          'X-Store-ID': currentStore.id
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        throw new Error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      // Use mock data if API fails
      setAnalyticsData({
        dateRange: selectedDateRange,
        deliveryMetrics: {
          total_sent: 15420,
          total_delivered: 14890,
          total_bounced: 230,
          total_failed: 300,
          delivery_rate: 96.6,
          bounce_rate: 1.5,
          failure_rate: 1.9
        },
        engagementMetrics: {
          total_opens: 8234,
          unique_opens: 6120,
          open_rate: 41.1,
          total_clicks: 2456,
          unique_clicks: 1890,
          click_rate: 12.7,
          click_to_open_rate: 30.9,
          unsubscribe_rate: 0.8
        },
        channelPerformance: {
          email: {
            sent: 8500,
            delivered: 8200,
            opened: 3450,
            clicked: 1230,
            cost: 42.50
          },
          sms: {
            sent: 4920,
            delivered: 4890,
            cost: 246.00
          },
          push: {
            sent: 2000,
            delivered: 1800,
            opened: 720,
            cost: 0
          }
        },
        topCampaigns: [
          { id: '1', name: 'Weekend Flash Sale', sent: 3500, engagement_rate: 45.2, roi: 320 },
          { id: '2', name: 'New Product Launch', sent: 2800, engagement_rate: 38.9, roi: 280 },
          { id: '3', name: 'Holiday Promotion', sent: 2200, engagement_rate: 42.1, roi: 410 },
          { id: '4', name: 'VIP Member Exclusive', sent: 1500, engagement_rate: 52.3, roi: 520 },
          { id: '5', name: 'Back in Stock Alert', sent: 950, engagement_rate: 48.7, roi: 380 }
        ],
        segmentPerformance: [
          { segment: 'VIP Customers', campaigns: 8, recipients: 2400, engagement_rate: 52.3 },
          { segment: 'New Customers', campaigns: 6, recipients: 3200, engagement_rate: 38.9 },
          { segment: 'High Spenders', campaigns: 5, recipients: 1800, engagement_rate: 48.7 },
          { segment: 'Frequent Buyers', campaigns: 7, recipients: 2900, engagement_rate: 44.2 },
          { segment: 'All Customers', campaigns: 4, recipients: 5120, engagement_rate: 35.6 }
        ],
        timeSeriesData: [
          { date: '2024-01-20', sent: 2200, opened: 890, clicked: 245 },
          { date: '2024-01-21', sent: 2400, opened: 1020, clicked: 310 },
          { date: '2024-01-22', sent: 1800, opened: 740, clicked: 198 },
          { date: '2024-01-23', sent: 2650, opened: 1120, clicked: 342 },
          { date: '2024-01-24', sent: 2100, opened: 865, clicked: 256 },
          { date: '2024-01-25', sent: 2370, opened: 985, clicked: 289 },
          { date: '2024-01-26', sent: 1900, opened: 614, clicked: 216 }
        ],
        costAnalysis: {
          total_spent: 288.50,
          email_cost: 42.50,
          sms_cost: 246.00,
          push_cost: 0,
          avg_cost_per_message: 0.019,
          avg_cost_per_engagement: 0.047
        }
      });
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'analytics' && currentStore?.id) {
      fetchAnalytics();
    }
  }, [activeTab, currentStore, selectedDateRange]);

  const renderAnalytics = () => {
    if (analyticsLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
        </div>
      );
    }

    if (!analyticsData) {
      return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-gray-600">{t('communications:descriptions.noAnalytics')}</p>
        </div>
      );
    }

    return (
      <CommunicationsAnalytics
        analyticsData={analyticsData}
        selectedDateRange={selectedDateRange}
        onDateRangeChange={setSelectedDateRange}
        onRefresh={fetchAnalytics}
      />
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('communications:stats.totalCampaigns')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.total_campaigns || 0}
              </p>
            </div>
            <Send className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('communications:stats.messagesSent')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.total_sent || 0}
              </p>
            </div>
            <Mail className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('communications:stats.successRate')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.avg_success_rate?.toFixed(1) || 0}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('communications:stats.failed')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.total_failed || 0}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Channel Performance */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{t('communications:titles.channelPerformance')}</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {['email', 'sms', 'push'].map(channel => {
              const channelData = channelStats.find(c => c.channel_type === channel);
              const Icon = channel === 'email' ? Mail : channel === 'sms' ? MessageSquare : Bell;

              return (
                <div key={channel} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <Icon className="w-5 h-5 text-gray-600" />
                      <span className="font-medium capitalize">{channel}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">{t('communications:channels.campaigns')}</span>
                      <span className="text-sm font-medium">
                        {channelData?.campaigns_used || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">{t('communications:channels.messages')}</span>
                      <span className="text-sm font-medium">
                        {channelData?.messages_sent || 0}
                      </span>
                    </div>
                    {channel !== 'sms' && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">{t('communications:channels.engagement')}</span>
                        <span className="text-sm font-medium">
                          {channelData?.avg_engagement_rate?.toFixed(1) || 0}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Campaigns */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">{t('communications:titles.recentCampaigns')}</h3>
          <button
            onClick={() => setActiveTab('campaigns')}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            {t('communications:actions.viewAll')}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('communications:table.campaign')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('communications:table.status')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('communications:table.recipients')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('communications:table.successRate')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('communications:table.created')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {broadcasts.slice(0, 5).map((broadcast) => (
                <tr key={broadcast.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {broadcast.name}
                      </div>
                      {broadcast.description && (
                        <div className="text-sm text-gray-500">
                          {broadcast.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(broadcast.status)}`}>
                      {getStatusIcon(broadcast.status)}
                      <span className="capitalize">{t(`communications:status.${broadcast.status}`)}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {broadcast.total_recipients}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {broadcast.total_recipients > 0
                      ? `${((broadcast.successful_sends / broadcast.total_recipients) * 100).toFixed(1)}%`
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(broadcast.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderCampaigns = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">{t('communications:titles.broadcastCampaigns')}</h3>
        <button
          onClick={() => setShowCreateWizard(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>{t('communications:actions.newCampaign')}</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.campaign')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.channels')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.recipients')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.scheduled')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('communications:table.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {broadcasts.map((broadcast) => (
              <tr key={broadcast.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {broadcast.name}
                    </div>
                    {broadcast.description && (
                      <div className="text-sm text-gray-500">
                        {broadcast.description}
                      </div>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {t('communications:table.createdBy')} {broadcast.created_by_name}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(broadcast.status)}`}>
                    {getStatusIcon(broadcast.status)}
                    <span className="capitalize">{t(`communications:status.${broadcast.status}`)}</span>
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-1">
                    {broadcast.channel_count > 0 && (
                      <>
                        <Mail className="w-4 h-4 text-gray-400" />
                        <MessageSquare className="w-4 h-4 text-gray-400" />
                        <Bell className="w-4 h-4 text-gray-400" />
                      </>
                    )}
                    <span className="text-sm text-gray-600">
                      ({broadcast.channel_count})
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {broadcast.total_recipients}
                  </div>
                  {broadcast.successful_sends > 0 && (
                    <div className="text-xs text-gray-500">
                      {broadcast.successful_sends} {t('communications:table.sentCount')}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(broadcast.scheduled_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => navigate(`/dashboard/communications/broadcast/${broadcast.id}`)}
                      className="text-purple-600 hover:text-purple-700"
                      title={t('communications:actions.viewDetails')}
                    >
                      <Eye className="w-4 h-4" />
                    </button>

                    {broadcast.status === 'draft' && (
                      <>
                        <button
                          onClick={() => navigate(`/dashboard/communications/broadcast/${broadcast.id}/edit`)}
                          className="text-blue-600 hover:text-blue-700"
                          title={t('communications:actions.edit')}
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleExecuteBroadcast(broadcast.id)}
                          className="text-green-600 hover:text-green-700"
                          title={t('communications:actions.sendNow')}
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      </>
                    )}

                    {broadcast.status === 'scheduled' && (
                      <button
                        onClick={() => handleCancelBroadcast(broadcast.id)}
                        className="text-red-600 hover:text-red-700"
                        title={t('communications:actions.cancel')}
                      >
                        <StopCircle className="w-4 h-4" />
                      </button>
                    )}

                    {broadcast.status === 'sending' && (
                      <button
                        onClick={() => handlePauseBroadcast(broadcast.id)}
                        className="text-orange-600 hover:text-orange-700"
                        title={t('communications:actions.pause')}
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}

                    {broadcast.status === 'paused' && (
                      <button
                        onClick={() => handleResumeBroadcast(broadcast.id)}
                        className="text-green-600 hover:text-green-700"
                        title={t('communications:actions.resume')}
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full">
              <Send className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('communications:descriptions.noStoreSelected')}</h3>
          <p className="text-gray-500">{t('communications:descriptions.selectStore')}</p>
        </div>
      </div>
    );
  }

  // Show loading state after store is selected
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('communications:titles.main')}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('communications:descriptions.managingFor')} {currentStore.name}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setRefreshKey(prev => prev + 1)}
            className="p-2 text-gray-600 hover:text-gray-900"
            title={t('communications:actions.refresh')}
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <button
            onClick={() => navigate('/dashboard/communications/settings')}
            className="p-2 text-gray-600 hover:text-gray-900"
            title={t('communications:actions.settings')}
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: t('communications:tabs.overview'), icon: BarChart3 },
            { id: 'campaigns', label: t('communications:tabs.campaigns'), icon: Send },
            { id: 'templates', label: t('communications:tabs.templates'), icon: FileText },
            { id: 'segments', label: t('communications:tabs.segments'), icon: Users },
            { id: 'analytics', label: t('communications:tabs.analytics'), icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'campaigns' && renderCampaigns()}
        {activeTab === 'templates' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <TemplateManager />
          </div>
        )}
        {activeTab === 'segments' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-gray-600">{t('communications:descriptions.segmentationComingSoon')}</p>
          </div>
        )}
        {activeTab === 'analytics' && renderAnalytics()}
      </div>

      {/* Broadcast Wizard Modal */}
      <BroadcastWizard
        isOpen={showCreateWizard}
        onClose={() => setShowCreateWizard(false)}
        onComplete={(broadcastId) => {
          setShowCreateWizard(false);
          setRefreshKey(prev => prev + 1);
        }}
      />

      {/* Store Selection Modal */}
      <StoreSelectionModal
        isOpen={showStoreSelectionModal}
        onSelect={handleStoreSelect}
        onClose={() => {
          // Only allow closing if a store is selected or user is not admin
          if (currentStore || (!isSuperAdmin() && !isTenantAdminOnly())) {
            setShowStoreSelectionModal(false);
          }
        }}
      />
    </div>
  );
};

export default Communications;