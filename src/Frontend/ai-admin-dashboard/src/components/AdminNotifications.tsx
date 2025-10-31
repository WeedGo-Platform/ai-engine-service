/**
 * AdminNotifications Component
 * Real-time WebSocket notifications for admin dashboard
 * Displays new account reviews and review updates
 */

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';
import { BellIcon, CheckCircleIcon, XCircleIcon, UserPlusIcon } from '@heroicons/react/24/outline';
import { getWebSocketUrl } from '../utils/websocket';

interface Notification {
  id: string;
  type: string;
  message: string;
  data: any;
  timestamp: string;
  read: boolean;
}

interface AdminNotificationsProps {
  onNewReview?: (tenantId: string) => void;
  onReviewUpdate?: (tenantId: string, action: string) => void;
}

export const AdminNotifications: React.FC<AdminNotificationsProps> = ({
  onNewReview,
  onReviewUpdate,
}) => {
  const { getAuthHeader } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Extract token from auth header
  const getToken = () => {
    const authHeader = getAuthHeader();
    const token = authHeader?.Authorization?.replace('Bearer ', '');
    return token || '';
  };

  // WebSocket connection
  const { isConnected, lastMessage } = useWebSocket({
    url: `${getWebSocketUrl('NOTIFICATIONS')}?token=${getToken()}`,
    onMessage: (message: WebSocketMessage) => {
      handleWebSocketMessage(message);
    },
    onOpen: () => {
      console.log('[AdminNotifications] WebSocket connected');
    },
    onClose: () => {
      console.log('[AdminNotifications] WebSocket disconnected');
    },
    onError: (error) => {
      console.error('[AdminNotifications] WebSocket error:', error);
    },
    autoReconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  });

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    // Skip heartbeat messages
    if (message.type === 'heartbeat' || message.type === 'system_message') {
      return;
    }

    // Create notification
    const notification: Notification = {
      id: `${Date.now()}-${Math.random()}`,
      type: message.type,
      message: message.message || 'New notification',
      data: message,
      timestamp: message.timestamp || new Date().toISOString(),
      read: false,
    };

    // Add to notifications list
    setNotifications((prev) => [notification, ...prev].slice(0, 50)); // Keep last 50
    setUnreadCount((prev) => prev + 1);

    // Show browser notification if supported
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('WeedGo Admin', {
        body: notification.message,
        icon: '/favicon.ico',
      });
    }

    // Trigger callbacks
    if (message.type === 'admin_new_review') {
      onNewReview?.(message.tenant_id);
    } else if (message.type === 'admin_review_update') {
      onReviewUpdate?.(message.tenant_id, message.action);
    }
  };

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const clearNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'admin_new_review':
        return <UserPlusIcon className="h-5 w-5 text-blue-500" />;
      case 'admin_review_update':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  return (
    <div className="relative">
      {/* Bell Icon with Badge */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 rounded-full hover:bg-gray-100 transition-colors"
      >
        <BellIcon className="h-6 w-6" />

        {/* Connection Status Indicator */}
        <span
          className={`absolute top-1 right-1 h-2 w-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />

        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
            <div className="flex gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={clearNotifications}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <BellIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No notifications</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => markAsRead(notification.id)}
                  className={`px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTimestamp(notification.timestamp)}
                      </p>
                    </div>
                    {!notification.read && (
                      <div className="flex-shrink-0">
                        <span className="h-2 w-2 bg-blue-500 rounded-full block" />
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-gray-200 text-center">
            <span className="text-xs text-gray-500">
              {isConnected ? (
                <span className="text-green-600">● Connected</span>
              ) : (
                <span className="text-red-600">● Disconnected</span>
              )}
            </span>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default AdminNotifications;
