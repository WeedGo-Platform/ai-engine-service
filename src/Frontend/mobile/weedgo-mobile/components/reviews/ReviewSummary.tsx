import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { ReviewStats } from '@/services/reviews';
import { StarRating } from './StarRating';

interface ReviewSummaryProps {
  stats: ReviewStats;
  onFilterByRating?: (rating: number) => void;
  onWriteReview?: () => void;
  showWriteButton?: boolean;
}

export const ReviewSummary: React.FC<ReviewSummaryProps> = ({
  stats,
  onFilterByRating,
  onWriteReview,
  showWriteButton = true,
}) => {
  const renderRatingBar = (rating: number, count: number) => {
    const percentage = stats.totalReviews > 0
      ? (count / stats.totalReviews) * 100
      : 0;

    return (
      <TouchableOpacity
        key={rating}
        style={styles.ratingBar}
        onPress={() => onFilterByRating?.(rating)}
        disabled={!onFilterByRating}
      >
        <Text style={styles.ratingNumber}>{rating}</Text>
        <Ionicons
          name="star"
          size={12}
          color={Colors.light.star}
          style={styles.starIcon}
        />
        <View style={styles.barContainer}>
          <View
            style={[
              styles.barFill,
              { width: `${percentage}%` },
            ]}
          />
        </View>
        <Text style={styles.countText}>{count}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Overall Rating */}
      <View style={styles.overallSection}>
        <View style={styles.ratingInfo}>
          <Text style={styles.averageRating}>
            {stats.averageRating.toFixed(1)}
          </Text>
          <StarRating rating={stats.averageRating} size={20} />
          <Text style={styles.totalReviews}>
            {stats.totalReviews} {stats.totalReviews === 1 ? 'review' : 'reviews'}
          </Text>
          {stats.recommendationRate > 0 && (
            <Text style={styles.recommendText}>
              {Math.round(stats.recommendationRate)}% recommend
            </Text>
          )}
        </View>

        {/* Write Review Button */}
        {showWriteButton && (
          <TouchableOpacity
            style={styles.writeButton}
            onPress={onWriteReview}
          >
            <Ionicons name="create-outline" size={20} color="white" />
            <Text style={styles.writeButtonText}>Write Review</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Rating Distribution */}
      <View style={styles.distribution}>
        {[5, 4, 3, 2, 1].map((rating) =>
          renderRatingBar(rating, stats.ratingDistribution[rating as keyof typeof stats.ratingDistribution])
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  overallSection: {
    marginBottom: 20,
  },
  ratingInfo: {
    alignItems: 'center',
    marginBottom: 16,
  },
  averageRating: {
    fontSize: 48,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 8,
  },
  totalReviews: {
    fontSize: 14,
    color: Colors.light.gray,
    marginTop: 8,
  },
  recommendText: {
    fontSize: 14,
    color: Colors.light.success,
    marginTop: 4,
  },
  writeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.light.primary,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 24,
  },
  writeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  distribution: {
    marginTop: 8,
  },
  ratingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  ratingNumber: {
    fontSize: 14,
    color: Colors.light.text,
    width: 16,
    textAlign: 'right',
  },
  starIcon: {
    marginLeft: 4,
    marginRight: 8,
  },
  barContainer: {
    flex: 1,
    height: 8,
    backgroundColor: Colors.light.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: Colors.light.star,
    borderRadius: 4,
  },
  countText: {
    fontSize: 12,
    color: Colors.light.gray,
    marginLeft: 8,
    width: 30,
  },
});