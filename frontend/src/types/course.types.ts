import { User } from './auth.types';
import { Schedule } from './schedule.types';

export interface Course {
  id: number;
  title: string;
  description?: string;
  instructor_id?: number;
  duration: number;
  price: number;
  capacity: number;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CourseWithDetails extends Course {
  instructor?: User;
  schedules: Schedule[];
  enrollment_count: number;
}

export interface CourseCreate {
  title: string;
  description?: string;
  instructor_id?: number;
  duration: number;
  price: number;
  capacity: number;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  image_url?: string;
}

export interface CourseUpdate {
  title?: string;
  description?: string;
  instructor_id?: number;
  duration?: number;
  price?: number;
  capacity?: number;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  image_url?: string;
}