import React from 'react';
import toast from 'react-hot-toast';
import { CheckCircle, XCircle } from 'lucide-react';

interface ConfirmToastProps {
  message: string;
  onConfirm: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  toastId: string;
}

const ConfirmToastContent: React.FC<ConfirmToastProps> = ({
  message,
  onConfirm,
  onCancel,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  toastId,
}) => {
  const handleConfirm = () => {
    toast.dismiss(toastId);
    onConfirm();
  };

  const handleCancel = () => {
    toast.dismiss(toastId);
    if (onCancel) onCancel();
  };

  return (
    <div className="flex flex-col gap-3 min-w-[300px]">
      <p className="text-gray-800 dark:text-gray-200 font-medium">{message}</p>
      <div className="flex gap-2 justify-end">
        <button
          onClick={handleCancel}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
        >
          <XCircle className="w-4 h-4" />
          {cancelText}
        </button>
        <button
          onClick={handleConfirm}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <CheckCircle className="w-4 h-4" />
          {confirmText}
        </button>
      </div>
    </div>
  );
};

/**
 * Display a confirmation toast dialog
 * @param message - The confirmation message to display
 * @param onConfirm - Callback function when user confirms
 * @param onCancel - Optional callback when user cancels
 * @param confirmText - Text for confirm button (default: "Confirm")
 * @param cancelText - Text for cancel button (default: "Cancel")
 * @returns Promise that resolves to true if confirmed, false if cancelled
 */
export const confirmToast = (
  message: string,
  onConfirm: () => void,
  onCancel?: () => void,
  confirmText?: string,
  cancelText?: string
): void => {
  const toastId = `confirm-${Date.now()}`;

  toast(
    (t) => (
      <ConfirmToastContent
        message={message}
        onConfirm={onConfirm}
        onCancel={onCancel}
        confirmText={confirmText}
        cancelText={cancelText}
        toastId={t.id}
      />
    ),
    {
      id: toastId,
      duration: Infinity,
      position: 'top-center',
      style: {
        background: 'white',
        padding: '16px',
        borderRadius: '12px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
      },
    }
  );
};

/**
 * Async version that returns a promise
 * @param message - The confirmation message to display
 * @param confirmText - Text for confirm button
 * @param cancelText - Text for cancel button
 * @returns Promise<boolean> - resolves to true if confirmed, false if cancelled
 */
export const confirmToastAsync = (
  message: string,
  confirmText: string = 'Confirm',
  cancelText: string = 'Cancel'
): Promise<boolean> => {
  return new Promise((resolve) => {
    const toastId = `confirm-${Date.now()}`;

    const handleConfirm = () => {
      toast.dismiss(toastId);
      resolve(true);
    };

    const handleCancel = () => {
      toast.dismiss(toastId);
      resolve(false);
    };

    toast(
      (t) => (
        <ConfirmToastContent
          message={message}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          confirmText={confirmText}
          cancelText={cancelText}
          toastId={t.id}
        />
      ),
      {
        id: toastId,
        duration: Infinity,
        position: 'top-center',
        style: {
          background: 'white',
          padding: '16px',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
        },
      }
    );
  });
};

export default ConfirmToastContent;
