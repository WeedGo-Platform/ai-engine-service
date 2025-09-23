/**
 * Review submission form component
 */

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';
import { PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { submitReview, selectIsSubmittingReview } from '@features/reviews/reviewsSlice';
import { selectUser } from '@features/auth/authSlice';
import { AccessibleButton, AccessibleInput, AccessibleModal } from '@components/common/AccessibleComponents';
import { validateForm, ValidationSchemas } from '@utils/validation';
import toast from 'react-hot-toast';

interface ReviewFormProps {
  productId: string;
  productName: string;
  onClose: () => void;
}

const ReviewForm: React.FC<ReviewFormProps> = ({ productId, productName, onClose }) => {
  const dispatch = useDispatch();
  const currentUser = useSelector(selectUser);
  const isSubmitting = useSelector(selectIsSubmittingReview);

  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [title, setTitle] = useState('');
  const [comment, setComment] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleRatingClick = (value: number) => {
    setRating(value);
    if (errors.rating) {
      setErrors({ ...errors, rating: '' });
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles: File[] = [];
    const previews: string[] = [];

    files.forEach(file => {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.error(`${file.name} is not an image file`);
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error(`${file.name} is too large (max 5MB)`);
        return;
      }

      validFiles.push(file);
      previews.push(URL.createObjectURL(file));
    });

    if (validFiles.length + images.length > 5) {
      toast.error('You can upload a maximum of 5 images');
      return;
    }

    setImages([...images, ...validFiles]);
    setImagePreviews([...imagePreviews, ...previews]);
  };

  const removeImage = (index: number) => {
    URL.revokeObjectURL(imagePreviews[index]);
    setImages(images.filter((_, i) => i !== index));
    setImagePreviews(imagePreviews.filter((_, i) => i !== index));
  };

  const validateReviewForm = () => {
    const errors: Record<string, string> = {};

    if (!rating) {
      errors.rating = 'Please select a rating';
    }

    if (!title.trim()) {
      errors.title = 'Please enter a title';
    } else if (title.length < 3) {
      errors.title = 'Title must be at least 3 characters';
    } else if (title.length > 100) {
      errors.title = 'Title must be less than 100 characters';
    }

    if (!comment.trim()) {
      errors.comment = 'Please enter your review';
    } else if (comment.length < 10) {
      errors.comment = 'Review must be at least 10 characters';
    } else if (comment.length > 1000) {
      errors.comment = 'Review must be less than 1000 characters';
    }

    setErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!currentUser) {
      toast.error('You must be logged in to write a review');
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return;
    }

    if (!validateReviewForm()) {
      toast.error('Please fix the errors in your review');
      return;
    }

    try {
      await dispatch(submitReview({
        productId,
        rating,
        title: title.trim(),
        comment: comment.trim(),
        images,
      }) as any).unwrap();

      toast.success('Thank you for your review!');
      onClose();
    } catch (error: any) {
      toast.error(error.message || 'Failed to submit review');
    }
  };

  return (
    <AccessibleModal
      isOpen={true}
      onClose={onClose}
      title={`Review ${productName}`}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Rating Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Overall Rating <span className="text-red-500">*</span>
          </label>
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => handleRatingClick(value)}
                onMouseEnter={() => setHoveredRating(value)}
                onMouseLeave={() => setHoveredRating(0)}
                className="p-1 focus:outline-none focus:ring-2 focus:ring-green-500 rounded"
                aria-label={`Rate ${value} star${value !== 1 ? 's' : ''}`}
              >
                {value <= (hoveredRating || rating) ? (
                  <StarIcon className="h-8 w-8 text-yellow-400" />
                ) : (
                  <StarOutlineIcon className="h-8 w-8 text-gray-300" />
                )}
              </button>
            ))}
            <span className="ml-2 text-sm text-gray-600">
              {rating > 0 && `${rating} star${rating !== 1 ? 's' : ''}`}
            </span>
          </div>
          {errors.rating && (
            <p className="mt-1 text-sm text-red-600">{errors.rating}</p>
          )}
        </div>

        {/* Review Title */}
        <AccessibleInput
          label="Review Title"
          placeholder="Summarize your experience"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          error={errors.title}
          required
          maxLength={100}
        />

        {/* Review Comment */}
        <div>
          <label htmlFor="review-comment" className="block text-sm font-medium text-gray-700">
            Your Review <span className="text-red-500">*</span>
          </label>
          <textarea
            id="review-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell others about your experience with this product"
            rows={5}
            maxLength={1000}
            className={`mt-1 block w-full rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 ${
              errors.comment ? 'border-red-500' : 'border-gray-300'
            }`}
            aria-invalid={!!errors.comment}
            aria-describedby={errors.comment ? 'comment-error' : undefined}
          />
          <div className="mt-1 flex justify-between">
            <div>
              {errors.comment && (
                <p id="comment-error" className="text-sm text-red-600">
                  {errors.comment}
                </p>
              )}
            </div>
            <span className="text-xs text-gray-500">
              {comment.length}/1000 characters
            </span>
          </div>
        </div>

        {/* Image Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Add Photos (Optional)
          </label>
          <div className="flex flex-wrap gap-2">
            {imagePreviews.map((preview, index) => (
              <div key={index} className="relative">
                <img
                  src={preview}
                  alt={`Upload ${index + 1}`}
                  className="h-20 w-20 object-cover rounded-lg border border-gray-300"
                />
                <button
                  type="button"
                  onClick={() => removeImage(index)}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  aria-label={`Remove image ${index + 1}`}
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            ))}

            {images.length < 5 && (
              <label className="h-20 w-20 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400 transition-colors">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  className="sr-only"
                  aria-label="Upload images"
                />
                <PhotoIcon className="h-8 w-8 text-gray-400" />
              </label>
            )}
          </div>
          <p className="mt-1 text-xs text-gray-500">
            You can upload up to 5 images (max 5MB each)
          </p>
        </div>

        {/* Guidelines */}
        <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-600">
          <h4 className="font-medium text-gray-700 mb-2">Review Guidelines</h4>
          <ul className="space-y-1 list-disc list-inside">
            <li>Focus on your personal experience with the product</li>
            <li>Be specific about effects, taste, and quality</li>
            <li>Mention if you're a verified purchaser</li>
            <li>Keep language respectful and appropriate</li>
            <li>Do not include personal information</li>
          </ul>
        </div>

        {/* Form Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t">
          <AccessibleButton
            type="button"
            onClick={onClose}
            variant="secondary"
            disabled={isSubmitting}
          >
            Cancel
          </AccessibleButton>
          <AccessibleButton
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            loadingText="Submitting..."
            disabled={!rating || !title.trim() || !comment.trim()}
          >
            Submit Review
          </AccessibleButton>
        </div>
      </form>
    </AccessibleModal>
  );
};

export default ReviewForm;