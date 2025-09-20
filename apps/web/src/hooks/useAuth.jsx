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
        // 使用 /profile 端點驗證 token 有效性
        const response = await fetch(`${API_URL}/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          setUser(userData.user);
          setIsAuthenticated(true);
        } else if (response.status === 401) {
          // Token 無效或已被撤銷
          console.log('Token 已失效或被撤銷');
          localStorage.removeItem('auth_token');
          setToken(null);
          setIsAuthenticated(false);
          setUser(null);
        } else {
          // 其他錯誤
          console.error('認證檢查失敗:', response.status);
          localStorage.removeItem('auth_token');
          setToken(null);
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('認證檢查網路錯誤:', error);
        // 網路錯誤時不清除 token，允許離線使用
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    // 設置定期檢查 token 有效性（每 5 分鐘）
    const interval = setInterval(() => {
      if (token && isAuthenticated) {
        checkAuth();
      }
    }, 5 * 60 * 1000); // 5 分鐘

    return () => clearInterval(interval);
  }, [token, API_URL, isAuthenticated]);

  const login = async (email, password, otp = null) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/login`, {
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

  const logout = async () => {
    try {
      // 調用後端登出 API 將 token 加入黑名單
      if (token) {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      console.error('登出 API 調用失敗:', error);
      // 即使 API 調用失敗，仍然清除本地狀態
    } finally {
      // 清除本地狀態
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      navigate('/login');
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);


