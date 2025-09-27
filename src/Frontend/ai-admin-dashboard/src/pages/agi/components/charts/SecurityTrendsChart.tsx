import React from 'react';
import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SecurityTrendData {
  time: string;
  threats: number;
  blocked: number;
  severity: number;
}

interface SecurityTrendsChartProps {
  data: SecurityTrendData[];
}

const SecurityTrendsChart: React.FC<SecurityTrendsChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <ComposedChart data={data}>
        <defs>
          <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
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
        <Area
          type="monotone"
          dataKey="threats"
          fill="url(#colorThreats)"
          stroke="#ef4444"
          strokeWidth={2}
          name="Total Threats"
        />
        <Line
          type="monotone"
          dataKey="blocked"
          stroke="#10b981"
          strokeWidth={2}
          name="Blocked"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="severity"
          stroke="#f59e0b"
          strokeWidth={2}
          name="Avg Severity"
          dot={false}
          strokeDasharray="5 5"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default SecurityTrendsChart;