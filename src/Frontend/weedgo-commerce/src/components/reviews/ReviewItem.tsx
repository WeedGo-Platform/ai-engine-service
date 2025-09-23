/**
 * Individual review item component
 */

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { StarIcon } from '@heroicons/react/24/solid';
import { HandThumbUpIcon, HandThumbDownIcon, FlagIcon } from '@heroicons/react/24/outline';
import { Review, voteReview, reportReview } from '@features/reviews/reviewsSlice';
import { selectUser } from '@features/auth/authSlice';
import { formatDistanceToNow } from 'date-fns';
import { AccessibleButton } from '@components/common/AccessibleComponents';

interface ReviewItemProps {
  review: Review;
}

const ReviewItem: React.FC<ReviewItemProps> = ({ review }) => {
  const dispatch = useDispatch();
  const currentUser = useSelector(selectUser);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const [reportDetails, setReportDetails] = useState('');

  const handleVote = (vote: 'helpful' | 'not-helpful') => {
    if (currentUser) {
      dispatch(voteReview({ reviewId: review.id, vote }) as any);
    } else {
      // Redirect to login
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
    }
  };

  const handleReport = () => {
    if (!currentUser) {
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return;
    }

    if (reportReason) {
      dispatch(reportReview({
        reviewId: review.id,
        reason: reportReason,
        details: reportDetails,
      }) as any);
      setShowReportModal(false);
      setReportReason('');
      setReportDetails('');
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center" role="img" aria-label={`${rating} out of 5 stars`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <StarIcon
            key={star}
            className={`h-4 w-4 ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            aria-hidden="true"
          />
        ))}
      </div>
    );
  };

  return (
    <article className="border-b pb-6" aria-label={`Review by ${review.userName}`}>
      {/* Review Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2">
            {renderStars(review.rating)}
            <span className="text-sm font-medium text-gray-900">{review.title}</span>
          </div>
          <div className="mt-1 flex items-center space-x-2 text-sm text-gray-500">
            <span className="font-medium">{review.userName}</span>
            <span aria-hidden="true">·</span>
            <time dateTime={review.createdAt}>
              {formatDistanceToNow(new Date(review.createdAt), { addSuffix: true })}
            </time>
            {review.verified && (
              <>
                <span aria-hidden="true">·</span>
                <span className="text-green-600 flex items-center">
                  <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Verified Purchase
                </span>
              </>
            )}
          </div>
        </div>

        {/* Report Button */}
        <button
          onClick={() => setShowReportModal(true)}
          className="text-gray-400 hover:text-gray-500 p-1"
          aria-label="Report this review"
        >
          <FlagIcon className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      {/* Review Content */}
      <div className="mt-4 text-gray-700">
        <p>{review.comment}</p>
      </div>

      {/* Review Images */}
      {review.images && review.images.length > 0 && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {review.images.map((image, index) => (
            <button
              key={index}
              className="relative h-20 w-20 rounded-lg overflow-hidden border border-gray-200 hover:border-gray-400 transition-colors"
              aria-label={`View image ${index + 1}`}
            >
              <img
                src={image}
                alt={`Review image ${index + 1}`}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Helpful Votes */}
      <div className="mt-4 flex items-center gap-4 text-sm">
        <span className="text-gray-500">Was this helpful?</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleVote('helpful')}
            className={`flex items-center gap-1 px-3 py-1 rounded-md border transition-colors ${
              review.userVote === 'helpful'
                ? 'bg-green-50 border-green-500 text-green-700'
                : 'border-gray-300 hover:bg-gray-50'
            }`}
            aria-label={`Mark as helpful (${review.helpful} found this helpful)`}
            aria-pressed={review.userVote === 'helpful'}
          >
            <HandThumbUpIcon className="h-4 w-4" aria-hidden="true" />
            <span>{review.helpful}</span>
          </button>

          <button
            onClick={() => handleVote('not-helpful')}
            className={`flex items-center gap-1 px-3 py-1 rounded-md border transition-colors ${
              review.userVote === 'not-helpful'
                ? 'bg-red-50 border-red-500 text-red-700'
                : 'border-gray-300 hover:bg-gray-50'
            }`}
            aria-label={`Mark as not helpful (${review.notHelpful} found this not helpful)`}
            aria-pressed={review.userVote === 'not-helpful'}
          >
            <HandThumbDownIcon className="h-4 w-4" aria-hidden="true" />
            <span>{review.notHelpful}</span>
          </button>
        </div>
      </div>

      {/* Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900">Report Review</h3>

            <div className="mt-4 space-y-4">
              <div>
                <label htmlFor="report-reason" className="block text-sm font-medium text-gray-700">
                  Reason for reporting
                </label>
                <select
                  id="report-reason"
                  value={reportReason}
                  onChange={(e) => setReportReason(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
                  required
                >
                  <option value="">Select a reason</option>
                  <option value="inappropriate">Inappropriate content</option>
                  <option value="spam">Spam or fake review</option>
                  <option value="offensive">Offensive language</option>
                  <option value="misleading">Misleading information</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label htmlFor="report-details" className="block text-sm font-medium text-gray-700">
                  Additional details (optional)
                </label>
                <textarea
                  id="report-details"
                  value={reportDetails}
                  onChange={(e) => setReportDetails(e.target.value)}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <AccessibleButton
                onClick={() => setShowReportModal(false)}
                variant="secondary"
              >
                Cancel
              </AccessibleButton>
              <AccessibleButton
                onClick={handleReport}
                variant="danger"
                disabled={!reportReason}
              >
                Submit Report
              </AccessibleButton>
            </div>
          </div>
        </div>
      )}
    </article>
  );
};

export default ReviewItem;