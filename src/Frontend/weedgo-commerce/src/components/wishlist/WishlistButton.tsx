/**
 * Wishlist button component for toggling product wishlist status
 */

import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { HeartIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import {
  toggleWishlistItem,
  selectIsInWishlist,
  selectWishlistLoading,
} from '@features/wishlist/wishlistSlice';
import { selectIsAuthenticated } from '@features/auth/authSlice';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

interface WishlistButtonProps {
  productId: string;
  productName?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const WishlistButton: React.FC<WishlistButtonProps> = ({
  productId,
  productName = 'this product',
  size = 'md',
  showText = false,
  className = '',
}) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isInWishlist = useSelector(selectIsInWishlist(productId));
  const { isAdding, isRemoving } = useSelector(selectWishlistLoading);

  const isLoading = isAdding || isRemoving;

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      toast('Please login to save items to your wishlist', {
        icon: '🔒',
      });
      navigate('/login?redirect=' + encodeURIComponent(window.location.pathname));
      return;
    }

    dispatch(toggleWishlistItem(productId) as any);
  };

  const sizeClasses = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  };

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const buttonContent = (
    <>
      {isInWishlist ? (
        <HeartSolidIcon
          className={`${iconSizes[size]} text-red-500`}
          aria-hidden="true"
        />
      ) : (
        <HeartIcon
          className={`${iconSizes[size]} text-gray-600 hover:text-red-500 transition-colors`}
          aria-hidden="true"
        />
      )}
      {showText && (
        <span className="ml-2">
          {isInWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}
        </span>
      )}
    </>
  );

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`
        inline-flex items-center justify-center rounded-full
        ${sizeClasses[size]}
        ${isInWishlist ? 'bg-red-50' : 'bg-white'}
        border border-gray-300 hover:border-red-300
        transition-all duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
      aria-label={
        isInWishlist
          ? `Remove ${productName} from wishlist`
          : `Add ${productName} to wishlist`
      }
      aria-pressed={isInWishlist}
      title={isInWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
    >
      {isLoading ? (
        <svg
          className={`animate-spin ${iconSizes[size]} text-gray-500`}
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        buttonContent
      )}
    </button>
  );
};

export default WishlistButton;