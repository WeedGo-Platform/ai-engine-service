/**
 * Reusable Chart Components
 * Provides various chart types for data visualization
 */

import React from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

interface IChartProps {
  data: any[];
  height?: number;
  className?: string;
}

interface ILineChartProps extends IChartProps {
  lines: {
    dataKey: string;
    color: string;
    name?: string;
    strokeWidth?: number;
  }[];
  xDataKey: string;
}

export const LineChartComponent: React.FC<ILineChartProps> = ({
  data,
  lines,
  xDataKey,
  height = 300,
  className = ''
}) => {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey={xDataKey} stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
          <Legend />
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              stroke={line.color}
              strokeWidth={line.strokeWidth || 2}
              name={line.name || line.dataKey}
              dot={false}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

interface IAreaChartProps extends IChartProps {
  areas: {
    dataKey: string;
    color: string;
    name?: string;
    fillOpacity?: number;
  }[];
  xDataKey: string;
}

export const AreaChartComponent: React.FC<IAreaChartProps> = ({
  data,
  areas,
  xDataKey,
  height = 300,
  className = ''
}) => {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey={xDataKey} stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
          <Legend />
          {areas.map((area) => (
            <Area
              key={area.dataKey}
              type="monotone"
              dataKey={area.dataKey}
              stroke={area.color}
              fill={area.color}
              fillOpacity={area.fillOpacity || 0.6}
              name={area.name || area.dataKey}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

interface IBarChartProps extends IChartProps {
  bars: {
    dataKey: string;
    color: string;
    name?: string;
  }[];
  xDataKey: string;
}

export const BarChartComponent: React.FC<IBarChartProps> = ({
  data,
  bars,
  xDataKey,
  height = 300,
  className = ''
}) => {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey={xDataKey} stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
          <Legend />
          {bars.map((bar) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              fill={bar.color}
              name={bar.name || bar.dataKey}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

interface IPieChartProps extends IChartProps {
  dataKey: string;
  nameKey: string;
  colors?: string[];
  innerRadius?: number;
}

export const PieChartComponent: React.FC<IPieChartProps> = ({
  data,
  dataKey,
  nameKey,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'],
  innerRadius = 0,
  height = 300,
  className = ''
}) => {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey={dataKey}
            nameKey={nameKey}
            cx="50%"
            cy="50%"
            outerRadius={80}
            innerRadius={innerRadius}
            label
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

interface IRadarChartProps extends IChartProps {
  dataKey: string;
  categories: string;
  color?: string;
}

export const RadarChartComponent: React.FC<IRadarChartProps> = ({
  data,
  dataKey,
  categories,
  color = '#3B82F6',
  height = 300,
  className = ''
}) => {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis dataKey={categories} stroke="#6b7280" fontSize={12} />
          <PolarRadiusAxis stroke="#6b7280" fontSize={12} />
          <Radar
            name={dataKey}
            dataKey={dataKey}
            stroke={color}
            fill={color}
            fillOpacity={0.6}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

interface ISparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

export const Sparkline: React.FC<ISparklineProps> = ({
  data,
  color = '#3B82F6',
  height = 40,
  width = 100
}) => {
  const chartData = data.map((value, index) => ({ index, value }));

  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

interface IProgressChartProps {
  value: number;
  max?: number;
  label?: string;
  color?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const ProgressChart: React.FC<IProgressChartProps> = ({
  value,
  max = 100,
  label,
  color = 'blue',
  showPercentage = true,
  size = 'md'
}) => {
  const percentage = Math.round((value / max) * 100);

  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
    purple: 'bg-purple-600'
  };

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6'
  };

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showPercentage && (
            <span className="text-sm text-gray-500">{percentage}%</span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`h-full ${colorClasses[color as keyof typeof colorClasses]} transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

interface IActivityChartProps {
  data: { date: string; value: number }[];
  color?: string;
  height?: number;
}

export const ActivityChart: React.FC<IActivityChartProps> = ({
  data,
  color = '#3B82F6',
  height = 100
}) => {
  const maxValue = Math.max(...data.map(d => d.value));

  return (
    <div className="flex items-end space-x-1" style={{ height }}>
      {data.map((item, index) => {
        const heightPercentage = (item.value / maxValue) * 100;
        const opacity = 0.3 + (item.value / maxValue) * 0.7;

        return (
          <div
            key={index}
            className="flex-1 bg-blue-600 rounded-t"
            style={{
              height: `${heightPercentage}%`,
              backgroundColor: color,
              opacity
            }}
            title={`${item.date}: ${item.value}`}
          />
        );
      })}
    </div>
  );
};