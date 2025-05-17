import apiClient from './client';
import { Schedule, ScheduleCreate, ScheduleUpdate, ScheduleWithCourse } from '../types/schedule.types';

interface ScheduleFilters {
  skip?: number;
  limit?: number;
  course_id?: number;
  day_of_week?: number;
  is_active?: boolean;
}

const schedulesApi = {
  getSchedules: async (filters?: ScheduleFilters): Promise<Schedule[]> => {
    return apiClient.get<Schedule[]>('/schedules', { params: filters });
  },
  
  getSchedule: async (id: number): Promise<ScheduleWithCourse> => {
    return apiClient.get<ScheduleWithCourse>(`/schedules/${id}`);
  },
  
  createSchedule: async (scheduleData: ScheduleCreate): Promise<Schedule> => {
    return apiClient.post<Schedule>('/schedules', scheduleData);
  },
  
  updateSchedule: async (id: number, scheduleData: ScheduleUpdate): Promise<Schedule> => {
    return apiClient.put<Schedule>(`/schedules/${id}`, scheduleData);
  },
  
  deleteSchedule: async (id: number): Promise<Schedule> => {
    return apiClient.delete<Schedule>(`/schedules/${id}`);
  },
  
  getCourseSchedules: async (courseId: number): Promise<Schedule[]> => {
    return apiClient.get<Schedule[]>(`/schedules/course/${courseId}`);
  },
  
  getInstructorSchedules: async (instructorId: number): Promise<ScheduleWithCourse[]> => {
    return apiClient.get<ScheduleWithCourse[]>(`/schedules/instructor/${instructorId}`);
  },
  
  getSchedulesByDay: async (dayOfWeek: number): Promise<Schedule[]> => {
    return apiClient.get<Schedule[]>('/schedules', { 
      params: { day_of_week: dayOfWeek } 
    });
  },
};

export default schedulesApi;