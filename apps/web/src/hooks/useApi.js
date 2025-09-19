import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

// Query keys
export const queryKeys = {
  profile: ['profile'],
  users: ['users'],
  user: (id) => ['user', id],
  twoFactorStatus: ['2fa-status'],
  blacklist: ['blacklist'],
  health: ['health'],
};

// Auth hooks
export const useProfile = () => {
  return useQuery({
    queryKey: queryKeys.profile,
    queryFn: apiClient.getProfile.bind(apiClient),
    enabled: !!localStorage.getItem('auth_token'),
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.updateProfile.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      toast.success('個人資料更新成功');
    },
    onError: (error) => {
      toast.error(error.message || '更新失敗');
    },
  });
};

// 2FA hooks
export const use2FAStatus = () => {
  return useQuery({
    queryKey: queryKeys.twoFactorStatus,
    queryFn: apiClient.get2FAStatus.bind(apiClient),
    enabled: !!localStorage.getItem('auth_token'),
  });
};

export const useSetup2FA = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.setup2FA.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.twoFactorStatus });
    },
    onError: (error) => {
      toast.error(error.message || '2FA 設定失敗');
    },
  });
};

export const useEnable2FA = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.enable2FA.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.twoFactorStatus });
      toast.success('2FA 已成功啟用');
    },
    onError: (error) => {
      toast.error(error.message || '2FA 啟用失敗');
    },
  });
};

export const useDisable2FA = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.disable2FA.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.twoFactorStatus });
      toast.success('2FA 已成功停用');
    },
    onError: (error) => {
      toast.error(error.message || '2FA 停用失敗');
    },
  });
};

// Email verification hooks
export const useSendVerificationEmail = () => {
  return useMutation({
    mutationFn: apiClient.sendVerificationEmail.bind(apiClient),
    onSuccess: () => {
      toast.success('驗證郵件已發送');
    },
    onError: (error) => {
      toast.error(error.message || '發送驗證郵件失敗');
    },
  });
};

// Admin hooks
export const useUsers = () => {
  return useQuery({
    queryKey: queryKeys.users,
    queryFn: apiClient.getAllUsers.bind(apiClient),
    enabled: !!localStorage.getItem('auth_token'),
  });
};

export const useUser = (userId) => {
  return useQuery({
    queryKey: queryKeys.user(userId),
    queryFn: () => apiClient.getUserById(userId),
    enabled: !!userId && !!localStorage.getItem('auth_token'),
  });
};

export const useUpdateUserRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, role }) => apiClient.updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users });
      toast.success('使用者角色更新成功');
    },
    onError: (error) => {
      toast.error(error.message || '角色更新失敗');
    },
  });
};

export const useUpdateUserStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, is_active }) => apiClient.updateUserStatus(userId, is_active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users });
      toast.success('使用者狀態更新成功');
    },
    onError: (error) => {
      toast.error(error.message || '狀態更新失敗');
    },
  });
};

export const useBlacklist = () => {
  return useQuery({
    queryKey: queryKeys.blacklist,
    queryFn: apiClient.getBlacklist.bind(apiClient),
    enabled: !!localStorage.getItem('auth_token'),
  });
};

export const useCleanupBlacklist = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.cleanupBlacklist.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blacklist });
      toast.success('黑名單清理完成');
    },
    onError: (error) => {
      toast.error(error.message || '清理失敗');
    },
  });
};

// Logout hooks
export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.logout.bind(apiClient),
    onSuccess: () => {
      localStorage.removeItem('auth_token');
      queryClient.clear();
      toast.success('已成功登出');
    },
    onError: (error) => {
      // Even if logout fails on server, clear local state
      localStorage.removeItem('auth_token');
      queryClient.clear();
      toast.error(error.message || '登出時發生錯誤');
    },
  });
};

export const useLogoutAll = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.logoutAll.bind(apiClient),
    onSuccess: () => {
      localStorage.removeItem('auth_token');
      queryClient.clear();
      toast.success('已從所有設備登出');
    },
    onError: (error) => {
      // Even if logout fails on server, clear local state
      localStorage.removeItem('auth_token');
      queryClient.clear();
      toast.error(error.message || '登出時發生錯誤');
    },
  });
};

// Health check hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: apiClient.healthCheck.bind(apiClient),
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 1,
  });
};
