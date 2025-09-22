import React from 'react';
import { useTheme } from '../templates/ThemeProvider';
import { PlayfulLoading } from '../templates/pot-palace/components';
import { SimpleLoading } from '../templates/modern/components';
import { BasicLoading } from '../templates/headless/components';

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  color?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = (props) => {
  const { template } = useTheme();

  switch (template) {
    case 'pot-palace':
      return <PlayfulLoading {...props} />;
    case 'modern':
      return <SimpleLoading {...props} />;
    case 'headless':
    default:
      return <BasicLoading message={props.message} />;
  }
};