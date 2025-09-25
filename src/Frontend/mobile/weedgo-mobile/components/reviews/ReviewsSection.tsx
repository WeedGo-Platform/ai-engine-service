import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { reviewService, Review, ReviewStats, ReviewFilters } from '@/services/reviews';
import { ReviewSummary } from './ReviewSummary';
import { ReviewCard } from './ReviewCard';
import { WriteReviewModal } from './WriteReviewModal';
import { useAuthStore } from '@/stores/authStore';

interface ReviewsSectionProps {
  productId: string;
  productName: string;
}

export const ReviewsSection: React.FC<ReviewsSectionProps> = ({
  productId,
  productName,
}) => {
  const { user } = useAuthStore();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showWriteModal, setShowWriteModal] = useState(false);
  const [filters, setFilters] = useState<ReviewFilters>({
    sortBy: 'newest',
    limit: 10,
    offset: 0,
  });
  const [hasMore, setHasMore] = useState(true);
  const [selectedRating, setSelectedRating] = useState<number | undefined>();

  useEffect(() => {
    loadReviews();
  }, [productId, filters.sortBy, selectedRating]);

  const loadReviews = async (append = false) => {
    try {
      if (!append) {
        setLoading(true);
      }

      const result = await reviewService.getProductReviews(productId, {
        ...filters,
        rating: selectedRating,
        offset: append ? reviews.length : 0,
      });

      if (append) {
        setReviews([...reviews, ...result.reviews]);
      } else {
        setReviews(result.reviews);
      }

      setStats(result.stats);
      setHasMore(result.reviews.length >= (filters.limit || 10));
    } catch (error) {
      console.error('Failed to load reviews:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadReviews();
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      setLoadingMore(true);
      loadReviews(true);
    }
  };

  const handleFilterByRating = (rating: number) => {
    setSelectedRating(rating === selectedRating ? undefined : rating);
  };

  const handleSortChange = (sortBy: ReviewFilters['sortBy']) => {
    setFilters({ ...filters, sortBy });
  };

  const handleHelpful = async (reviewId: string, helpful: boolean) => {
    await reviewService.markReviewHelpful(reviewId, helpful);
  };

  const handleReviewSubmitted = () => {
    loadReviews();
  };

  const handleWriteReview = () => {
    if (!user) {
      // Could show login prompt
      console.log('User needs to be logged in to write reviews');
      return;
    }
    setShowWriteModal(true);
  };

  const renderSortOptions = () => (
    <View style={styles.sortContainer}>
      <Text style={styles.sortLabel}>Sort by:</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {[
          { key: 'newest', label: 'Newest' },
          { key: 'oldest', label: 'Oldest' },
          { key: 'helpful', label: 'Most Helpful' },
          { key: 'rating_high', label: 'Highest Rating' },
          { key: 'rating_low', label: 'Lowest Rating' },
        ].map((option) => (
          <TouchableOpacity
            key={option.key}
            style={[
              styles.sortButton,
              filters.sortBy === option.key && styles.sortButtonActive,
            ]}
            onPress={() => handleSortChange(option.key as ReviewFilters['sortBy'])}
          >
            <Text
              style={[
                styles.sortButtonText,
                filters.sortBy === option.key && styles.sortButtonTextActive,
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  const renderRatingFilter = () => {
    if (!selectedRating) return null;

    return (
      <View style={styles.filterBar}>
        <Text style={styles.filterText}>
          Showing {selectedRating} star reviews
        </Text>
        <TouchableOpacity onPress={() => setSelectedRating(undefined)}>
          <Ionicons name="close-circle" size={20} color={Colors.light.gray} />
        </TouchableOpacity>
      </View>
    );
  };

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="chatbubbles-outline" size={64} color={Colors.light.gray} />
      <Text style={styles.emptyTitle}>No reviews yet</Text>
      <Text style={styles.emptySubtitle}>Be the first to review this product</Text>
      {user && (
        <TouchableOpacity style={styles.writeFirstButton} onPress={handleWriteReview}>
          <Text style={styles.writeFirstButtonText}>Write a Review</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={Colors.light.primary} />
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Review Summary */}
      {stats && (
        <ReviewSummary
          stats={stats}
          onFilterByRating={handleFilterByRating}
          onWriteReview={handleWriteReview}
          showWriteButton={!!user}
        />
      )}

      {/* Rating Filter */}
      {renderRatingFilter()}

      {/* Sort Options */}
      {reviews.length > 0 && renderSortOptions()}

      {/* Reviews List */}
      <FlatList
        data={reviews}
        renderItem={({ item }) => (
          <ReviewCard
            review={item}
            onHelpful={(helpful) => handleHelpful(item.id, helpful)}
          />
        )}
        keyExtractor={(item, index) => `${item.id}-${index}`}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={renderFooter}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        scrollEnabled={false}
        nestedScrollEnabled
      />

      {/* Write Review Modal */}
      <WriteReviewModal
        visible={showWriteModal}
        onClose={() => setShowWriteModal(false)}
        productId={productId}
        productName={productName}
        onSubmit={handleReviewSubmitted}
      />
    </View>
  );
};

// Import ScrollView at top of file
import { ScrollView } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  sortContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  sortLabel: {
    fontSize: 14,
    color: Colors.light.gray,
    marginRight: 12,
  },
  sortButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.light.border,
    marginRight: 8,
  },
  sortButtonActive: {
    backgroundColor: Colors.light.primary,
    borderColor: Colors.light.primary,
  },
  sortButtonText: {
    fontSize: 14,
    color: Colors.light.text,
  },
  sortButtonTextActive: {
    color: 'white',
  },
  filterBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.light.primary + '10',
    marginBottom: 8,
  },
  filterText: {
    fontSize: 14,
    color: Colors.light.primary,
  },
  emptyContainer: {
    padding: 48,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.light.gray,
    marginTop: 8,
  },
  writeFirstButton: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.light.primary,
    borderRadius: 24,
  },
  writeFirstButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  footerLoader: {
    paddingVertical: 16,
    alignItems: 'center',
  },
});