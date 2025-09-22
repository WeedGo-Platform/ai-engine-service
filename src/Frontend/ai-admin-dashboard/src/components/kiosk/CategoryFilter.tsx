import React from 'react';
import { LucideIcon } from 'lucide-react';

interface CategoryFilterProps {
  categories: Array<{
    id: string;
    name: string;
    icon: LucideIcon;
  }>;
  selectedCategory: string | null;
  onCategorySelect: (categoryId: string | null) => void;
}

export default function CategoryFilter({
  categories,
  selectedCategory,
  onCategorySelect
}: CategoryFilterProps) {
  return (
    <div className="space-y-2">
      <button
        onClick={() => onCategorySelect(null)}
        className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
          !selectedCategory
            ? 'bg-primary-100 text-primary-600'
            : 'hover:bg-gray-100'
        }`}
      >
        All Products
      </button>

      {categories.map(category => {
        const Icon = category.icon;
        return (
          <button
            key={category.id}
            onClick={() => onCategorySelect(category.id)}
            className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center ${
              selectedCategory === category.id
                ? 'bg-primary-100 text-primary-600'
                : 'hover:bg-gray-100'
            }`}
          >
            {Icon && <Icon className="w-5 h-5 mr-3" />}
            {category.name}
          </button>
        );
      })}
    </div>
  );
}