import { User } from './auth.types';

export enum NotificationType {
  ENROLLMENT = "enrollment",
  PAYMENT = "payment",
  COURSE = "course",
  SYSTEM = "system",
  EMAIL = "email",
  SMS = "sms"
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  notification_type: NotificationType;
  entity_id?: number;
  entity_type?: string;
  updated_at: string;
}

export interface NotificationWithUser extends Notification {
  user: User;
}

export interface NotificationCreate {
  user_id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  entity_id?: number;
  entity_type?: string;
  is_read?: boolean;
}

export interface NotificationUpdate {
  is_read?: boolean;
  title?: string;
  message?: string;
}