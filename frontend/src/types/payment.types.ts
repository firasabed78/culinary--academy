import { Enrollment } from './enrollment.types';

export enum PaymentMethod {
  CREDIT_CARD = "credit_card",
  DEBIT_CARD = "debit_card",
  PAYPAL = "paypal",
  BANK_TRANSFER = "bank_transfer",
  OTHER = "other"
}

export enum PaymentStatus {
  PENDING = "pending",
  COMPLETED = "completed",
  FAILED = "failed",
  REFUNDED = "refunded"
}

export interface Payment {
  id: number;
  enrollment_id: number;
  amount: number;
  payment_date: string;
  payment_method?: PaymentMethod;
  transaction_id?: string;
  status: PaymentStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentWithEnrollment extends Payment {
  enrollment: Enrollment;
}

export interface PaymentCreate {
  enrollment_id: number;
  amount: number;
  payment_method?: PaymentMethod;
  transaction_id?: string;
  notes?: string;
  status?: PaymentStatus;
}

export interface PaymentUpdate {
  payment_method?: PaymentMethod;
  transaction_id?: string;
  status?: PaymentStatus;
  notes?: string;
}