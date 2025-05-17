import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AuthRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    // Redirect to the page they were trying to access before being sent to login,
    // or to the dashboard if they came directly to the login page
    return <Navigate to={from} replace />;
  }

  return <Outlet />;
};

export default AuthRoute;