import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-hot-toast';
import notificationsApi from '../api/notifications';
import { Notification } from '../types/notification.types';
import { useAuth } from '../hooks/useAuth';

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: number) => Promise<void>;
  notifyUser: (title: string, message: string) => void;
}

export const NotificationContext = createContext<NotificationContextType>({
  notifications: [],
  unreadCount: 0,
  loading: false,
  fetchNotifications: async () => {},
  markAsRead: async () => {},
  markAllAsRead: async () => {},
  deleteNotification: async () => {},
  notifyUser: () => {},
});

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const { isAuthenticated } = useAuth();

  const fetchNotifications = async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    try {
      const data = await notificationsApi.getNotifications();
      setNotifications(data);
      
      // Get unread count
      const { count } = await notificationsApi.getUnreadCount();
      setUnreadCount(count);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      
      // Update local state
      setNotifications(
        notifications.map(notification =>
          notification.id === id ? { ...notification, is_read: true } : notification
        )
      );
      
      // Update unread count
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      
      // Update local state
      setNotifications(
        notifications.map(notification => ({ ...notification, is_read: true }))
      );
      
      // Update unread count
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const deleteNotification = async (id: number) => {
    try {
      await notificationsApi.deleteNotification(id);
      
      // Update local state
      const deletedNotification = notifications.find(n => n.id === id);
      setNotifications(notifications.filter(notification => notification.id !== id));
      
      // Update unread count if the deleted notification was unread
      if (deletedNotification && !deletedNotification.is_read) {
        setUnreadCount(prevCount => Math.max(0, prevCount - 1));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const notifyUser = (title: string, message: string) => {
    toast.custom((t) => (
      <div
        className={`${
          t.visible ? 'animate-enter' : 'animate-leave'
        } max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex flex-col ring-1 ring-black ring-opacity-5`}
      >
        <div className="p-4">
          <div className="flex items-start">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{title}</p>
              <p className="mt-1 text-sm text-gray-500">{message}</p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                onClick={() => toast.dismiss(t.id)}
                className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <span className="sr-only">Close</span>
                <svg
                  className="h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    ));
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
      
      // Poll for new notifications every minute
      const interval = setInterval(fetchNotifications, 60000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        notifyUser,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};