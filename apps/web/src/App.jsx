import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/sonner';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import TwoFactorAuthSettings from '@/components/TwoFactorAuthSettings';
import UserManagement from '@/components/UserManagement';

import LoginPage from '@/components/LoginPage';
import RegisterPage from '@/components/RegisterPage';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { queryClient } from './lib/queryClient';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route 
              path="/dashboard" 
              element={<PrivateRoute><Sidebar /><Dashboard /></PrivateRoute>}
            />
            <Route 
              path="/settings/2fa" 
              element={<PrivateRoute><Sidebar /><TwoFactorAuthSettings /></PrivateRoute>}
            />
            <Route 
              path="/admin/users" 
              element={<PrivateRoute><Sidebar /><UserManagement /></PrivateRoute>}
            />
            <Route 
              path="/" 
              element={<Navigate to="/login" replace />}
            />
          </Routes>
          <Toaster />
        </AuthProvider>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;


