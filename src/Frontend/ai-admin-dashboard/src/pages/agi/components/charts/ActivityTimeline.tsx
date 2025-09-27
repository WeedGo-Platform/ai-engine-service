import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ActivityData {
  time: string;
  activeAgents: number;
  tasksProcessed: number;
}

interface ActivityTimelineProps {
  data: ActivityData[];
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorActiveAgents" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
          </linearGradient>
          <linearGradient id="colorTasks" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          stroke="#6b7280"
          fontSize={11}
        />
        <YAxis
          stroke="#6b7280"
          fontSize={11}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px'
          }}
        />
        <Area
          type="monotone"
          dataKey="activeAgents"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#colorActiveAgents)"
          name="Active Agents"
        />
        <Area
          type="monotone"
          dataKey="tasksProcessed"
          stroke="#10b981"
          strokeWidth={2}
          fill="url(#colorTasks)"
          name="Tasks Processed"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default ActivityTimeline;