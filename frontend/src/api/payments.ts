import apiClient from './client';
import { Payment, PaymentCreate, PaymentWithEnrollment } from '../types/payment.types';

export interface PaymentFilters {
  skip?: number;
  limit?: number;
  status?: string;
  payment_method?: string;
  enrollment_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface PaymentStats {
  total: number;
  totalAmount: number;
  completed: number;
  pending: number;
  failed: number;
}

export interface PaymentIntentResponse {
  clientSecret: string;
  payment_id: number;
}

const paymentsApi = {
  getPayments: async (filters?: PaymentFilters): Promise<Payment[]> => {
    return apiClient.get<Payment[]>('/payments', { params: filters });
  },
  
  getPayment: async (id: number): Promise<PaymentWithEnrollment> => {
    return apiClient.get<PaymentWithEnrollment>(`/payments/${id}`);
  },
  
  createPayment: async (paymentData: PaymentCreate): Promise<Payment> => {
    return apiClient.post<Payment>('/payments', paymentData);
  },
  
  getEnrollmentPayments: async (enrollmentId: number): Promise<Payment[]> => {
    return apiClient.get<Payment[]>('/payments', { 
      params: { enrollment_id: enrollmentId } 
    });
  },
  
  createPaymentIntent: async (paymentId: number): Promise<PaymentIntentResponse> => {
    return apiClient.post<PaymentIntentResponse>(`/payments/${paymentId}/intent`);
  },
  
  refundPayment: async (paymentId: number): Promise<Payment> => {
    return apiClient.post<Payment>(`/payments/${paymentId}/refund`);
  },
  
  getPaymentStats: async (): Promise<PaymentStats> => {
    return apiClient.get<PaymentStats>('/payments/stats');
  },
};

export default paymentsApi;