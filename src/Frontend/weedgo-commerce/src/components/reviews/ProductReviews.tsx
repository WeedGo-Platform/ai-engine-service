/**
 * Product reviews and ratings component
 */

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';
import {
  fetchProductReviews,
  fetchProductStats,
  selectProductReviews,
  selectProductStats,
  selectIsLoadingReviews,
  setFilter,
  selectReviewsFilter,
  selectReviewsPagination,
} from '@features/reviews/reviewsSlice';
import ReviewForm from './ReviewForm';
import ReviewItem from './ReviewItem';
import { AccessibleButton, AccessibleSelect } from '@components/common/AccessibleComponents';
import { useAnnouncement } from '@hooks/useAccessibility';

interface ProductReviewsProps {
  productId: string;
  productName: string;
}

const ProductReviews: React.FC<ProductReviewsProps> = ({ productId, productName }) => {
  const dispatch = useDispatch();
  const reviews = useSelector((state: any) => selectProductReviews(state, productId));
  const stats = useSelector((state: any) => selectProductStats(state, productId));
  const isLoading = useSelector(selectIsLoadingReviews);
  const filter = useSelector(selectReviewsFilter);
  const pagination = useSelector(selectReviewsPagination);
  const announce = useAnnouncement();

  const [showReviewForm, setShowReviewForm] = useState(false);
  const [selectedRatingFilter, setSelectedRatingFilter] = useState<number | null>(null);

  useEffect(() => {
    // Fetch reviews and stats on component mount
    dispatch(fetchProductReviews({ productId }) as any);
    dispatch(fetchProductStats(productId) as any);
  }, [dispatch, productId]);

  useEffect(() => {
    // Refetch when filter changes
    if (filter) {
      dispatch(fetchProductReviews({
        productId,
        rating: filter.rating || undefined,
        verified: filter.verified || undefined,
        sortBy: filter.sortBy,
      }) as any);
    }
  }, [dispatch, productId, filter]);

  const handleFilterChange = (key: string, value: any) => {
    dispatch(setFilter({ [key]: value }));
    announce(`Filter changed: ${key} set to ${value}`);
  };

  const handleLoadMore = () => {
    if (pagination.hasMore) {
      dispatch(fetchProductReviews({
        productId,
        page: pagination.page + 1,
        limit: pagination.limit,
        rating: filter.rating || undefined,
        verified: filter.verified || undefined,
        sortBy: filter.sortBy,
      }) as any);
    }
  };

  const renderStars = (rating: number, size: string = 'h-5 w-5') => {
    return (
      <div className="flex items-center" role="img" aria-label={`${rating} out of 5 stars`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span key={star}>
            {star <= rating ? (
              <StarIcon className={`${size} text-yellow-400`} aria-hidden="true" />
            ) : (
              <StarOutlineIcon className={`${size} text-gray-300`} aria-hidden="true" />
            )}
          </span>
        ))}
      </div>
    );
  };

  const renderRatingDistribution = () => {
    if (!stats) return null;

    const maxCount = Math.max(...Object.values(stats.ratingDistribution));

    return (
      <div className="space-y-2" aria-label="Rating distribution">
        {[5, 4, 3, 2, 1].map((rating) => {
          const count = stats.ratingDistribution[rating as keyof typeof stats.ratingDistribution];
          const percentage = stats.totalReviews > 0 ? (count / stats.totalReviews) * 100 : 0;

          return (
            <button
              key={rating}
              onClick={() => handleFilterChange('rating', rating)}
              className={`flex items-center w-full hover:bg-gray-50 p-1 rounded transition-colors ${
                filter.rating === rating ? 'bg-gray-100' : ''
              }`}
              aria-label={`Filter by ${rating} star reviews`}
            >
              <span className="text-sm text-gray-600 w-12">{rating} star</span>
              <div className="flex-1 mx-3">
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-400 h-2 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                    role="progressbar"
                    aria-valuenow={percentage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  />
                </div>
              </div>
              <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className="mt-8" id="reviews-section">
      <h2 className="text-2xl font-bold text-gray-900">Customer Reviews</h2>

      {/* Reviews Summary */}
      {stats && (
        <div className="mt-6 lg:grid lg:grid-cols-3 lg:gap-8">
          {/* Overall Rating */}
          <div className="text-center lg:text-left">
            <div className="flex items-center justify-center lg:justify-start space-x-2">
              <span className="text-4xl font-bold text-gray-900">
                {stats.averageRating.toFixed(1)}
              </span>
              {renderStars(Math.round(stats.averageRating))}
            </div>
            <p className="mt-1 text-sm text-gray-600">
              Based on {stats.totalReviews} {stats.totalReviews === 1 ? 'review' : 'reviews'}
            </p>
            {stats.verifiedPurchasePercentage > 0 && (
              <p className="mt-1 text-xs text-green-600">
                {stats.verifiedPurchasePercentage}% verified purchases
              </p>
            )}

            <AccessibleButton
              onClick={() => setShowReviewForm(true)}
              variant="primary"
              className="mt-4"
              aria-label="Write a review"
            >
              Write a Review
            </AccessibleButton>
          </div>

          {/* Rating Distribution */}
          <div className="mt-6 lg:mt-0 lg:col-span-2">
            <h3 className="sr-only">Rating distribution</h3>
            {renderRatingDistribution()}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mt-8 flex flex-wrap gap-4 items-center border-t border-b py-4">
        <AccessibleSelect
          label="Sort by"
          options={[
            { value: 'newest', label: 'Most Recent' },
            { value: 'oldest', label: 'Oldest First' },
            { value: 'highest', label: 'Highest Rating' },
            { value: 'lowest', label: 'Lowest Rating' },
            { value: 'helpful', label: 'Most Helpful' },
          ]}
          value={filter.sortBy}
          onChange={(e) => handleFilterChange('sortBy', e.target.value)}
          className="w-48"
        />

        <div className="flex gap-2">
          <AccessibleButton
            onClick={() => handleFilterChange('verified', filter.verified === true ? null : true)}
            variant={filter.verified === true ? 'primary' : 'secondary'}
            size="sm"
            aria-pressed={filter.verified === true}
          >
            Verified Purchase
          </AccessibleButton>

          {filter.rating && (
            <AccessibleButton
              onClick={() => handleFilterChange('rating', null)}
              variant="secondary"
              size="sm"
              aria-label={`Clear ${filter.rating} star filter`}
            >
              {filter.rating} Stars ✕
            </AccessibleButton>
          )}
        </div>

        <div className="ml-auto text-sm text-gray-600">
          Showing {reviews.length} of {pagination.total} reviews
        </div>
      </div>

      {/* Reviews List */}
      <div className="mt-6 space-y-6" role="feed" aria-busy={isLoading}>
        {isLoading && reviews.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-flex items-center">
              <svg
                className="animate-spin h-5 w-5 text-gray-600 mr-2"
                fill="none"
                viewBox="0 0 24 24"
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
              Loading reviews...
            </div>
          </div>
        ) : reviews.length > 0 ? (
          <>
            {reviews.map((review) => (
              <ReviewItem key={review.id} review={review} />
            ))}

            {/* Load More */}
            {pagination.hasMore && (
              <div className="text-center pt-4">
                <AccessibleButton
                  onClick={handleLoadMore}
                  variant="secondary"
                  isLoading={isLoading}
                  loadingText="Loading more..."
                  aria-label="Load more reviews"
                >
                  Load More Reviews
                </AccessibleButton>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg">No reviews yet</p>
            <p className="mt-2">Be the first to review {productName}!</p>
            <AccessibleButton
              onClick={() => setShowReviewForm(true)}
              variant="primary"
              className="mt-4"
            >
              Write the First Review
            </AccessibleButton>
          </div>
        )}
      </div>

      {/* Review Form Modal */}
      {showReviewForm && (
        <ReviewForm
          productId={productId}
          productName={productName}
          onClose={() => setShowReviewForm(false)}
        />
      )}
    </div>
  );
};

export default ProductReviews;