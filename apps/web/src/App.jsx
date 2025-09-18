import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import TwoFactorAuthSettings from '@/components/TwoFactorAuthSettings';

import LoginPage from '@/components/LoginPage';
import RegisterPage from '@/components/RegisterPage';
import { AuthProvider, useAuth } from './hooks/useAuth';
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

  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
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
            path="/" 
            element={<Navigate to="/dashboard" />}
          />
        </Routes>
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App;


