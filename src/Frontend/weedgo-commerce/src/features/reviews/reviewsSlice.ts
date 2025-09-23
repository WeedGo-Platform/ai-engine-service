/**
 * Redux slice for product reviews and ratings management
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '@api/client';

// Types
export interface Review {
  id: string;
  productId: string;
  userId: string;
  userName: string;
  rating: number; // 1-5
  title: string;
  comment: string;
  verified: boolean;
  helpful: number;
  notHelpful: number;
  userVote?: 'helpful' | 'not-helpful' | null;
  images?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ReviewStats {
  averageRating: number;
  totalReviews: number;
  ratingDistribution: {
    1: number;
    2: number;
    3: number;
    4: number;
    5: number;
  };
  verifiedPurchasePercentage: number;
}

interface ReviewsState {
  reviews: Record<string, Review[]>; // Keyed by productId
  stats: Record<string, ReviewStats>; // Keyed by productId
  userReviews: Review[];
  currentReview: Review | null;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  filter: {
    rating: number | null;
    verified: boolean | null;
    sortBy: 'newest' | 'oldest' | 'highest' | 'lowest' | 'helpful';
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasMore: boolean;
  };
}

const initialState: ReviewsState = {
  reviews: {},
  stats: {},
  userReviews: [],
  currentReview: null,
  isLoading: false,
  isSubmitting: false,
  error: null,
  filter: {
    rating: null,
    verified: null,
    sortBy: 'newest',
  },
  pagination: {
    page: 1,
    limit: 10,
    total: 0,
    hasMore: true,
  },
};

// Async thunks
export const fetchProductReviews = createAsyncThunk(
  'reviews/fetchProductReviews',
  async ({
    productId,
    page = 1,
    limit = 10,
    rating,
    verified,
    sortBy = 'newest',
  }: {
    productId: string;
    page?: number;
    limit?: number;
    rating?: number;
    verified?: boolean;
    sortBy?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      sort: sortBy,
    });

    if (rating) params.append('rating', rating.toString());
    if (verified !== undefined) params.append('verified', verified.toString());

    const response = await apiClient.get(`/api/products/${productId}/reviews?${params}`);
    return {
      productId,
      reviews: response.data.reviews,
      total: response.data.total,
      page,
      limit,
    };
  }
);

export const fetchProductStats = createAsyncThunk(
  'reviews/fetchProductStats',
  async (productId: string) => {
    const response = await apiClient.get(`/api/products/${productId}/reviews/stats`);
    return {
      productId,
      stats: response.data,
    };
  }
);

export const submitReview = createAsyncThunk(
  'reviews/submitReview',
  async ({
    productId,
    rating,
    title,
    comment,
    images,
  }: {
    productId: string;
    rating: number;
    title: string;
    comment: string;
    images?: File[];
  }) => {
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('rating', rating.toString());
    formData.append('title', title);
    formData.append('comment', comment);

    if (images && images.length > 0) {
      images.forEach((image, index) => {
        formData.append(`images`, image);
      });
    }

    const response = await apiClient.post('/api/reviews', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }
);

export const updateReview = createAsyncThunk(
  'reviews/updateReview',
  async ({
    reviewId,
    rating,
    title,
    comment,
  }: {
    reviewId: string;
    rating?: number;
    title?: string;
    comment?: string;
  }) => {
    const response = await apiClient.patch(`/api/reviews/${reviewId}`, {
      rating,
      title,
      comment,
    });
    return response.data;
  }
);

export const deleteReview = createAsyncThunk(
  'reviews/deleteReview',
  async (reviewId: string) => {
    await apiClient.delete(`/api/reviews/${reviewId}`);
    return reviewId;
  }
);

export const voteReview = createAsyncThunk(
  'reviews/voteReview',
  async ({
    reviewId,
    vote,
  }: {
    reviewId: string;
    vote: 'helpful' | 'not-helpful';
  }) => {
    const response = await apiClient.post(`/api/reviews/${reviewId}/vote`, { vote });
    return {
      reviewId,
      vote,
      helpful: response.data.helpful,
      notHelpful: response.data.notHelpful,
    };
  }
);

export const fetchUserReviews = createAsyncThunk(
  'reviews/fetchUserReviews',
  async () => {
    const response = await apiClient.get('/api/user/reviews');
    return response.data.reviews;
  }
);

export const reportReview = createAsyncThunk(
  'reviews/reportReview',
  async ({
    reviewId,
    reason,
    details,
  }: {
    reviewId: string;
    reason: string;
    details?: string;
  }) => {
    const response = await apiClient.post(`/api/reviews/${reviewId}/report`, {
      reason,
      details,
    });
    return response.data;
  }
);

// Slice
const reviewsSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    setFilter: (state, action: PayloadAction<Partial<ReviewsState['filter']>>) => {
      state.filter = { ...state.filter, ...action.payload };
      state.pagination.page = 1; // Reset to first page when filter changes
    },
    resetFilter: (state) => {
      state.filter = initialState.filter;
      state.pagination = initialState.pagination;
    },
    clearError: (state) => {
      state.error = null;
    },
    setCurrentReview: (state, action: PayloadAction<Review | null>) => {
      state.currentReview = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch product reviews
    builder
      .addCase(fetchProductReviews.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchProductReviews.fulfilled, (state, action) => {
        const { productId, reviews, total, page, limit } = action.payload;

        if (page === 1) {
          state.reviews[productId] = reviews;
        } else {
          state.reviews[productId] = [...(state.reviews[productId] || []), ...reviews];
        }

        state.pagination = {
          page,
          limit,
          total,
          hasMore: page * limit < total,
        };
        state.isLoading = false;
      })
      .addCase(fetchProductReviews.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch reviews';
      });

    // Fetch product stats
    builder
      .addCase(fetchProductStats.fulfilled, (state, action) => {
        const { productId, stats } = action.payload;
        state.stats[productId] = stats;
      });

    // Submit review
    builder
      .addCase(submitReview.pending, (state) => {
        state.isSubmitting = true;
        state.error = null;
      })
      .addCase(submitReview.fulfilled, (state, action) => {
        const review = action.payload;

        // Add to product reviews
        if (!state.reviews[review.productId]) {
          state.reviews[review.productId] = [];
        }
        state.reviews[review.productId].unshift(review);

        // Add to user reviews
        state.userReviews.unshift(review);

        // Update stats (increment count)
        if (state.stats[review.productId]) {
          state.stats[review.productId].totalReviews += 1;
          // Recalculate average (simplified - should refetch for accuracy)
          const currentTotal = state.stats[review.productId].averageRating * (state.stats[review.productId].totalReviews - 1);
          state.stats[review.productId].averageRating = (currentTotal + review.rating) / state.stats[review.productId].totalReviews;
        }

        state.isSubmitting = false;
      })
      .addCase(submitReview.rejected, (state, action) => {
        state.isSubmitting = false;
        state.error = action.error.message || 'Failed to submit review';
      });

    // Update review
    builder
      .addCase(updateReview.pending, (state) => {
        state.isSubmitting = true;
        state.error = null;
      })
      .addCase(updateReview.fulfilled, (state, action) => {
        const updatedReview = action.payload;

        // Update in product reviews
        const productReviews = state.reviews[updatedReview.productId];
        if (productReviews) {
          const index = productReviews.findIndex(r => r.id === updatedReview.id);
          if (index !== -1) {
            productReviews[index] = updatedReview;
          }
        }

        // Update in user reviews
        const userIndex = state.userReviews.findIndex(r => r.id === updatedReview.id);
        if (userIndex !== -1) {
          state.userReviews[userIndex] = updatedReview;
        }

        state.isSubmitting = false;
      })
      .addCase(updateReview.rejected, (state, action) => {
        state.isSubmitting = false;
        state.error = action.error.message || 'Failed to update review';
      });

    // Delete review
    builder
      .addCase(deleteReview.fulfilled, (state, action) => {
        const reviewId = action.payload;

        // Remove from all product reviews
        Object.keys(state.reviews).forEach(productId => {
          state.reviews[productId] = state.reviews[productId].filter(r => r.id !== reviewId);
        });

        // Remove from user reviews
        state.userReviews = state.userReviews.filter(r => r.id !== reviewId);
      });

    // Vote review
    builder
      .addCase(voteReview.fulfilled, (state, action) => {
        const { reviewId, vote, helpful, notHelpful } = action.payload;

        // Update in all product reviews
        Object.keys(state.reviews).forEach(productId => {
          const review = state.reviews[productId].find(r => r.id === reviewId);
          if (review) {
            review.helpful = helpful;
            review.notHelpful = notHelpful;
            review.userVote = vote;
          }
        });
      });

    // Fetch user reviews
    builder
      .addCase(fetchUserReviews.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchUserReviews.fulfilled, (state, action) => {
        state.userReviews = action.payload;
        state.isLoading = false;
      })
      .addCase(fetchUserReviews.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch user reviews';
      });
  },
});

// Actions
export const { setFilter, resetFilter, clearError, setCurrentReview } = reviewsSlice.actions;

// Selectors
export const selectProductReviews = (state: { reviews: ReviewsState }, productId: string) =>
  state.reviews.reviews[productId] || [];

export const selectProductStats = (state: { reviews: ReviewsState }, productId: string) =>
  state.reviews.stats[productId] || null;

export const selectUserReviews = (state: { reviews: ReviewsState }) =>
  state.reviews.userReviews;

export const selectReviewsFilter = (state: { reviews: ReviewsState }) =>
  state.reviews.filter;

export const selectReviewsPagination = (state: { reviews: ReviewsState }) =>
  state.reviews.pagination;

export const selectIsLoadingReviews = (state: { reviews: ReviewsState }) =>
  state.reviews.isLoading;

export const selectIsSubmittingReview = (state: { reviews: ReviewsState }) =>
  state.reviews.isSubmitting;

// Export reducer
export default reviewsSlice.reducer;