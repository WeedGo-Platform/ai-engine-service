import React from 'react';
import { ISkeletonProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceSkeleton: React.FC<ISkeletonProps> = ({
  width,
  height,
  variant = 'rectangular',
  className,
  animation = 'pulse'
}) => {
  const animations = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer',
    none: ''
  };

  const variants = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-xl'
  };

  return (
    <div
      className={clsx(
        'bg-gradient-to-r from-green-100 via-yellow-100 to-green-100',
        'bg-[length:200%_100%]',
        animations[animation],
        variants[variant],
        className
      )}
      style={{
        width: width || '100%',
        height: height || '20px'
      }}
    />
  );
};