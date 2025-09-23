import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { Colors } from '@/constants/Colors';
import { StarRating } from './StarRating';
import { CreateReviewData, reviewService } from '@/services/reviews';
import * as Haptics from 'expo-haptics';

interface WriteReviewModalProps {
  visible: boolean;
  onClose: () => void;
  productId: string;
  productName: string;
  onSubmit: () => void;
}

export const WriteReviewModal: React.FC<WriteReviewModalProps> = ({
  visible,
  onClose,
  productId,
  productName,
  onSubmit,
}) => {
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState('');
  const [comment, setComment] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [recommend, setRecommend] = useState<boolean | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRatingChange = (newRating: number) => {
    setRating(newRating);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handlePickImage = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Please allow access to your photo library');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      quality: 0.8,
      selectionLimit: 5 - images.length,
    });

    if (!result.canceled && result.assets) {
      const newImages = result.assets.map(asset => asset.uri);
      setImages([...images, ...newImages].slice(0, 5));
    }
  };

  const handleTakePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Please allow access to your camera');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      quality: 0.8,
    });

    if (!result.canceled && result.assets?.[0]) {
      setImages([...images, result.assets[0].uri].slice(0, 5));
    }
  };

  const handleRemoveImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const handleSubmitReview = async () => {
    if (rating === 0) {
      Alert.alert('Rating required', 'Please select a rating');
      return;
    }

    if (comment.trim().length < 10) {
      Alert.alert('Review too short', 'Please write at least 10 characters');
      return;
    }

    setIsSubmitting(true);

    try {
      const reviewData: CreateReviewData = {
        productId,
        rating,
        title: title.trim(),
        comment: comment.trim(),
        images: images.length > 0 ? images : undefined,
        recommend,
      };

      const result = await reviewService.submitReview(reviewData);

      if (result) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        onSubmit();
        handleClose();
      } else {
        Alert.alert('Error', 'Failed to submit review. Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setRating(0);
    setTitle('');
    setComment('');
    setImages([]);
    setRecommend(null);
    onClose();
  };

  const isValid = rating > 0 && comment.trim().length >= 10;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <SafeAreaView style={styles.container} edges={['top']}>
        <KeyboardAvoidingView
          style={styles.container}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={Colors.light.text} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Write a Review</Text>
            <TouchableOpacity
              onPress={handleSubmitReview}
              disabled={!isValid || isSubmitting}
              style={[
                styles.submitButton,
                (!isValid || isSubmitting) && styles.submitButtonDisabled,
              ]}
            >
              {isSubmitting ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.submitButtonText}>Submit</Text>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            {/* Product Name */}
            <Text style={styles.productName}>{productName}</Text>

            {/* Rating */}
            <View style={styles.ratingSection}>
              <Text style={styles.sectionTitle}>Your Rating</Text>
              <StarRating
                rating={rating}
                size={36}
                editable
                onRatingChange={handleRatingChange}
              />
              <Text style={styles.ratingHint}>Tap to rate</Text>
            </View>

            {/* Recommendation */}
            <View style={styles.recommendSection}>
              <Text style={styles.sectionTitle}>Would you recommend this product?</Text>
              <View style={styles.recommendButtons}>
                <TouchableOpacity
                  style={[
                    styles.recommendButton,
                    recommend === true && styles.recommendButtonActive,
                  ]}
                  onPress={() => setRecommend(true)}
                >
                  <Ionicons
                    name="thumbs-up"
                    size={24}
                    color={recommend === true ? 'white' : Colors.light.text}
                  />
                  <Text
                    style={[
                      styles.recommendButtonText,
                      recommend === true && styles.recommendButtonTextActive,
                    ]}
                  >
                    Yes
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.recommendButton,
                    recommend === false && styles.recommendButtonActive,
                  ]}
                  onPress={() => setRecommend(false)}
                >
                  <Ionicons
                    name="thumbs-down"
                    size={24}
                    color={recommend === false ? 'white' : Colors.light.text}
                  />
                  <Text
                    style={[
                      styles.recommendButtonText,
                      recommend === false && styles.recommendButtonTextActive,
                    ]}
                  >
                    No
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Review Title */}
            <View style={styles.inputSection}>
              <Text style={styles.sectionTitle}>Review Title (Optional)</Text>
              <TextInput
                style={styles.titleInput}
                placeholder="Summarize your experience"
                value={title}
                onChangeText={setTitle}
                maxLength={100}
                placeholderTextColor={Colors.light.gray}
              />
            </View>

            {/* Review Comment */}
            <View style={styles.inputSection}>
              <Text style={styles.sectionTitle}>Your Review</Text>
              <TextInput
                style={styles.commentInput}
                placeholder="Tell us about your experience with this product..."
                value={comment}
                onChangeText={setComment}
                multiline
                maxLength={1000}
                placeholderTextColor={Colors.light.gray}
              />
              <Text style={styles.charCount}>
                {comment.length}/1000 characters
              </Text>
            </View>

            {/* Images */}
            <View style={styles.imagesSection}>
              <Text style={styles.sectionTitle}>Add Photos (Optional)</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={styles.imagesScroll}
              >
                {images.map((image, index) => (
                  <View key={index} style={styles.imageWrapper}>
                    <Image source={{ uri: image }} style={styles.reviewImage} />
                    <TouchableOpacity
                      style={styles.removeImageButton}
                      onPress={() => handleRemoveImage(index)}
                    >
                      <Ionicons name="close-circle" size={24} color={Colors.light.error} />
                    </TouchableOpacity>
                  </View>
                ))}
                {images.length < 5 && (
                  <View style={styles.addImageButtons}>
                    <TouchableOpacity
                      style={styles.addImageButton}
                      onPress={handlePickImage}
                    >
                      <Ionicons name="image-outline" size={32} color={Colors.light.gray} />
                      <Text style={styles.addImageText}>Gallery</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.addImageButton}
                      onPress={handleTakePhoto}
                    >
                      <Ionicons name="camera-outline" size={32} color={Colors.light.gray} />
                      <Text style={styles.addImageText}>Camera</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </ScrollView>
              {images.length > 0 && (
                <Text style={styles.imageCount}>{images.length}/5 photos</Text>
              )}
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
  },
  submitButton: {
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
    minWidth: 80,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: Colors.light.gray,
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  productName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 24,
  },
  ratingSection: {
    alignItems: 'center',
    marginBottom: 24,
    paddingVertical: 16,
    backgroundColor: Colors.light.card,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  ratingHint: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 8,
  },
  recommendSection: {
    marginBottom: 24,
  },
  recommendButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  recommendButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.light.border,
    backgroundColor: Colors.light.card,
  },
  recommendButtonActive: {
    backgroundColor: Colors.light.primary,
    borderColor: Colors.light.primary,
  },
  recommendButtonText: {
    fontSize: 16,
    color: Colors.light.text,
  },
  recommendButtonTextActive: {
    color: 'white',
  },
  inputSection: {
    marginBottom: 24,
  },
  titleInput: {
    backgroundColor: Colors.light.card,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: Colors.light.text,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  commentInput: {
    backgroundColor: Colors.light.card,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: Colors.light.text,
    minHeight: 120,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  charCount: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 4,
    textAlign: 'right',
  },
  imagesSection: {
    marginBottom: 24,
  },
  imagesScroll: {
    marginTop: 8,
  },
  imageWrapper: {
    marginRight: 12,
  },
  reviewImage: {
    width: 100,
    height: 100,
    borderRadius: 8,
  },
  removeImageButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: 'white',
    borderRadius: 12,
  },
  addImageButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  addImageButton: {
    width: 100,
    height: 100,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: Colors.light.border,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.light.card,
  },
  addImageText: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 4,
  },
  imageCount: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 8,
  },
});