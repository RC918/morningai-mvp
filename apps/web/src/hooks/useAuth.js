import { useState, useEffect, createContext, useContext } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const API_URL = import.meta.env.VITE_API_URL || 'https://morningai-mvp.onrender.com/api';

  useEffect(() => {
    const checkAuth = async () => {
      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          setUser(userData.user);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('auth_token');
          setToken(null);
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('認證檢查失敗:', error);
        localStorage.removeItem('auth_token');
        setToken(null);
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [token, API_URL]);

  const login = async (email, password, otp = null) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, otp }),
      });
      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('auth_token', data.token);
        setToken(data.token);
        setUser(data.user);
        setIsAuthenticated(true);
        navigate('/dashboard');
        return { success: true, user: data.user };
      } else {
        setIsAuthenticated(false);
        return { success: false, message: data.message, requires_2fa: data.requires_2fa };
      }
    } catch (error) {
      console.error('登入失敗:', error);
      return { success: false, message: '登入時發生錯誤' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);


