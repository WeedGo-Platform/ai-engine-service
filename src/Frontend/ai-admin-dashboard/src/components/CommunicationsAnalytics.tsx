import React from 'react';
import {
  Send,
  Mail,
  MessageSquare,
  Bell,
  CheckCircle2,
  Eye,
  DollarSign,
  Target,
  Activity,
  MousePointer,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

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

interface CommunicationsAnalyticsProps {
  analyticsData: AnalyticsData;
  selectedDateRange: string;
  onDateRangeChange: (range: string) => void;
  onRefresh: () => void;
}

const CommunicationsAnalytics: React.FC<CommunicationsAnalyticsProps> = ({
  analyticsData,
  selectedDateRange,
  onDateRangeChange,
  onRefresh
}) => {
  return (
    <div className="space-y-6">
      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Analytics Dashboard</h3>
          <div className="flex items-center space-x-2">
            <select
              value={selectedDateRange}
              onChange={(e) => onDateRangeChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
            <button
              onClick={onRefresh}
              className="p-2 text-gray-600 hover:text-gray-900"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Delivery Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Sent</p>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.deliveryMetrics.total_sent.toLocaleString()}
              </p>
            </div>
            <Send className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Delivery Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.deliveryMetrics.delivery_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-1" />
                +2.3% vs last period
              </p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Open Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.engagementMetrics.open_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-1" />
                +5.7% vs last period
              </p>
            </div>
            <Eye className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Click Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.engagementMetrics.click_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-red-600 flex items-center mt-1">
                <ArrowDownRight className="w-3 h-3 mr-1" />
                -1.2% vs last period
              </p>
            </div>
            <MousePointer className="w-8 h-8 text-indigo-600" />
          </div>
        </div>
      </div>

      {/* Channel Performance */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Channel Performance</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Email Channel */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Mail className="w-5 h-5 text-blue-600" />
                  <span className="font-medium">Email</span>
                </div>
                <span className="text-sm text-gray-500">
                  ${analyticsData.channelPerformance.email.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Sent</span>
                    <span className="font-medium">
                      {analyticsData.channelPerformance.email.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Delivered</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.email.delivered / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.delivered / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Opened</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.email.opened / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.opened / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Clicked</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.email.clicked / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.clicked / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* SMS Channel */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-5 h-5 text-green-600" />
                  <span className="font-medium">SMS</span>
                </div>
                <span className="text-sm text-gray-500">
                  ${analyticsData.channelPerformance.sms.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Sent</span>
                    <span className="font-medium">
                      {analyticsData.channelPerformance.sms.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Delivered</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.sms.delivered / analyticsData.channelPerformance.sms.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.sms.delivered / analyticsData.channelPerformance.sms.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    <div className="flex justify-between">
                      <span>Avg. Cost/MSG</span>
                      <span className="font-medium">
                        ${(analyticsData.channelPerformance.sms.cost / analyticsData.channelPerformance.sms.sent).toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Push Channel */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Bell className="w-5 h-5 text-orange-600" />
                  <span className="font-medium">Push</span>
                </div>
                <span className="text-sm text-gray-500">
                  ${analyticsData.channelPerformance.push.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Sent</span>
                    <span className="font-medium">
                      {analyticsData.channelPerformance.push.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-orange-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Delivered</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.push.delivered / analyticsData.channelPerformance.push.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.push.delivered / analyticsData.channelPerformance.push.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Opened</span>
                    <span className="font-medium">
                      {((analyticsData.channelPerformance.push.opened / analyticsData.channelPerformance.push.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.push.opened / analyticsData.channelPerformance.push.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Campaigns */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Top Performing Campaigns</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analyticsData.topCampaigns.map((campaign, index) => (
                <div key={campaign.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-purple-600">
                        {index + 1}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{campaign.name}</p>
                      <p className="text-xs text-gray-500">
                        {campaign.sent.toLocaleString()} sent • {campaign.engagement_rate.toFixed(1)}% engagement
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-green-600">+{campaign.roi}%</p>
                    <p className="text-xs text-gray-500">ROI</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Segment Performance */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Segment Performance</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analyticsData.segmentPerformance.map(segment => (
                <div key={segment.segment} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        {segment.segment}
                      </span>
                      <span className="text-sm text-gray-500">
                        {segment.engagement_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full"
                        style={{ width: `${segment.engagement_rate}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-gray-500">
                        {segment.campaigns} campaigns
                      </span>
                      <span className="text-xs text-gray-500">
                        {segment.recipients.toLocaleString()} recipients
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Cost Analysis */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Cost Analysis</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <DollarSign className="w-5 h-5 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.total_spent.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Total Spent</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Mail className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.email_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Email</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <MessageSquare className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.sms_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">SMS</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Bell className="w-5 h-5 text-orange-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.push_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Push</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Activity className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.avg_cost_per_message.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500">Per Message</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Target className="w-5 h-5 text-indigo-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${analyticsData.costAnalysis.avg_cost_per_engagement.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500">Per Engagement</p>
            </div>
          </div>
        </div>
      </div>

      {/* Engagement Timeline */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Engagement Timeline</h3>
        </div>
        <div className="p-6">
          <div className="h-64 flex items-end justify-between space-x-2">
            {analyticsData.timeSeriesData.map((day, index) => {
              const maxSent = Math.max(...analyticsData.timeSeriesData.map(d => d.sent));
              const sentHeight = (day.sent / maxSent) * 100;
              const openHeight = (day.opened / day.sent) * sentHeight;
              const clickHeight = (day.clicked / day.sent) * sentHeight;

              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div className="w-full flex flex-col justify-end h-48 relative">
                    <div
                      className="w-full bg-gray-200 rounded-t"
                      style={{ height: `${sentHeight}%` }}
                      title={`Sent: ${day.sent}`}
                    >
                      <div
                        className="w-full bg-blue-400 rounded-t"
                        style={{ height: `${(openHeight / sentHeight) * 100}%` }}
                        title={`Opened: ${day.opened}`}
                      >
                        <div
                          className="w-full bg-purple-600 rounded-t"
                          style={{ height: `${(clickHeight / openHeight) * 100}%` }}
                          title={`Clicked: ${day.clicked}`}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 transform -rotate-45">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </p>
                </div>
              );
            })}
          </div>
          <div className="flex items-center justify-center mt-4 space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-200 rounded"></div>
              <span className="text-xs text-gray-600">Sent</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-400 rounded"></div>
              <span className="text-xs text-gray-600">Opened</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-purple-600 rounded"></div>
              <span className="text-xs text-gray-600">Clicked</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunicationsAnalytics;