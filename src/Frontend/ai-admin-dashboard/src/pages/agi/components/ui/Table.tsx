/**
 * Reusable Table Components
 * Flexible table system with sorting, filtering, and pagination
 */

import React, { ReactNode, useState, useMemo } from 'react';

interface IColumn<T> {
  key: keyof T | string;
  header: string;
  render?: (value: any, item: T) => ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface ITableProps<T> {
  data: T[];
  columns: IColumn<T>[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  className?: string;
  striped?: boolean;
  hoverable?: boolean;
  compact?: boolean;
}

export function Table<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No data available',
  onRowClick,
  className = '',
  striped = true,
  hoverable = true,
  compact = false
}: ITableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortColumn) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];

      if (aValue === bValue) return 0;

      const comparison = aValue < bValue ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, sortColumn, sortDirection]);

  if (loading) {
    return <TableSkeleton columns={columns.length} rows={5} />;
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  const rowClasses = `
    ${hoverable ? 'hover:bg-gray-50' : ''}
    ${onRowClick ? 'cursor-pointer' : ''}
    ${compact ? '' : 'border-b border-gray-200'}
  `;

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={`
                  px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                  ${column.sortable ? 'cursor-pointer select-none' : ''}
                  ${compact ? 'py-2' : ''}
                `}
                style={{ width: column.width }}
                onClick={() => column.sortable && handleSort(String(column.key))}
              >
                <div className="flex items-center space-x-1">
                  <span>{column.header}</span>
                  {column.sortable && (
                    <SortIcon
                      active={sortColumn === String(column.key)}
                      direction={sortDirection}
                    />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((item, index) => (
            <tr
              key={index}
              className={`
                ${rowClasses}
                ${striped && index % 2 === 1 ? 'bg-gray-50' : ''}
              `}
              onClick={() => onRowClick?.(item)}
            >
              {columns.map((column) => {
                const value = column.key.includes('.')
                  ? column.key.split('.').reduce((obj, key) => obj?.[key], item as any)
                  : item[column.key];

                return (
                  <td
                    key={String(column.key)}
                    className={`
                      px-6 py-4 whitespace-nowrap text-sm text-gray-900
                      ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                      ${compact ? 'py-2' : ''}
                    `}
                  >
                    {column.render ? column.render(value, item) : value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ISortIconProps {
  active: boolean;
  direction: 'asc' | 'desc';
}

const SortIcon: React.FC<ISortIconProps> = ({ active, direction }) => {
  return (
    <svg
      className={`w-4 h-4 ${active ? 'text-gray-900' : 'text-gray-400'}`}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      {direction === 'asc' ? (
        <path d="M5 15l7-7 7 7" />
      ) : (
        <path d="M19 9l-7 7-7-7" />
      )}
    </svg>
  );
};

interface ITableSkeletonProps {
  columns: number;
  rows: number;
}

const TableSkeleton: React.FC<ITableSkeletonProps> = ({ columns, rows }) => {
  return (
    <div className="animate-pulse">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {Array.from({ length: columns }).map((_, i) => (
                <th key={i} className="px-6 py-3">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <tr key={rowIndex}>
                {Array.from({ length: columns }).map((_, colIndex) => (
                  <td key={colIndex} className="px-6 py-4">
                    <div className="h-4 bg-gray-200 rounded w-24"></div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

interface IPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<IPaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className = ''
}) => {
  const pages = useMemo(() => {
    const delta = 2;
    const range: number[] = [];
    const rangeWithDots: (number | string)[] = [];
    let l: number | undefined;

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= currentPage - delta && i <= currentPage + delta)) {
        range.push(i);
      }
    }

    range.forEach((i) => {
      if (l) {
        if (i - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (i - l !== 1) {
          rangeWithDots.push('...');
        }
      }
      rangeWithDots.push(i);
      l = i;
    });

    return rangeWithDots;
  }, [currentPage, totalPages]);

  return (
    <div className={`flex items-center justify-between ${className}`}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>

      <div className="flex space-x-1">
        {pages.map((page, index) => (
          <button
            key={index}
            onClick={() => typeof page === 'number' && onPageChange(page)}
            disabled={page === '...'}
            className={`
              px-3 py-2 text-sm font-medium rounded-md
              ${
                page === currentPage
                  ? 'bg-blue-600 text-white'
                  : page === '...'
                  ? 'text-gray-400 cursor-default'
                  : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
              }
            `}
          >
            {page}
          </button>
        ))}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  );
};

interface IDataTableProps<T> extends ITableProps<T> {
  pageSize?: number;
  searchable?: boolean;
  searchPlaceholder?: string;
}

export function DataTable<T extends Record<string, any>>({
  data,
  pageSize = 10,
  searchable = true,
  searchPlaceholder = 'Search...',
  ...tableProps
}: IDataTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredData = useMemo(() => {
    if (!searchTerm) return data;

    return data.filter((item) =>
      Object.values(item).some((value) =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredData.slice(startIndex, startIndex + pageSize);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredData.length / pageSize);

  return (
    <div>
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            placeholder={searchPlaceholder}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      <Table {...tableProps} data={paginatedData} />

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          className="mt-4"
        />
      )}

      <div className="mt-2 text-sm text-gray-500">
        Showing {((currentPage - 1) * pageSize) + 1} to{' '}
        {Math.min(currentPage * pageSize, filteredData.length)} of{' '}
        {filteredData.length} results
      </div>
    </div>
  );
}