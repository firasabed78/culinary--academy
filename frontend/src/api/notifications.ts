import apiClient from './client';
import { Notification, NotificationCreate, NotificationWithUser } from '../types/notification.types';

interface NotificationFilters {
  skip?: number;
  limit?: number;
  is_read?: boolean;
  notification_type?: string;
}

interface UnreadCountResponse {
  count: number;
}

interface MarkAllReadResponse {
  count: number;
}

const notificationsApi = {
  getNotifications: async (filters?: NotificationFilters): Promise<Notification[]> => {
    return apiClient.get<Notification[]>('/notifications', { params: filters });
  },
  
  getNotification: async (id: number): Promise<NotificationWithUser> => {
    return apiClient.get<NotificationWithUser>(`/notifications/${id}`);
  },
  
  createNotification: async (
    notificationData: NotificationCreate, 
    sendEmail: boolean = false
  ): Promise<Notification> => {
    return apiClient.post<Notification>('/notifications', notificationData, {
      params: { send_email: sendEmail },
    });
  },
  
  markAsRead: async (id: number): Promise<Notification> => {
    return apiClient.put<Notification>(`/notifications/${id}/read`);
  },
  
  markAllAsRead: async (): Promise<MarkAllReadResponse> => {
    return apiClient.put<MarkAllReadResponse>('/notifications/read-all');
  },
  
  deleteNotification: async (id: number): Promise<Notification> => {
    return apiClient.delete<Notification>(`/notifications/${id}`);
  },
  
  deleteAllNotifications: async (): Promise<MarkAllReadResponse> => {
    return apiClient.delete<MarkAllReadResponse>('/notifications');
  },
  
  getUnreadCount: async (): Promise<UnreadCountResponse> => {
    return apiClient.get<UnreadCountResponse>('/notifications/unread-count');
  },
};

export default notificationsApi;