import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PerformanceData {
  time: string;
  successRate: number;
  responseTime: number;
  throughput: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
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
        <Line
          type="monotone"
          dataKey="successRate"
          stroke="#10b981"
          strokeWidth={2}
          name="Success Rate (%)"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="responseTime"
          stroke="#3b82f6"
          strokeWidth={2}
          name="Response Time (ms)"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="throughput"
          stroke="#f59e0b"
          strokeWidth={2}
          name="Throughput (req/s)"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PerformanceChart;