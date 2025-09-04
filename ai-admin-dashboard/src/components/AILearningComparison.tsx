import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitCompare, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  CheckCircle,
  XCircle,
  AlertCircle,
  Brain,
  Sparkles,
  BarChart3,
  Clock,
  Target,
  Zap
} from 'lucide-react';
import { format } from 'date-fns';

interface ComparisonResult {
  messageId: string;
  userMessage: string;
  originalResponse: {
    content: string;
    confidence: number;
    timestamp: string;
    modelVersion: string;
    processingTime: number;
    personality?: string;
  };
  replayedResponse: {
    content: string;
    confidence: number;
    timestamp: string;
    modelVersion: string;
    processingTime: number;
    personality?: string;
  };
  metrics: {
    confidenceChange: number;
    speedImprovement: number;
    relevanceScore: number;
    accuracyScore: number;
    sentimentAlignment: number;
  };
}

interface AILearningComparisonProps {
  comparisonResults: ComparisonResult[];
  sessionInfo?: {
    originalDate: string;
    replayDate: string;
    customerId: string;
    sessionId: string;
  };
}

export default function AILearningComparison({ 
  comparisonResults, 
  sessionInfo 
}: AILearningComparisonProps) {
  const [selectedMetric, setSelectedMetric] = useState<'confidence' | 'speed' | 'relevance' | 'all'>('all');
  const [viewMode, setViewMode] = useState<'side-by-side' | 'diff' | 'timeline'>('side-by-side');
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  // Calculate overall improvement metrics
  const overallMetrics = useMemo(() => {
    if (comparisonResults.length === 0) return null;

    const totalConfidenceChange = comparisonResults.reduce(
      (sum, r) => sum + r.metrics.confidenceChange, 0
    ) / comparisonResults.length;

    const totalSpeedImprovement = comparisonResults.reduce(
      (sum, r) => sum + r.metrics.speedImprovement, 0
    ) / comparisonResults.length;

    const totalRelevance = comparisonResults.reduce(
      (sum, r) => sum + r.metrics.relevanceScore, 0
    ) / comparisonResults.length;

    const totalAccuracy = comparisonResults.reduce(
      (sum, r) => sum + r.metrics.accuracyScore, 0
    ) / comparisonResults.length;

    return {
      confidenceChange: totalConfidenceChange,
      speedImprovement: totalSpeedImprovement,
      relevanceScore: totalRelevance,
      accuracyScore: totalAccuracy,
      totalComparisons: comparisonResults.length,
      improvedResponses: comparisonResults.filter(r => r.metrics.confidenceChange > 0).length,
      degradedResponses: comparisonResults.filter(r => r.metrics.confidenceChange < -5).length
    };
  }, [comparisonResults]);

  const toggleExpanded = (messageId: string) => {
    setExpandedResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  // Function to highlight differences between two texts
  const highlightDifferences = (original: string, updated: string) => {
    const originalWords = original.split(' ');
    const updatedWords = updated.split(' ');
    
    return updatedWords.map((word, idx) => {
      if (!originalWords[idx]) {
        return <span key={idx} className="bg-green-200 px-1 rounded">{word} </span>;
      } else if (word !== originalWords[idx]) {
        return <span key={idx} className="bg-yellow-200 px-1 rounded">{word} </span>;
      }
      return <span key={idx}>{word} </span>;
    });
  };

  const getMetricIcon = (change: number) => {
    if (change > 10) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < -10) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* Header with Overall Metrics */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900">AI Learning Comparison</h2>
          </div>
          
          {/* View Mode Selector */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-3 py-1 rounded-lg text-sm ${
                viewMode === 'side-by-side' 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Side by Side
            </button>
            <button
              onClick={() => setViewMode('diff')}
              className={`px-3 py-1 rounded-lg text-sm ${
                viewMode === 'diff' 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Differences
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded-lg text-sm ${
                viewMode === 'timeline' 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Timeline
            </button>
          </div>
        </div>

        {/* Session Info */}
        {sessionInfo && (
          <div className="text-xs text-gray-500 mb-4">
            Original: {format(new Date(sessionInfo.originalDate), 'MMM d, yyyy h:mm a')} | 
            Replay: {format(new Date(sessionInfo.replayDate), 'MMM d, yyyy h:mm a')}
          </div>
        )}

        {/* Overall Metrics Dashboard */}
        {overallMetrics && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-5 h-5 text-blue-600" />
                <span className={`text-2xl font-bold ${getConfidenceColor(overallMetrics.confidenceChange + 70)}`}>
                  {overallMetrics.confidenceChange > 0 ? '+' : ''}{overallMetrics.confidenceChange.toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-gray-600">Confidence Change</p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <Zap className="w-5 h-5 text-green-600" />
                <span className="text-2xl font-bold text-green-600">
                  {overallMetrics.speedImprovement > 0 ? '+' : ''}{overallMetrics.speedImprovement.toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-600">Speed Improvement</p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <span className="text-2xl font-bold text-purple-600">
                  {overallMetrics.relevanceScore.toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-600">Relevance Score</p>
            </div>

            <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <BarChart3 className="w-5 h-5 text-amber-600" />
                <div className="flex items-center gap-2">
                  <span className="text-sm text-green-600">↑{overallMetrics.improvedResponses}</span>
                  <span className="text-sm text-red-600">↓{overallMetrics.degradedResponses}</span>
                </div>
              </div>
              <p className="text-xs text-gray-600">Response Changes</p>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      <div className="space-y-4">
        {comparisonResults.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No comparison results yet. Run a replay to compare AI responses.</p>
          </div>
        ) : (
          <AnimatePresence>
            {comparisonResults.map((result, idx) => (
              <motion.div
                key={result.messageId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: idx * 0.1 }}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                {/* Message Header */}
                <div 
                  className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => toggleExpanded(result.messageId)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="text-sm font-medium text-gray-700">
                        Message {idx + 1}
                      </div>
                      <div className="text-xs text-gray-500 italic">
                        "{result.userMessage.substring(0, 50)}..."
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      {/* Quick Metrics */}
                      <div className="flex items-center gap-2">
                        {getMetricIcon(result.metrics.confidenceChange)}
                        <span className="text-sm">
                          {result.metrics.confidenceChange > 0 ? '+' : ''}
                          {result.metrics.confidenceChange.toFixed(1)}%
                        </span>
                      </div>
                      
                      {/* Status Badge */}
                      {result.metrics.confidenceChange > 5 ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : result.metrics.confidenceChange < -5 ? (
                        <XCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-yellow-500" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedResults.has(result.messageId) && (
                  <div className="p-4 border-t border-gray-200">
                    {viewMode === 'side-by-side' && (
                      <div className="grid grid-cols-2 gap-4">
                        {/* Original Response */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">Original Response</span>
                            <span className="text-xs text-gray-500">
                              v{result.originalResponse.modelVersion}
                            </span>
                          </div>
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-700">
                              {result.originalResponse.content}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-500">
                            <span className={getConfidenceColor(result.originalResponse.confidence)}>
                              {result.originalResponse.confidence}% confidence
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {result.originalResponse.processingTime}ms
                            </span>
                          </div>
                        </div>

                        {/* Replayed Response */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">Replayed Response</span>
                            <span className="text-xs text-gray-500">
                              v{result.replayedResponse.modelVersion}
                            </span>
                          </div>
                          <div className="p-3 bg-blue-50 rounded-lg">
                            <p className="text-sm text-gray-700">
                              {result.replayedResponse.content}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-500">
                            <span className={getConfidenceColor(result.replayedResponse.confidence)}>
                              {result.replayedResponse.confidence}% confidence
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {result.replayedResponse.processingTime}ms
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {viewMode === 'diff' && (
                      <div className="space-y-4">
                        <div className="p-3 bg-gray-50 rounded-lg">
                          <p className="text-sm font-medium text-gray-700 mb-2">Response Changes:</p>
                          <div className="text-sm">
                            {highlightDifferences(
                              result.originalResponse.content,
                              result.replayedResponse.content
                            )}
                          </div>
                        </div>
                        
                        {/* Metrics Comparison */}
                        <div className="grid grid-cols-5 gap-2">
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500">Confidence</p>
                            <p className={`text-sm font-medium ${
                              result.metrics.confidenceChange > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {result.metrics.confidenceChange > 0 ? '+' : ''}
                              {result.metrics.confidenceChange.toFixed(1)}%
                            </p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500">Speed</p>
                            <p className={`text-sm font-medium ${
                              result.metrics.speedImprovement > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {result.metrics.speedImprovement > 0 ? '+' : ''}
                              {result.metrics.speedImprovement.toFixed(0)}%
                            </p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500">Relevance</p>
                            <p className="text-sm font-medium text-blue-600">
                              {result.metrics.relevanceScore.toFixed(0)}%
                            </p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500">Accuracy</p>
                            <p className="text-sm font-medium text-purple-600">
                              {result.metrics.accuracyScore.toFixed(0)}%
                            </p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500">Sentiment</p>
                            <p className="text-sm font-medium text-amber-600">
                              {result.metrics.sentimentAlignment.toFixed(0)}%
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {viewMode === 'timeline' && (
                      <div className="space-y-4">
                        <div className="relative">
                          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300"></div>
                          
                          {/* Original */}
                          <div className="relative flex items-start mb-4">
                            <div className="bg-gray-500 rounded-full w-8 h-8 flex items-center justify-center text-white text-xs">
                              1
                            </div>
                            <div className="ml-4 flex-1">
                              <p className="text-xs text-gray-500 mb-1">
                                {format(new Date(result.originalResponse.timestamp), 'MMM d, h:mm a')}
                              </p>
                              <div className="p-3 bg-gray-50 rounded-lg">
                                <p className="text-sm text-gray-700">
                                  {result.originalResponse.content}
                                </p>
                                <p className="text-xs text-gray-500 mt-2">
                                  Confidence: {result.originalResponse.confidence}%
                                </p>
                              </div>
                            </div>
                          </div>
                          
                          {/* Replayed */}
                          <div className="relative flex items-start">
                            <div className="bg-blue-500 rounded-full w-8 h-8 flex items-center justify-center text-white text-xs">
                              2
                            </div>
                            <div className="ml-4 flex-1">
                              <p className="text-xs text-gray-500 mb-1">
                                {format(new Date(result.replayedResponse.timestamp), 'MMM d, h:mm a')}
                              </p>
                              <div className="p-3 bg-blue-50 rounded-lg">
                                <p className="text-sm text-gray-700">
                                  {result.replayedResponse.content}
                                </p>
                                <p className="text-xs text-gray-500 mt-2">
                                  Confidence: {result.replayedResponse.confidence}%
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Learning Insights */}
      {comparisonResults.length > 0 && overallMetrics && (
        <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Learning Insights</h3>
          <ul className="space-y-1 text-xs text-gray-600">
            {overallMetrics.confidenceChange > 5 && (
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3 text-green-500" />
                Model confidence has improved by {overallMetrics.confidenceChange.toFixed(1)}%
              </li>
            )}
            {overallMetrics.speedImprovement > 0 && (
              <li className="flex items-center gap-2">
                <Zap className="w-3 h-3 text-blue-500" />
                Response time improved by {overallMetrics.speedImprovement.toFixed(0)}%
              </li>
            )}
            {overallMetrics.improvedResponses > overallMetrics.degradedResponses && (
              <li className="flex items-center gap-2">
                <TrendingUp className="w-3 h-3 text-purple-500" />
                {overallMetrics.improvedResponses} out of {overallMetrics.totalComparisons} responses showed improvement
              </li>
            )}
            {overallMetrics.relevanceScore > 75 && (
              <li className="flex items-center gap-2">
                <Target className="w-3 h-3 text-amber-500" />
                High relevance score indicates good contextual understanding
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}