import apiClient from './client';
import { Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentWithDetails } from '../types/enrollment.types';

export interface EnrollmentFilters {
  skip?: number;
  limit?: number;
  status?: string;
  payment_status?: string;
  student_id?: number;
  course_id?: number;
}

export interface EnrollmentStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  completed: number;
}

const enrollmentsApi = {
  getEnrollments: async (filters?: EnrollmentFilters): Promise<Enrollment[]> => {
    return apiClient.get<Enrollment[]>('/enrollments', { params: filters });
  },
  
  getEnrollment: async (id: number): Promise<EnrollmentWithDetails> => {
    return apiClient.get<EnrollmentWithDetails>(`/enrollments/${id}`);
  },
  
  createEnrollment: async (enrollmentData: EnrollmentCreate): Promise<Enrollment> => {
    return apiClient.post<Enrollment>('/enrollments', enrollmentData);
  },
  
  updateEnrollment: async (id: number, enrollmentData: EnrollmentUpdate): Promise<Enrollment> => {
    return apiClient.put<Enrollment>(`/enrollments/${id}`, enrollmentData);
  },
  
  getStudentEnrollments: async (studentId: number): Promise<Enrollment[]> => {
    return apiClient.get<Enrollment[]>('/enrollments', { 
      params: { student_id: studentId } 
    });
  },
  
  getCourseEnrollments: async (courseId: number): Promise<Enrollment[]> => {
    return apiClient.get<Enrollment[]>('/enrollments', { 
      params: { course_id: courseId } 
    });
  },
  
  getEnrollmentStats: async (): Promise<EnrollmentStats> => {
    return apiClient.get<EnrollmentStats>('/enrollments/stats');
  },
};

export default enrollmentsApi;