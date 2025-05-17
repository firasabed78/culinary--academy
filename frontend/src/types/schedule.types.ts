import { Course } from './course.types';

export interface Schedule {
  id: number;
  course_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  location?: string;
  is_recurring: boolean;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScheduleWithCourse extends Schedule {
  course: Course;
}

export interface ScheduleCreate {
  course_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  location?: string;
  is_recurring?: boolean;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
}

export interface ScheduleUpdate {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
  location?: string;
  is_recurring?: boolean;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
}