import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import AppRoutes from './routes';
import './index.css';

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <NotificationProvider>
          <Toaster position="top-right" />
          <AppRoutes />
        </NotificationProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;