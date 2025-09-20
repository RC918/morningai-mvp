import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/sonner';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import TwoFactorAuthSettings from './components/TwoFactorAuthSettings';
import UserManagement from './components/UserManagement';
import StrategyManagement from './components/StrategyManagement';
import DecisionApproval from './components/DecisionApproval';
import HistoryAnalysis from './components/HistoryAnalysis';
import CostAnalysis from './components/CostAnalysis';
import SystemSettings from './components/SystemSettings';

import LoginPage from '@/components/LoginPage';
import RegisterPage from '@/components/RegisterPage';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { queryClient } from './lib/queryClient';
import './App.css';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  return (
    <div className="flex h-screen">
      <Sidebar user={user} onLogout={logout} />
      <div className="flex-1 overflow-auto">
        <Dashboard />
      </div>
    </div>
  );
};

const LayoutWithSidebar = ({ component: PageComponent }) => {
  const { user, logout } = useAuth();
  return (
    <div className="flex h-screen">
      <Sidebar user={user} onLogout={logout} />
      <div className="flex-1 overflow-auto">
        <PageComponent />
      </div>
    </div>
  );
};

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
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            />
            <Route 
              path="/settings/2fa" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={TwoFactorAuthSettings} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/admin/users" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={UserManagement} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/strategy" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={StrategyManagement} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/decisions" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={DecisionApproval} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/history" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={HistoryAnalysis} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/cost" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={CostAnalysis} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/settings" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={SystemSettings} />
                </PrivateRoute>
              }
            />
            <Route 
              path="/two-factor" 
              element={
                <PrivateRoute>
                  <LayoutWithSidebar component={TwoFactorAuthSettings} />
                </PrivateRoute>
              }
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


