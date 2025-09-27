import React from 'react';
import { IFilterPanelProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceFilterPanel: React.FC<IFilterPanelProps> = ({
  filters,
  onFilterChange,
  className
}) => {
  const toggleFilter = (filterId: string) => {
    const updated = filters.map(f =>
      f.id === filterId ? { ...f, active: !f.active } : f
    );
    onFilterChange(updated);
  };

  const filtersByType = filters.reduce((acc, filter) => {
    if (!acc[filter.type]) acc[filter.type] = [];
    acc[filter.type].push(filter);
    return acc;
  }, {} as Record<string, typeof filters>);

  return (
    <div className={clsx(
      'bg-white rounded-2xl border-3 border-green-300 p-6',
      'shadow-lg',
      className
    )}>
      <h3 className="font-bold text-xl text-gray-800 mb-4">
        Filter Products 🔍
      </h3>

      <div className="space-y-6">
        {Object.entries(filtersByType).map(([type, typeFilters]) => (
          <div key={type}>
            <h4 className="font-semibold text-green-600 mb-2 capitalize">
              {type}
            </h4>
            <div className="space-y-2">
              {typeFilters.map(filter => (
                <label
                  key={filter.id}
                  className="flex items-center gap-3 cursor-pointer hover:bg-green-50 p-2 rounded-lg"
                >
                  <input
                    type="checkbox"
                    checked={filter.active}
                    onChange={() => toggleFilter(filter.id)}
                    className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
                  />
                  <span className={clsx(
                    'text-gray-700',
                    filter.active && 'font-bold text-green-600'
                  )}>
                    {filter.label}
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
