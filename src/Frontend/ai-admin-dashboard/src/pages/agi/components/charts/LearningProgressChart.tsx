import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LearningData {
  metric: string;
  value: number;
  target: number;
}

interface LearningProgressChartProps {
  data: LearningData[];
}

const LearningProgressChart: React.FC<LearningProgressChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="metric"
          stroke="#6b7280"
          fontSize={12}
        />
        <YAxis
          stroke="#6b7280"
          fontSize={12}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px'
          }}
        />
        <Legend />
        <Bar
          dataKey="value"
          fill="#8b5cf6"
          name="Current"
          radius={[8, 8, 0, 0]}
        />
        <Bar
          dataKey="target"
          fill="#e9d5ff"
          name="Target"
          radius={[8, 8, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default LearningProgressChart;