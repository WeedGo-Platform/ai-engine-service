import React from 'react';
import { TrendingUp } from 'lucide-react';

interface LearningData {
  patternCount: number;
  feedbackPositive: number;
  adaptationsToday: number;
}

interface LearningMetricsProps {
  learning?: LearningData;
}

const LearningMetrics: React.FC<LearningMetricsProps> = ({ learning }) => {
  const defaultLearning: LearningData = {
    patternCount: 847,
    feedbackPositive: 92,
    adaptationsToday: 34
  };

  const data = learning || defaultLearning;

  const metrics = [
    {
      label: 'Pattern Recognition',
      value: `${data.patternCount} patterns`,
      percentage: 75,
      gradient: 'from-blue-500 to-purple-500'
    },
    {
      label: 'Feedback Processing',
      value: `${data.feedbackPositive}% positive`,
      percentage: data.feedbackPositive,
      gradient: 'from-green-500 to-blue-500'
    },
    {
      label: 'Adaptations Applied',
      value: `${data.adaptationsToday} today`,
      percentage: 60,
      gradient: 'from-purple-500 to-pink-500'
    }
  ];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="font-semibold flex items-center">
          <TrendingUp className="w-4 h-4 mr-2" />
          Learning & Adaptation
        </h3>
      </div>
      <div className="p-4 space-y-3">
        {metrics.map((metric, index) => (
          <div key={index} className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{metric.label}</span>
              <span>{metric.value}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${metric.gradient}`}
                style={{ width: `${metric.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LearningMetrics;