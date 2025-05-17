import apiClient from './client';
import { Document, DocumentCreate, DocumentUpdate, DocumentWithUser } from '../types/document.types';

interface DocumentFilters {
  skip?: number;
  limit?: number;
  user_id?: number;
  document_type?: string;
  search?: string;
}

const documentsApi = {
  getDocuments: async (filters?: DocumentFilters): Promise<Document[]> => {
    return apiClient.get<Document[]>('/documents', { params: filters });
  },
  
  getDocument: async (id: number): Promise<DocumentWithUser> => {
    return apiClient.get<DocumentWithUser>(`/documents/${id}`);
  },
  
  uploadDocument: async (
    file: File, 
    documentType: string, 
    description?: string
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (description) {
      formData.append('description', description);
    }
    
    return apiClient.post<Document>('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  updateDocument: async (id: number, documentData: DocumentUpdate): Promise<Document> => {
    return apiClient.put<Document>(`/documents/${id}`, documentData);
  },
  
  deleteDocument: async (id: number): Promise<Document> => {
    return apiClient.delete<Document>(`/documents/${id}`);
  },
  
  downloadDocument: async (id: number): Promise<Blob> => {
    return apiClient.get<Blob>(`/documents/${id}/download`, {
      responseType: 'blob',
    });
  },
  
  getUserDocuments: async (userId?: number): Promise<Document[]> => {
    return apiClient.get<Document[]>('/documents', { 
      params: { user_id: userId } 
    });
  },
};

export default documentsApi;