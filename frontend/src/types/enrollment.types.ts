import { User } from './auth.types';
import { Course } from './course.types';
import { Payment } from './payment.types';

export enum EnrollmentStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  COMPLETED = "completed"
}

export enum PaymentStatus {
  PENDING = "pending",
  PAID = "paid",
  REFUNDED = "refunded"
}

export interface Enrollment {
  id: number;
  student_id: number;
  course_id: number;
  enrollment_date: string;
  status: EnrollmentStatus;
  payment_status: PaymentStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface EnrollmentWithDetails extends Enrollment {
  student: User;
  course: Course;
  payments: Payment[];
}

export interface EnrollmentCreate {
  student_id: number;
  course_id: number;
  notes?: string;
  status?: EnrollmentStatus;
  payment_status?: PaymentStatus;
}

export interface EnrollmentUpdate {
  status?: EnrollmentStatus;
  payment_status?: PaymentStatus;
  notes?: string;
}