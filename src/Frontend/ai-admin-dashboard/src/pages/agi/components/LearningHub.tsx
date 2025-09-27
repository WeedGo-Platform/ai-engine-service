/**
 * Learning Hub Component
 * AI learning progress monitoring and pattern visualization
 * Following SOLID principles with data-driven insights
 */

import React, { useState, useMemo } from 'react';
import { useLearning, useAsyncData } from '../hooks/useAGI';
import { agiApi } from '../services/agiApi';
import {
  Card, CardHeader, CardContent, CardFooter,
  Table, DataTable,
  Badge, StatusDot,
  Alert, Button, IconButton,
  LineChartComponent, AreaChartComponent, BarChartComponent,
  PieChartComponent, RadarChartComponent,
  ProgressChart, ActivityChart, Sparkline,
  Modal, Tabs,
  LoadingState, Spinner, Skeleton
} from './ui';
import {
  ILearningMetrics, IPattern, IFeedback, IAdaptation,
  ILearningHistory, IFeedbackAnalysis
} from '../types';

/**
 * Main Learning Hub Component
 */
export const LearningHub: React.FC = () => {
  const { metrics, patterns, feedback, loading, error, refetch } = useLearning();
  const [selectedPattern, setSelectedPattern] = useState<IPattern | null>(null);
  const [showPatternDetails, setShowPatternDetails] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [filterPatternType, setFilterPatternType] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('7d');

  // Filter patterns
  const filteredPatterns = useMemo(() => {
    if (filterPatternType === 'all') return patterns;
    return patterns.filter(p => p.type === filterPatternType);
  }, [patterns, filterPatternType]);

  // Calculate learning statistics
  const learningStats = useMemo(() => {
    const positiveCount = feedback.filter(f => f.type === 'positive').length;
    const negativeCount = feedback.filter(f => f.type === 'negative').length;
    const neutralCount = feedback.filter(f => f.type === 'neutral').length;

    return {
      totalPatterns: patterns.length,
      averageConfidence: patterns.reduce((acc, p) => acc + p.confidence, 0) / patterns.length || 0,
      totalFeedback: feedback.length,
      positiveRatio: feedback.length > 0 ? (positiveCount / feedback.length) * 100 : 0,
      negativeRatio: feedback.length > 0 ? (negativeCount / feedback.length) * 100 : 0,
      neutralRatio: feedback.length > 0 ? (neutralCount / feedback.length) * 100 : 0
    };
  }, [patterns, feedback]);

  // Prepare pattern evolution data
  const patternEvolutionData = useMemo(() => {
    const recentPatterns = patterns.slice(0, 10);
    return recentPatterns.map(p => ({
      name: p.name || p.id.slice(0, 8),
      confidence: p.confidence,
      frequency: p.frequency,
      occurrences: p.occurrences || 0
    }));
  }, [patterns]);

  // Prepare feedback sentiment data
  const sentimentData = useMemo(() => [
    { name: 'Positive', value: learningStats.positiveRatio, count: feedback.filter(f => f.type === 'positive').length },
    { name: 'Neutral', value: learningStats.neutralRatio, count: feedback.filter(f => f.type === 'neutral').length },
    { name: 'Negative', value: learningStats.negativeRatio, count: feedback.filter(f => f.type === 'negative').length }
  ], [learningStats, feedback]);

  // Prepare learning metrics history (mock data for demo)
  const metricsHistory = useMemo(() => {
    const days = timeRange === '24h' ? 24 : timeRange === '7d' ? 7 : 30;
    return Array.from({ length: days }, (_, i) => ({
      time: timeRange === '24h' ? `${i}:00` : `Day ${i + 1}`,
      learningRate: Math.max(0, (metrics?.learningRate || 0) + (Math.random() - 0.5) * 10),
      confidence: Math.max(0, (metrics?.confidenceScore || 0) + (Math.random() - 0.5) * 5),
      accuracy: Math.max(0, (metrics?.model_accuracy || 0) * 100 + (Math.random() - 0.5) * 8)
    }));
  }, [metrics, timeRange]);

  // Pattern type distribution
  const patternTypeDistribution = useMemo(() => {
    const distribution: Record<string, number> = {};
    patterns.forEach(p => {
      distribution[p.type] = (distribution[p.type] || 0) + 1;
    });
    return Object.entries(distribution).map(([type, count]) => ({
      name: type.replace(/_/g, ' '),
      value: count
    }));
  }, [patterns]);

  const handlePatternClick = (pattern: IPattern) => {
    setSelectedPattern(pattern);
    setShowPatternDetails(true);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Learning Hub</h1>
          <p className="text-gray-600 mt-1">Monitor AI learning progress and pattern recognition</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <Button variant="primary" size="sm" onClick={refetch}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Learning Rate"
          value={`${metrics?.learningRate || 0}%`}
          change={15}
          icon={<LearningIcon />}
          color="blue"
          sparkline={metricsHistory.map(m => m.learningRate)}
        />
        <MetricCard
          title="Confidence Score"
          value={`${metrics?.confidenceScore || 0}%`}
          change={8}
          icon={<ConfidenceIcon />}
          color="green"
          sparkline={metricsHistory.map(m => m.confidence)}
        />
        <MetricCard
          title="Patterns Detected"
          value={metrics?.patternCount || 0}
          change={12}
          icon={<PatternIcon />}
          color="purple"
          sparkline={[]}
        />
        <MetricCard
          title="Positive Feedback"
          value={`${metrics?.feedbackPositive || 0}%`}
          change={-2}
          icon={<FeedbackIcon />}
          color="yellow"
          sparkline={[]}
        />
      </div>

      {/* Learning Progress Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Learning Metrics Over Time"
            subtitle={`Showing ${timeRange === '24h' ? 'hourly' : 'daily'} progress`}
          />
          <CardContent>
            <LoadingState loading={loading} error={error}>
              <LineChartComponent
                data={metricsHistory}
                lines={[
                  { dataKey: 'learningRate', color: '#3B82F6', name: 'Learning Rate %' },
                  { dataKey: 'confidence', color: '#10B981', name: 'Confidence %' },
                  { dataKey: 'accuracy', color: '#F59E0B', name: 'Accuracy %' }
                ]}
                xDataKey="time"
                height={300}
              />
            </LoadingState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Model Performance"
            subtitle="Current capabilities"
          />
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Improvement Rate</span>
                  <span className="text-sm font-medium">{metrics?.improvement_rate || 0}%</span>
                </div>
                <ProgressChart
                  value={metrics?.improvement_rate || 0}
                  color="blue"
                  size="sm"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Model Accuracy</span>
                  <span className="text-sm font-medium">{((metrics?.model_accuracy || 0) * 100).toFixed(1)}%</span>
                </div>
                <ProgressChart
                  value={(metrics?.model_accuracy || 0) * 100}
                  color="green"
                  size="sm"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Adaptations Today</span>
                  <span className="text-sm font-medium">{metrics?.adaptationsToday || 0}</span>
                </div>
                <div className="flex space-x-1 mt-2">
                  {Array.from({ length: 10 }, (_, i) => (
                    <div
                      key={i}
                      className={`flex-1 h-8 rounded ${
                        i < (metrics?.adaptationsToday || 0) ? 'bg-purple-500' : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pattern Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader
            title="Pattern Recognition"
            subtitle="Discovered patterns and their confidence levels"
            action={
              <select
                value={filterPatternType}
                onChange={(e) => setFilterPatternType(e.target.value)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none"
              >
                <option value="all">All Types</option>
                <option value="conversation_flow">Conversation Flow</option>
                <option value="user_behavior">User Behavior</option>
                <option value="error_pattern">Error Pattern</option>
                <option value="optimization">Optimization</option>
              </select>
            }
          />
          <CardContent>
            <LoadingState loading={loading}>
              {filteredPatterns.length > 0 ? (
                <div className="space-y-3">
                  {filteredPatterns.slice(0, 10).map(pattern => (
                    <PatternCard
                      key={pattern.id}
                      pattern={pattern}
                      onClick={() => handlePatternClick(pattern)}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">No patterns detected</p>
              )}
            </LoadingState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Pattern Distribution"
            subtitle="Breakdown by pattern type"
          />
          <CardContent>
            {patternTypeDistribution.length > 0 ? (
              <PieChartComponent
                data={patternTypeDistribution}
                dataKey="value"
                nameKey="name"
                height={300}
              />
            ) : (
              <div className="flex justify-center items-center h-64">
                <p className="text-gray-500">No pattern data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Feedback Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Feedback Analysis"
            subtitle="User feedback sentiment and trends"
            action={
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowFeedbackModal(true)}
              >
                View All Feedback
              </Button>
            }
          />
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {sentimentData.map(item => (
                <div key={item.name} className="text-center">
                  <div className={`text-3xl font-bold ${
                    item.name === 'Positive' ? 'text-green-600' :
                    item.name === 'Negative' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {item.count}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{item.name}</p>
                  <p className="text-xs text-gray-500">{item.value.toFixed(1)}%</p>
                </div>
              ))}
            </div>

            {feedback.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Recent Feedback</h4>
                {feedback.slice(0, 5).map(fb => (
                  <FeedbackItem key={fb.id} feedback={fb} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Learning Adaptations"
            subtitle="Recent model adjustments"
          />
          <CardContent>
            <div className="space-y-3">
              <AdaptationItem
                type="parameter"
                description="Adjusted confidence threshold"
                impact={12}
                timestamp="2 hours ago"
              />
              <AdaptationItem
                type="strategy"
                description="Enhanced pattern matching"
                impact={8}
                timestamp="5 hours ago"
              />
              <AdaptationItem
                type="model"
                description="Updated response generation"
                impact={15}
                timestamp="1 day ago"
              />
              <AdaptationItem
                type="rule"
                description="Refined filtering rules"
                impact={-3}
                timestamp="2 days ago"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pattern Evolution Chart */}
      <Card>
        <CardHeader
          title="Pattern Evolution"
          subtitle="Top patterns by confidence and frequency"
        />
        <CardContent>
          {patternEvolutionData.length > 0 ? (
            <BarChartComponent
              data={patternEvolutionData}
              bars={[
                { dataKey: 'confidence', color: '#3B82F6', name: 'Confidence %' },
                { dataKey: 'frequency', color: '#10B981', name: 'Frequency' }
              ]}
              xDataKey="name"
              height={250}
            />
          ) : (
            <div className="flex justify-center items-center h-64">
              <p className="text-gray-500">No evolution data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pattern Details Modal */}
      {showPatternDetails && selectedPattern && (
        <PatternDetailsModal
          pattern={selectedPattern}
          onClose={() => {
            setShowPatternDetails(false);
            setSelectedPattern(null);
          }}
        />
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackModal
          feedback={feedback}
          onClose={() => setShowFeedbackModal(false)}
        />
      )}
    </div>
  );
};

/**
 * Metric Card Component
 */
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change: number;
  icon: React.ReactNode;
  color: string;
  sparkline?: number[];
}> = ({ title, value, change, icon, color, sparkline }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    yellow: 'bg-yellow-50 text-yellow-600'
  };

  return (
    <Card>
      <CardContent>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {change > 0 ? '↑' : '↓'} {Math.abs(change)}%
              </span>
            </div>
            {sparkline && sparkline.length > 0 && (
              <div className="mt-3">
                <Sparkline data={sparkline} color={color} height={30} />
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Pattern Card Component
 */
const PatternCard: React.FC<{
  pattern: IPattern;
  onClick: () => void;
}> = ({ pattern, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <Badge variant="info" size="sm">{pattern.type.replace(/_/g, ' ')}</Badge>
            <span className="text-sm font-medium text-gray-900">
              {pattern.name || pattern.id.slice(0, 12)}
            </span>
          </div>
          <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
            <span>Confidence: {pattern.confidence}%</span>
            <span>Frequency: {pattern.frequency}</span>
            <span>Last: {new Date(pattern.last_seen).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="text-right">
          <ProgressChart
            value={pattern.confidence}
            size="sm"
            color={pattern.confidence > 80 ? 'green' : pattern.confidence > 50 ? 'yellow' : 'red'}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * Feedback Item Component
 */
const FeedbackItem: React.FC<{ feedback: IFeedback }> = ({ feedback }) => {
  const typeColors = {
    positive: 'bg-green-100 text-green-800',
    negative: 'bg-red-100 text-red-800',
    neutral: 'bg-gray-100 text-gray-800'
  };

  return (
    <div className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-50">
      <div className={`px-2 py-1 rounded text-xs font-medium ${typeColors[feedback.type]}`}>
        {feedback.type}
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-700 line-clamp-2">{feedback.message}</p>
        <p className="text-xs text-gray-500 mt-1">
          {new Date(feedback.timestamp).toLocaleString()}
          {feedback.rating && ` • Rating: ${feedback.rating}/5`}
        </p>
      </div>
    </div>
  );
};

/**
 * Adaptation Item Component
 */
const AdaptationItem: React.FC<{
  type: string;
  description: string;
  impact: number;
  timestamp: string;
}> = ({ type, description, impact, timestamp }) => {
  const typeIcons = {
    parameter: '⚙️',
    strategy: '🎯',
    model: '🤖',
    rule: '📋'
  };

  return (
    <div className="flex items-start space-x-3">
      <span className="text-lg">{typeIcons[type as keyof typeof typeIcons]}</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{description}</p>
        <div className="flex items-center space-x-3 mt-1">
          <span className="text-xs text-gray-500">{timestamp}</span>
          <span className={`text-xs font-medium ${impact > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {impact > 0 ? '+' : ''}{impact}% impact
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Pattern Details Modal
 */
const PatternDetailsModal: React.FC<{
  pattern: IPattern;
  onClose: () => void;
}> = ({ pattern, onClose }) => {
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Pattern Details"
      size="lg"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Pattern ID</p>
            <p className="font-medium">{pattern.id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Type</p>
            <Badge variant="info">{pattern.type.replace(/_/g, ' ')}</Badge>
          </div>
          <div>
            <p className="text-sm text-gray-600">Confidence</p>
            <div className="flex items-center space-x-2">
              <ProgressChart value={pattern.confidence} size="sm" />
              <span className="font-medium">{pattern.confidence}%</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600">Frequency</p>
            <p className="font-medium">{pattern.frequency}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">First Seen</p>
            <p className="font-medium">
              {pattern.first_seen ? new Date(pattern.first_seen).toLocaleString() : 'Unknown'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Last Seen</p>
            <p className="font-medium">{new Date(pattern.last_seen).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Occurrences</p>
            <p className="font-medium">{pattern.occurrences || 0}</p>
          </div>
        </div>

        {pattern.evolution && pattern.evolution.length > 0 && (
          <div>
            <p className="text-sm text-gray-600 mb-2">Evolution History</p>
            <LineChartComponent
              data={pattern.evolution.map(e => ({
                time: new Date(e.timestamp).toLocaleDateString(),
                accuracy: e.accuracy,
                frequency: e.frequency
              }))}
              lines={[
                { dataKey: 'accuracy', color: '#3B82F6', name: 'Accuracy' },
                { dataKey: 'frequency', color: '#10B981', name: 'Frequency' }
              ]}
              xDataKey="time"
              height={200}
            />
          </div>
        )}

        {pattern.related_patterns && pattern.related_patterns.length > 0 && (
          <div>
            <p className="text-sm text-gray-600 mb-2">Related Patterns</p>
            <div className="flex flex-wrap gap-2">
              {pattern.related_patterns.map(id => (
                <Badge key={id} variant="default" size="sm">{id}</Badge>
              ))}
            </div>
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
 * Feedback Modal
 */
const FeedbackModal: React.FC<{
  feedback: IFeedback[];
  onClose: () => void;
}> = ({ feedback, onClose }) => {
  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      render: (value: string) => new Date(value).toLocaleString(),
      sortable: true
    },
    {
      key: 'type',
      header: 'Type',
      render: (value: string) => {
        const colors = {
          positive: 'success',
          negative: 'danger',
          neutral: 'default'
        };
        return <Badge variant={colors[value as keyof typeof colors] as any} size="sm">{value}</Badge>;
      },
      sortable: true
    },
    {
      key: 'rating',
      header: 'Rating',
      render: (value: number) => value ? `${value}/5` : 'N/A',
      sortable: true
    },
    {
      key: 'message',
      header: 'Message',
      render: (value: string) => (
        <span className="text-sm text-gray-700 line-clamp-2">{value}</span>
      )
    },
    {
      key: 'categories',
      header: 'Categories',
      render: (value: string[]) => value ? (
        <div className="flex flex-wrap gap-1">
          {value.map(cat => (
            <Badge key={cat} variant="info" size="sm">{cat}</Badge>
          ))}
        </div>
      ) : 'N/A'
    }
  ];

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="User Feedback"
      size="xl"
    >
      <DataTable
        data={feedback}
        columns={columns}
        pageSize={10}
        searchable
        searchPlaceholder="Search feedback..."
      />

      <div className="flex justify-end mt-6">
        <Button onClick={onClose}>Close</Button>
      </div>
    </Modal>
  );
};

// Icon Components
const LearningIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const ConfidenceIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const PatternIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
  </svg>
);

const FeedbackIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
  </svg>
);

export default LearningHub;