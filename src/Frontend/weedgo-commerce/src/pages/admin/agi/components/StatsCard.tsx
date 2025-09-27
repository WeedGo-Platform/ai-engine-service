import React from 'react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: string;
  trendUp?: boolean;
  bgColor?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  trend,
  trendUp,
  bgColor = 'bg-gray-700'
}) => {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 ${bgColor} rounded-lg`}>
          {icon}
        </div>
        {trend && (
          <span className={`text-sm ${
            trendUp ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend}
          </span>
        )}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-gray-400 text-sm">{title}</div>
    </div>
  );
};

export default StatsCard;