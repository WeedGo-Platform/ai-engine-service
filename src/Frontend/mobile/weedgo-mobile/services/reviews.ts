import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Review {
  id: string;
  productId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  rating: number; // 1-5
  title: string;
  comment: string;
  images?: string[];
  verified: boolean;
  helpful: number;
  unhelpful: number;
  createdAt: Date;
  updatedAt: Date;
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
  recommendationRate: number;
}

export interface CreateReviewData {
  productId: string;
  rating: number;
  title: string;
  comment: string;
  images?: string[];
  recommend?: boolean;
}

export interface ReviewFilters {
  rating?: number;
  verified?: boolean;
  sortBy?: 'newest' | 'oldest' | 'helpful' | 'rating_high' | 'rating_low';
  limit?: number;
  offset?: number;
}

class ReviewService {
  private apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';

  /**
   * Get reviews for a product
   */
  async getProductReviews(
    productId: string,
    filters?: ReviewFilters
  ): Promise<{ reviews: Review[]; stats: ReviewStats }> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');
      const params = new URLSearchParams();

      if (filters?.rating) params.append('rating', filters.rating.toString());
      if (filters?.verified !== undefined) params.append('verified', filters.verified.toString());
      if (filters?.sortBy) params.append('sort', filters.sortBy);
      if (filters?.limit) params.append('limit', filters.limit.toString());
      if (filters?.offset) params.append('offset', filters.offset.toString());

      const response = await fetch(
        `${this.apiUrl}/api/products/${productId}/reviews?${params.toString()}`,
        {
          headers: {
            'Authorization': authToken ? `Bearer ${authToken}` : '',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return {
          reviews: data.reviews?.map((r: any) => ({
            ...r,
            createdAt: new Date(r.created_at),
            updatedAt: new Date(r.updated_at),
          })) || [],
          stats: data.stats || this.getEmptyStats(),
        };
      }

      // Return empty data if endpoint doesn't exist yet
      return {
        reviews: [],
        stats: this.getEmptyStats(),
      };
    } catch (error) {
      console.error('Failed to get product reviews:', error);
      return {
        reviews: [],
        stats: this.getEmptyStats(),
      };
    }
  }

  /**
   * Get review statistics for a product
   */
  async getProductReviewStats(productId: string): Promise<ReviewStats> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(
        `${this.apiUrl}/api/products/${productId}/reviews/stats`,
        {
          headers: {
            'Authorization': authToken ? `Bearer ${authToken}` : '',
          },
        }
      );

      if (response.ok) {
        return await response.json();
      }

      return this.getEmptyStats();
    } catch (error) {
      console.error('Failed to get review stats:', error);
      return this.getEmptyStats();
    }
  }

  /**
   * Submit a review
   */
  async submitReview(data: CreateReviewData): Promise<Review | null> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      if (!authToken) {
        console.error('User must be logged in to submit reviews');
        return null;
      }

      const response = await fetch(
        `${this.apiUrl}/api/products/${data.productId}/reviews`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            rating: data.rating,
            title: data.title,
            comment: data.comment,
            images: data.images,
            recommend: data.recommend,
          }),
        }
      );

      if (response.ok) {
        const review = await response.json();
        return {
          ...review,
          createdAt: new Date(review.created_at),
          updatedAt: new Date(review.updated_at),
        };
      }

      return null;
    } catch (error) {
      console.error('Failed to submit review:', error);
      return null;
    }
  }

  /**
   * Update a review
   */
  async updateReview(reviewId: string, data: Partial<CreateReviewData>): Promise<boolean> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      if (!authToken) {
        return false;
      }

      const response = await fetch(
        `${this.apiUrl}/api/reviews/${reviewId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify(data),
        }
      );

      return response.ok;
    } catch (error) {
      console.error('Failed to update review:', error);
      return false;
    }
  }

  /**
   * Delete a review
   */
  async deleteReview(reviewId: string): Promise<boolean> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      if (!authToken) {
        return false;
      }

      const response = await fetch(
        `${this.apiUrl}/api/reviews/${reviewId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      return response.ok;
    } catch (error) {
      console.error('Failed to delete review:', error);
      return false;
    }
  }

  /**
   * Mark a review as helpful/unhelpful
   */
  async markReviewHelpful(reviewId: string, helpful: boolean): Promise<boolean> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(
        `${this.apiUrl}/api/reviews/${reviewId}/helpful`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authToken ? `Bearer ${authToken}` : '',
          },
          body: JSON.stringify({ helpful }),
        }
      );

      return response.ok;
    } catch (error) {
      console.error('Failed to mark review helpful:', error);
      return false;
    }
  }

  /**
   * Get user's review for a product
   */
  async getUserReviewForProduct(productId: string): Promise<Review | null> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      if (!authToken) {
        return null;
      }

      const response = await fetch(
        `${this.apiUrl}/api/products/${productId}/reviews/mine`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      if (response.ok) {
        const review = await response.json();
        return {
          ...review,
          createdAt: new Date(review.created_at),
          updatedAt: new Date(review.updated_at),
        };
      }

      return null;
    } catch (error) {
      console.error('Failed to get user review:', error);
      return null;
    }
  }

  /**
   * Upload review images
   */
  async uploadReviewImages(images: string[]): Promise<string[]> {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');

      if (!authToken) {
        return [];
      }

      const formData = new FormData();
      images.forEach((imageUri, index) => {
        formData.append('images', {
          uri: imageUri,
          type: 'image/jpeg',
          name: `review-image-${index}.jpg`,
        } as any);
      });

      const response = await fetch(
        `${this.apiUrl}/api/reviews/upload-images`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
          body: formData,
        }
      );

      if (response.ok) {
        const data = await response.json();
        return data.urls || [];
      }

      return [];
    } catch (error) {
      console.error('Failed to upload review images:', error);
      return [];
    }
  }

  /**
   * Get empty stats object
   */
  private getEmptyStats(): ReviewStats {
    return {
      averageRating: 0,
      totalReviews: 0,
      ratingDistribution: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
      },
      recommendationRate: 0,
    };
  }
}

// Export singleton instance
export const reviewService = new ReviewService();