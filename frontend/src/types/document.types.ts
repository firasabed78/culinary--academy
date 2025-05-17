import { User } from './auth.types';

export enum DocumentType {
  ID_PROOF = "id_proof",
  CERTIFICATION = "certification",
  RESUME = "resume",
  TRANSCRIPT = "transcript",
  OTHER = "other"
}

export interface Document {
  id: number;
  user_id: number;
  file_name: string;
  file_path: string;
  file_type?: string;
  upload_date: string;
  document_type: DocumentType;
  description?: string;
  file_size?: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithUser extends Document {
  user: User;
}

export interface DocumentCreate {
  user_id: number;
  document_type: DocumentType;
  description?: string;
  file_name: string;
  file_path: string;
  file_type?: string;
  file_size?: number;
}

export interface DocumentUpdate {
  document_type?: DocumentType;
  description?: string;
}