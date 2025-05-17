import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import PrivateRoute from './PrivateRoute';
import AuthRoute from './AuthRoute';

// Layouts
import MainLayout from '../layouts/MainLayout';
import AuthLayout from '../layouts/AuthLayout';

// Auth Pages
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';
import ForgotPasswordPage from '../pages/auth/ForgotPasswordPage';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage';

// Dashboard Pages
import DashboardPage from '../pages/dashboard/DashboardPage';
import AdminDashboard from '../pages/dashboard/AdminDashboard';
import InstructorDashboard from '../pages/dashboard/InstructorDashboard';
import StudentDashboard from '../pages/dashboard/StudentDashboard';

// Course Pages
import CourseListPage from '../pages/courses/CourseListPage';
import CourseDetailPage from '../pages/courses/CourseDetailPage';
import CourseFormPage from '../pages/courses/CourseFormPage';

// Enrollment Pages
import EnrollmentListPage from '../pages/enrollments/EnrollmentListPage';
import EnrollmentDetailPage from '../pages/enrollments/EnrollmentDetailPage';

// Payment Pages
import PaymentPage from '../pages/payments/PaymentPage';
import PaymentHistoryPage from '../pages/payments/PaymentHistoryPage';

// Document Pages
import DocumentListPage from '../pages/documents/DocumentListPage';
import DocumentUploadPage from '../pages/documents/DocumentUploadPage';

// Schedule Pages
import ScheduleManagementPage from '../pages/schedules/ScheduleManagementPage';

// Notification Pages
import NotificationListPage from '../pages/notifications/NotificationListPage';

// Profile Pages
import ProfilePage from '../pages/profile/ProfilePage';
import EditProfilePage from '../pages/profile/EditProfilePage';

// Misc Pages
import NotFoundPage from '../pages/NotFoundPage';

const AppRoutes: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Auth Routes */}
      <Route element={<AuthRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Route>
      </Route>

      {/* Private Routes */}
      <Route element={<PrivateRoute />}>
        <Route element={<MainLayout />}>
          {/* Dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          
          {/* Role-based dashboards */}
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/instructor" element={<InstructorDashboard />} />
          <Route path="/student" element={<StudentDashboard />} />

          {/* Courses */}
          <Route path="/courses" element={<CourseListPage />} />
          <Route path="/courses/:id" element={<CourseDetailPage />} />
          <Route path="/courses/new" element={<CourseFormPage />} />
          <Route path="/courses/:id/edit" element={<CourseFormPage />} />

          {/* Enrollments */}
          <Route path="/enrollments" element={<EnrollmentListPage />} />
          <Route path="/enrollments/:id" element={<EnrollmentDetailPage />} />

          {/* Payments */}
          <Route path="/payments/:enrollmentId" element={<PaymentPage />} />
          <Route path="/payments" element={<PaymentHistoryPage />} />

          {/* Documents */}
          <Route path="/documents" element={<DocumentListPage />} />
          <Route path="/documents/upload" element={<DocumentUploadPage />} />

          {/* Schedules */}
          <Route path="/schedules" element={<ScheduleManagementPage />} />

          {/* Notifications */}
          <Route path="/notifications" element={<NotificationListPage />} />

          {/* Profile */}
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/profile/edit" element={<EditProfilePage />} />
        </Route>
      </Route>

      {/* 404 Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default AppRoutes;