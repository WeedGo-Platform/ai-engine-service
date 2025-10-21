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
    <div className="space-y-4 sm:space-y-6">
      {/* Date Range Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3 sm:p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Analytics Dashboard</h3>
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <select
              value={selectedDateRange}
              onChange={(e) => onDateRangeChange(e.target.value)}
              className="flex-1 sm:flex-none px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
            <button
              onClick={onRefresh}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white active:scale-95 transition-colors touch-manipulation"
              aria-label="Refresh analytics data"
            >
              <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Delivery Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Total Sent</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {analyticsData.deliveryMetrics.total_sent.toLocaleString()}
              </p>
            </div>
            <Send className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Delivery Rate</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {analyticsData.deliveryMetrics.delivery_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-1" />
                +2.3% vs last period
              </p>
            </div>
            <CheckCircle2 className="w-6 h-6 sm:w-8 sm:h-8 text-green-600 dark:text-green-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Open Rate</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {analyticsData.engagementMetrics.open_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-1" />
                +5.7% vs last period
              </p>
            </div>
            <Eye className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Click Rate</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {analyticsData.engagementMetrics.click_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-red-600 dark:text-red-400 flex items-center mt-1">
                <ArrowDownRight className="w-3 h-3 mr-1" />
                -1.2% vs last period
              </p>
            </div>
            <MousePointer className="w-6 h-6 sm:w-8 sm:h-8 text-indigo-600 dark:text-indigo-400" />
          </div>
        </div>
      </div>

      {/* Channel Performance */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Channel Performance</h3>
        </div>
        <div className="p-4 sm:p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
            {/* Email Channel */}
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 sm:p-4">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center space-x-2">
                  <Mail className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Email</span>
                </div>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  ${analyticsData.channelPerformance.email.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Sent</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {analyticsData.channelPerformance.email.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Delivered</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.email.delivered / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-600 dark:bg-green-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.delivered / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Opened</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.email.opened / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-purple-600 dark:bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.opened / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Clicked</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.email.clicked / analyticsData.channelPerformance.email.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.email.clicked / analyticsData.channelPerformance.email.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* SMS Channel */}
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 sm:p-4">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 dark:text-green-400" />
                  <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">SMS</span>
                </div>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  ${analyticsData.channelPerformance.sms.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Sent</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {analyticsData.channelPerformance.sms.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-green-600 dark:bg-green-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Delivered</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.sms.delivered / analyticsData.channelPerformance.sms.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.sms.delivered / analyticsData.channelPerformance.sms.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div className="mt-3 sm:mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex justify-between">
                      <span>Avg. Cost/MSG</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        ${(analyticsData.channelPerformance.sms.cost / analyticsData.channelPerformance.sms.sent).toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Push Channel */}
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 sm:p-4">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center space-x-2">
                  <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600 dark:text-orange-400" />
                  <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Push</span>
                </div>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  ${analyticsData.channelPerformance.push.cost.toFixed(2)}
                </span>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Sent</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {analyticsData.channelPerformance.push.sent.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-orange-600 dark:bg-orange-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Delivered</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.push.delivered / analyticsData.channelPerformance.push.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-yellow-600 dark:bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.push.delivered / analyticsData.channelPerformance.push.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Opened</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {((analyticsData.channelPerformance.push.opened / analyticsData.channelPerformance.push.sent) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-purple-600 dark:bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(analyticsData.channelPerformance.push.opened / analyticsData.channelPerformance.push.sent) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Top Campaigns */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Top Performing Campaigns</h3>
          </div>
          <div className="p-4 sm:p-6">
            <div className="space-y-3 sm:space-y-4">
              {analyticsData.topCampaigns.map((campaign, index) => (
                <div key={campaign.id} className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1 min-w-0">
                    <div className="w-7 h-7 sm:w-8 sm:h-8 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-xs sm:text-sm font-semibold text-purple-600 dark:text-purple-400">
                        {index + 1}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">{campaign.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {campaign.sent.toLocaleString()} sent • {campaign.engagement_rate.toFixed(1)}% engagement
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs sm:text-sm font-semibold text-green-600 dark:text-green-400 whitespace-nowrap">+{campaign.roi}%</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">ROI</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Segment Performance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Segment Performance</h3>
          </div>
          <div className="p-4 sm:p-6">
            <div className="space-y-3 sm:space-y-4">
              {analyticsData.segmentPerformance.map(segment => (
                <div key={segment.segment} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">
                        {segment.segment}
                      </span>
                      <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 ml-2 whitespace-nowrap">
                        {segment.engagement_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-purple-600 dark:from-purple-400 dark:to-purple-500 h-2 rounded-full"
                        style={{ width: `${segment.engagement_rate}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {segment.campaigns} campaigns
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Cost Analysis</h3>
        </div>
        <div className="p-4 sm:p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 dark:text-gray-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.total_spent.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total Spent</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <Mail className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.email_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Email</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 dark:text-green-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.sms_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">SMS</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.push_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Push</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.avg_cost_per_message.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Per Message</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1 sm:mb-2">
                <Target className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${analyticsData.costAnalysis.avg_cost_per_engagement.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Per Engagement</p>
            </div>
          </div>
        </div>
      </div>

      {/* Engagement Timeline */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Engagement Timeline</h3>
        </div>
        <div className="p-4 sm:p-6">
          <div className="h-48 sm:h-64 flex items-end justify-between space-x-1 sm:space-x-2">
            {analyticsData.timeSeriesData.map((day, index) => {
              const maxSent = Math.max(...analyticsData.timeSeriesData.map(d => d.sent));
              const sentHeight = (day.sent / maxSent) * 100;
              const openHeight = (day.opened / day.sent) * sentHeight;
              const clickHeight = (day.clicked / day.sent) * sentHeight;

              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div className="w-full flex flex-col justify-end h-36 sm:h-48 relative">
                    <div
                      className="w-full bg-gray-200 dark:bg-gray-700 rounded-t"
                      style={{ height: `${sentHeight}%` }}
                      title={`Sent: ${day.sent}`}
                    >
                      <div
                        className="w-full bg-blue-400 dark:bg-blue-500 rounded-t"
                        style={{ height: `${(openHeight / sentHeight) * 100}%` }}
                        title={`Opened: ${day.opened}`}
                      >
                        <div
                          className="w-full bg-purple-600 dark:bg-purple-500 rounded-t"
                          style={{ height: `${(clickHeight / openHeight) * 100}%` }}
                          title={`Clicked: ${day.clicked}`}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 sm:mt-2 transform -rotate-45 truncate">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </p>
                </div>
              );
            })}
          </div>
          <div className="flex flex-wrap items-center justify-center mt-3 sm:mt-4 gap-3 sm:gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <span className="text-xs text-gray-600 dark:text-gray-400">Sent</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-400 dark:bg-blue-500 rounded"></div>
              <span className="text-xs text-gray-600 dark:text-gray-400">Opened</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-purple-600 dark:bg-purple-500 rounded"></div>
              <span className="text-xs text-gray-600 dark:text-gray-400">Clicked</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunicationsAnalytics;