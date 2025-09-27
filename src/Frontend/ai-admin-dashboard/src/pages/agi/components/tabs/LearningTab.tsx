import React, { useEffect, useState } from 'react';
import { Brain, TrendingUp, Target, Award } from 'lucide-react';
import { LearningMetrics, Pattern } from '../../types';
import { agiApi } from '../../services/api';
import LearningProgressChart from '../charts/LearningProgressChart';

interface LearningTabProps {
  metrics: LearningMetrics | null;
}

const LearningTab: React.FC<LearningTabProps> = ({ metrics }) => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [feedback, setFeedback] = useState<any[]>([]);
  const [progressData, setProgressData] = useState<any[]>([]);

  useEffect(() => {
    loadLearningData();
    const interval = setInterval(loadLearningData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadLearningData = async () => {
    try {
      const [patternsData, feedbackData] = await Promise.all([
        agiApi.getPatterns(20),
        agiApi.getFeedback(20)
      ]);
      setPatterns(patternsData);
      setFeedback(feedbackData);

      const progress = [
        { metric: 'Pattern Recognition', value: metrics?.patternCount || 0, target: 100 },
        { metric: 'Accuracy', value: (metrics?.confidenceScore || 0) * 100, target: 95 },
        { metric: 'Learning Speed', value: (metrics?.learningRate || 0) * 100, target: 85 },
        { metric: 'Adaptation Rate', value: metrics?.adaptationsToday || 0, target: 80 },
        { metric: 'Feedback Score', value: metrics?.feedbackPositive || 0, target: 95 }
      ];
      setProgressData(progress);
    } catch (error) {
      console.error('Failed to load learning data:', error);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Brain className="h-8 w-8 text-purple-500" />
            <span className="text-2xl font-bold text-gray-900">{metrics?.patternCount || 0}</span>
          </div>
          <p className="text-sm text-gray-600">Patterns Recognized</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="h-8 w-8 text-green-500" />
            <span className="text-2xl font-bold text-gray-900">{metrics?.feedbackPositive || 0}%</span>
          </div>
          <p className="text-sm text-gray-600">Positive Feedback</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Target className="h-8 w-8 text-blue-500" />
            <span className="text-2xl font-bold text-gray-900">{metrics?.adaptationsToday || 0}</span>
          </div>
          <p className="text-sm text-gray-600">Adaptations Today</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Award className="h-8 w-8 text-yellow-500" />
            <span className="text-2xl font-bold text-gray-900">
              {metrics?.confidenceScore ? (metrics.confidenceScore * 100).toFixed(0) : 0}%
            </span>
          </div>
          <p className="text-sm text-gray-600">Confidence Score</p>
        </div>
      </div>

      {/* Patterns */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recognized Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((pattern) => (
            <div key={pattern.id} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-gray-900">{pattern.type}</h4>
                <span className="text-sm text-gray-500">{pattern.frequency} occurrences</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence</span>
                <div className="flex items-center">
                  <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${pattern.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{(pattern.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Learning Progress Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Progress</h3>
        <LearningProgressChart data={progressData} />
      </div>

      {/* Learning Metrics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Metrics</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Learning Rate</span>
              <span className="text-sm font-medium">
                {metrics?.learningRate ? (metrics.learningRate * 100).toFixed(1) : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full"
                style={{ width: `${(metrics?.learningRate || 0) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningTab;