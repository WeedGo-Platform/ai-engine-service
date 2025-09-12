import React from 'react';

interface NotificationProps {
  show: boolean;
  message: string;
}

const Notification: React.FC<NotificationProps> = ({ show, message }) => {
  if (!show) return null;

  return (
    <div className="fixed top-20 right-4 z-50 animate-float">
      <div className="bg-gradient-to-r from-purple-600 to-purple-500 text-white px-6 py-3 rounded-xl shadow-2xl font-medium flex items-center gap-2">
        <span className="text-pink-300">✨</span>
        {message}
      </div>
    </div>
  );
};

export default Notification;