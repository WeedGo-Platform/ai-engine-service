import React from 'react';
import { useTheme } from '../templates/ThemeProvider';
import { PotPalaceProductCard } from '../templates/pot-palace/components';
import { MinimalProductCard } from '../templates/modern/components';
import { BasicProductCard } from '../templates/headless/components';

export interface Product {
  id: string;
  name: string;
  brand?: string;
  price: number;
  image?: string;
  thc?: number;
  cbd?: number;
  category?: string;
  inStock?: boolean;
}

export interface ProductCardProps {
  product: Product;
  onPress: () => void;
  onAddToCart: () => void;
}

export const ProductCard: React.FC<ProductCardProps> = (props) => {
  const { template } = useTheme();

  switch (template) {
    case 'pot-palace':
      return <PotPalaceProductCard {...props} />;
    case 'modern':
      return <MinimalProductCard {...props} />;
    case 'headless':
    default:
      return <BasicProductCard {...props} />;
  }
};