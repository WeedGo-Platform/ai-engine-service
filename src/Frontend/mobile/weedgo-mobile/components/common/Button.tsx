import React from 'react';
import { ViewStyle } from 'react-native';
import { useTheme } from '../templates/ThemeProvider';
import { RoundedButton } from '../templates/pot-palace/components';
import { FlatButton } from '../templates/modern/components';
import { BasicButton } from '../templates/headless/components';

export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium' | 'large';
  icon?: React.ReactNode;
  style?: ViewStyle;
}

export const Button: React.FC<ButtonProps> = (props) => {
  const { template } = useTheme();

  switch (template) {
    case 'pot-palace':
      return <RoundedButton {...props} />;
    case 'modern':
      return <FlatButton {...props} variant={props.variant as any} />;
    case 'headless':
    default:
      return <BasicButton {...props} />;
  }
};