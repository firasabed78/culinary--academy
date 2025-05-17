import apiClient from './client';
import { Course, CourseCreate, CourseUpdate, CourseWithDetails } from '../types/course.types';

export interface CourseFilters {
  skip?: number;
  limit?: number;
  title?: string;
  instructor_id?: number;
  is_active?: boolean;
  min_price?: number;
  max_price?: number;
  start_date_after?: string;
  end_date_before?: string;
}

export interface CourseStats {
  total: number;
  active: number;
  upcoming: number;
  completed: number;
}

const coursesApi = {
  getCourses: async (filters?: CourseFilters): Promise<Course[]> => {
    return apiClient.get<Course[]>('/courses', { params: filters });
  },
  
  getCourse: async (id: number): Promise<CourseWithDetails> => {
    return apiClient.get<CourseWithDetails>(`/courses/${id}`);
  },
  
  createCourse: async (courseData: CourseCreate): Promise<Course> => {
    return apiClient.post<Course>('/courses', courseData);
  },
  
  updateCourse: async (id: number, courseData: CourseUpdate): Promise<Course> => {
    return apiClient.put<Course>(`/courses/${id}`, courseData);
  },
  
  deleteCourse: async (id: number): Promise<Course> => {
    return apiClient.delete<Course>(`/courses/${id}`);
  },
  
  getInstructorCourses: async (instructorId: number): Promise<Course[]> => {
    return apiClient.get<Course[]>('/courses', { 
      params: { instructor_id: instructorId } 
    });
  },
  
  getAvailableCourses: async (): Promise<Course[]> => {
    return apiClient.get<Course[]>('/courses/available');
  },
  
  searchCourses: async (searchTerm: string): Promise<Course[]> => {
    return apiClient.get<Course[]>('/courses', { 
      params: { title: searchTerm } 
    });
  },
  
  getCourseStats: async (): Promise<CourseStats> => {
    return apiClient.get<CourseStats>('/courses/stats');
  },
};

export default coursesApi;