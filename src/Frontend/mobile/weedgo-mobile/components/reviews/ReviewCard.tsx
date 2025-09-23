import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { Review } from '@/services/reviews';
import { StarRating } from './StarRating';

interface ReviewCardProps {
  review: Review;
  onHelpful?: (helpful: boolean) => void;
  onReport?: () => void;
  showActions?: boolean;
}

export const ReviewCard: React.FC<ReviewCardProps> = ({
  review,
  onHelpful,
  onReport,
  showActions = true,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [helpfulVote, setHelpfulVote] = useState<boolean | null>(null);

  const handleHelpful = (helpful: boolean) => {
    setHelpfulVote(helpful);
    onHelpful?.(helpful);
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const shouldTruncate = review.comment.length > 150;
  const displayComment = expanded || !shouldTruncate
    ? review.comment
    : truncateText(review.comment, 150);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.userInfo}>
          {review.userAvatar ? (
            <Image source={{ uri: review.userAvatar }} style={styles.avatar} />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Text style={styles.avatarText}>
                {review.userName.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          <View style={styles.userDetails}>
            <View style={styles.nameRow}>
              <Text style={styles.userName}>{review.userName}</Text>
              {review.verified && (
                <View style={styles.verifiedBadge}>
                  <Ionicons name="checkmark-circle" size={14} color={Colors.light.success} />
                  <Text style={styles.verifiedText}>Verified</Text>
                </View>
              )}
            </View>
            <Text style={styles.date}>{formatDate(review.createdAt)}</Text>
          </View>
        </View>
        <StarRating rating={review.rating} size={16} />
      </View>

      {/* Review Title */}
      {review.title && (
        <Text style={styles.title}>{review.title}</Text>
      )}

      {/* Review Comment */}
      <Text style={styles.comment}>{displayComment}</Text>
      {shouldTruncate && (
        <TouchableOpacity onPress={() => setExpanded(!expanded)}>
          <Text style={styles.readMore}>
            {expanded ? 'Show less' : 'Read more'}
          </Text>
        </TouchableOpacity>
      )}

      {/* Review Images */}
      {review.images && review.images.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.imagesContainer}
        >
          {review.images.map((image, index) => (
            <TouchableOpacity key={index} style={styles.imageWrapper}>
              <Image source={{ uri: image }} style={styles.reviewImage} />
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Actions */}
      {showActions && (
        <View style={styles.actions}>
          <View style={styles.helpfulSection}>
            <Text style={styles.helpfulText}>Was this helpful?</Text>
            <View style={styles.helpfulButtons}>
              <TouchableOpacity
                style={[
                  styles.helpfulButton,
                  helpfulVote === true && styles.helpfulButtonActive,
                ]}
                onPress={() => handleHelpful(true)}
              >
                <Ionicons
                  name="thumbs-up-outline"
                  size={16}
                  color={helpfulVote === true ? Colors.light.primary : Colors.light.gray}
                />
                <Text
                  style={[
                    styles.helpfulCount,
                    helpfulVote === true && styles.helpfulCountActive,
                  ]}
                >
                  {review.helpful + (helpfulVote === true ? 1 : 0)}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.helpfulButton,
                  helpfulVote === false && styles.helpfulButtonActive,
                ]}
                onPress={() => handleHelpful(false)}
              >
                <Ionicons
                  name="thumbs-down-outline"
                  size={16}
                  color={helpfulVote === false ? Colors.light.primary : Colors.light.gray}
                />
                <Text
                  style={[
                    styles.helpfulCount,
                    helpfulVote === false && styles.helpfulCountActive,
                  ]}
                >
                  {review.unhelpful + (helpfulVote === false ? 1 : 0)}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
          {onReport && (
            <TouchableOpacity onPress={onReport} style={styles.reportButton}>
              <Ionicons name="flag-outline" size={16} color={Colors.light.gray} />
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  userInfo: {
    flexDirection: 'row',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  avatarPlaceholder: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.light.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.primary,
  },
  userDetails: {
    marginLeft: 12,
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  userName: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.light.success + '10',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  verifiedText: {
    fontSize: 11,
    color: Colors.light.success,
  },
  date: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
  },
  comment: {
    fontSize: 14,
    color: Colors.light.text,
    lineHeight: 20,
  },
  readMore: {
    fontSize: 14,
    color: Colors.light.primary,
    marginTop: 4,
  },
  imagesContainer: {
    marginTop: 12,
    marginHorizontal: -4,
  },
  imageWrapper: {
    marginHorizontal: 4,
  },
  reviewImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
  },
  helpfulSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  helpfulText: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  helpfulButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  helpfulButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  helpfulButtonActive: {
    borderColor: Colors.light.primary,
    backgroundColor: Colors.light.primary + '10',
  },
  helpfulCount: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  helpfulCountActive: {
    color: Colors.light.primary,
  },
  reportButton: {
    padding: 4,
  },
});