import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';

interface StarRatingProps {
  rating: number;
  maxRating?: number;
  size?: number;
  color?: string;
  editable?: boolean;
  onRatingChange?: (rating: number) => void;
  showHalfStars?: boolean;
}

export const StarRating: React.FC<StarRatingProps> = ({
  rating,
  maxRating = 5,
  size = 20,
  color = Colors.light.star,
  editable = false,
  onRatingChange,
  showHalfStars = true,
}) => {
  const handlePress = (starIndex: number) => {
    if (editable && onRatingChange) {
      onRatingChange(starIndex);
    }
  };

  const renderStar = (index: number) => {
    const starNumber = index + 1;
    let iconName: keyof typeof Ionicons.glyphMap = 'star-outline';

    if (showHalfStars) {
      if (rating >= starNumber) {
        iconName = 'star';
      } else if (rating >= starNumber - 0.5) {
        iconName = 'star-half';
      }
    } else {
      if (rating >= starNumber) {
        iconName = 'star';
      }
    }

    const Star = (
      <Ionicons
        name={iconName}
        size={size}
        color={color}
        style={styles.star}
      />
    );

    if (editable) {
      return (
        <TouchableOpacity
          key={index}
          onPress={() => handlePress(starNumber)}
          style={styles.starButton}
        >
          {Star}
        </TouchableOpacity>
      );
    }

    return <View key={index}>{Star}</View>;
  };

  return (
    <View style={styles.container}>
      {Array.from({ length: maxRating }, (_, index) => renderStar(index))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  star: {
    marginHorizontal: 2,
  },
  starButton: {
    padding: 2,
  },
});