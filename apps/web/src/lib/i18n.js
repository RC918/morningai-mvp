import { createContext, useContext, useState } from 'react';

// 支援的語言列表
export const SUPPORTED_LANGUAGES = {
  'zh-TW': '繁體中文',
  'zh-CN': '简体中文',
  'en': 'English',
  'ja': '日本語',
  'ko': '한국어'
};

// 預設語言
export const DEFAULT_LANGUAGE = 'zh-TW';

// 語言上下文
const I18nContext = createContext();

// 翻譯資源
const translations = {
  'zh-TW': {
    // 通用
    'common.loading': '載入中...',
    'common.error': '錯誤',
    'common.success': '成功',
    'common.cancel': '取消',
    'common.confirm': '確認',
    'common.save': '儲存',
    'common.delete': '刪除',
    'common.edit': '編輯',
    'common.add': '新增',
    'common.search': '搜尋',
    'common.filter': '篩選',
    'common.actions': '操作',
    'common.status': '狀態',
    'common.active': '啟用',
    'common.inactive': '停用',
    'common.yes': '是',
    'common.no': '否',
    
    // 認證
    'auth.login': '登入',
    'auth.logout': '登出',
    'auth.register': '註冊',
    'auth.email': '電子郵件',
    'auth.password': '密碼',
    'auth.confirmPassword': '確認密碼',
    'auth.username': '使用者名稱',
    'auth.forgotPassword': '忘記密碼？',
    'auth.loginSuccess': '登入成功',
    'auth.loginFailed': '登入失敗',
    'auth.registerSuccess': '註冊成功',
    'auth.registerFailed': '註冊失敗',
    'auth.invalidCredentials': '帳號或密碼錯誤',
    'auth.passwordMismatch': '密碼確認不符',
    'auth.emailRequired': '請輸入電子郵件',
    'auth.passwordRequired': '請輸入密碼',
    'auth.usernameRequired': '請輸入使用者名稱',
    
    // 2FA
    'twofa.title': '雙重認證',
    'twofa.setup': '設定 2FA',
    'twofa.enable': '啟用 2FA',
    'twofa.disable': '停用 2FA',
    'twofa.code': '驗證碼',
    'twofa.qrCode': 'QR 碼',
    'twofa.secret': '密鑰',
    'twofa.enabled': '已啟用',
    'twofa.disabled': '已停用',
    'twofa.enterCode': '請輸入 6 位數驗證碼',
    'twofa.invalidCode': '驗證碼錯誤',
    
    // 儀表板
    'dashboard.title': '儀表板',
    'dashboard.welcome': '歡迎回來',
    'dashboard.overview': '總覽',
    'dashboard.statistics': '統計資料',
    'dashboard.recentActivity': '最近活動',
    'dashboard.systemStatus': '系統狀態',
    'dashboard.performance': '效能',
    'dashboard.users': '使用者',
    'dashboard.storage': '儲存空間',
    
    // 使用者管理
    'users.title': '使用者管理',
    'users.list': '使用者列表',
    'users.add': '新增使用者',
    'users.edit': '編輯使用者',
    'users.delete': '刪除使用者',
    'users.role': '角色',
    'users.admin': '管理員',
    'users.user': '使用者',
    'users.member': '成員',
    'users.owner': '擁有者',
    'users.createdAt': '建立時間',
    'users.lastLogin': '最後登入',
    'users.totalUsers': '總使用者數',
    'users.activeUsers': '活躍使用者',
    
    // 租戶管理
    'tenant.title': '租戶管理',
    'tenant.name': '租戶名稱',
    'tenant.slug': 'Slug',
    'tenant.domain': '自訂網域',
    'tenant.description': '描述',
    'tenant.plan': '方案',
    'tenant.members': '成員',
    'tenant.invite': '邀請成員',
    'tenant.settings': '設定',
    'tenant.usage': '使用量',
    'tenant.billing': '帳單',
    'tenant.free': '免費版',
    'tenant.basic': '基本版',
    'tenant.premium': '進階版',
    'tenant.enterprise': '企業版',
    
    // 設定
    'settings.title': '設定',
    'settings.profile': '個人資料',
    'settings.security': '安全性',
    'settings.notifications': '通知',
    'settings.language': '語言',
    'settings.theme': '主題',
    'settings.privacy': '隱私',
    
    // 錯誤訊息
    'error.notFound': '找不到頁面',
    'error.unauthorized': '未授權存取',
    'error.forbidden': '權限不足',
    'error.serverError': '伺服器錯誤',
    'error.networkError': '網路錯誤',
    'error.unknownError': '未知錯誤',
    
    // 成功訊息
    'success.saved': '儲存成功',
    'success.deleted': '刪除成功',
    'success.updated': '更新成功',
    'success.created': '建立成功',
    'success.sent': '發送成功',
  },
  
  'en': {
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.save': 'Save',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.add': 'Add',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.actions': 'Actions',
    'common.status': 'Status',
    'common.active': 'Active',
    'common.inactive': 'Inactive',
    'common.yes': 'Yes',
    'common.no': 'No',
    
    // Authentication
    'auth.login': 'Login',
    'auth.logout': 'Logout',
    'auth.register': 'Register',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.confirmPassword': 'Confirm Password',
    'auth.username': 'Username',
    'auth.forgotPassword': 'Forgot Password?',
    'auth.loginSuccess': 'Login successful',
    'auth.loginFailed': 'Login failed',
    'auth.registerSuccess': 'Registration successful',
    'auth.registerFailed': 'Registration failed',
    'auth.invalidCredentials': 'Invalid credentials',
    'auth.passwordMismatch': 'Passwords do not match',
    'auth.emailRequired': 'Email is required',
    'auth.passwordRequired': 'Password is required',
    'auth.usernameRequired': 'Username is required',
    
    // 2FA
    'twofa.title': 'Two-Factor Authentication',
    'twofa.setup': 'Setup 2FA',
    'twofa.enable': 'Enable 2FA',
    'twofa.disable': 'Disable 2FA',
    'twofa.code': 'Verification Code',
    'twofa.qrCode': 'QR Code',
    'twofa.secret': 'Secret Key',
    'twofa.enabled': 'Enabled',
    'twofa.disabled': 'Disabled',
    'twofa.enterCode': 'Enter 6-digit code',
    'twofa.invalidCode': 'Invalid code',
    
    // Dashboard
    'dashboard.title': 'Dashboard',
    'dashboard.welcome': 'Welcome back',
    'dashboard.overview': 'Overview',
    'dashboard.statistics': 'Statistics',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.systemStatus': 'System Status',
    'dashboard.performance': 'Performance',
    'dashboard.users': 'Users',
    'dashboard.storage': 'Storage',
    
    // User Management
    'users.title': 'User Management',
    'users.list': 'User List',
    'users.add': 'Add User',
    'users.edit': 'Edit User',
    'users.delete': 'Delete User',
    'users.role': 'Role',
    'users.admin': 'Admin',
    'users.user': 'User',
    'users.member': 'Member',
    'users.owner': 'Owner',
    'users.createdAt': 'Created At',
    'users.lastLogin': 'Last Login',
    'users.totalUsers': 'Total Users',
    'users.activeUsers': 'Active Users',
    
    // Tenant Management
    'tenant.title': 'Tenant Management',
    'tenant.name': 'Tenant Name',
    'tenant.slug': 'Slug',
    'tenant.domain': 'Custom Domain',
    'tenant.description': 'Description',
    'tenant.plan': 'Plan',
    'tenant.members': 'Members',
    'tenant.invite': 'Invite Members',
    'tenant.settings': 'Settings',
    'tenant.usage': 'Usage',
    'tenant.billing': 'Billing',
    'tenant.free': 'Free',
    'tenant.basic': 'Basic',
    'tenant.premium': 'Premium',
    'tenant.enterprise': 'Enterprise',
    
    // Settings
    'settings.title': 'Settings',
    'settings.profile': 'Profile',
    'settings.security': 'Security',
    'settings.notifications': 'Notifications',
    'settings.language': 'Language',
    'settings.theme': 'Theme',
    'settings.privacy': 'Privacy',
    
    // Error Messages
    'error.notFound': 'Page not found',
    'error.unauthorized': 'Unauthorized access',
    'error.forbidden': 'Insufficient permissions',
    'error.serverError': 'Server error',
    'error.networkError': 'Network error',
    'error.unknownError': 'Unknown error',
    
    // Success Messages
    'success.saved': 'Saved successfully',
    'success.deleted': 'Deleted successfully',
    'success.updated': 'Updated successfully',
    'success.created': 'Created successfully',
    'success.sent': 'Sent successfully',
  }
};

// I18n Provider 元件
export const I18nProvider = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState(() => {
    // 從 localStorage 讀取儲存的語言設定
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage && SUPPORTED_LANGUAGES[savedLanguage]) {
      return savedLanguage;
    }
    
    // 嘗試從瀏覽器語言設定推測
    const browserLanguage = navigator.language || navigator.languages[0];
    if (browserLanguage.startsWith('zh')) {
      return browserLanguage.includes('CN') ? 'zh-CN' : 'zh-TW';
    } else if (browserLanguage.startsWith('ja')) {
      return 'ja';
    } else if (browserLanguage.startsWith('ko')) {
      return 'ko';
    } else {
      return 'en';
    }
  });

  const changeLanguage = (language) => {
    if (SUPPORTED_LANGUAGES[language]) {
      setCurrentLanguage(language);
      localStorage.setItem('language', language);
    }
  };

  const t = (key, params = {}) => {
    const translation = translations[currentLanguage]?.[key] || translations[DEFAULT_LANGUAGE]?.[key] || key;
    
    // 簡單的參數替換
    return Object.keys(params).reduce((text, param) => {
      return text.replace(`{{${param}}}`, params[param]);
    }, translation);
  };

  const value = {
    currentLanguage,
    changeLanguage,
    t,
    supportedLanguages: SUPPORTED_LANGUAGES
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

// useI18n Hook
export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// 語言切換元件
export const LanguageSelector = ({ className = '' }) => {
  const { currentLanguage, changeLanguage, supportedLanguages } = useI18n();

  return (
    <select
      value={currentLanguage}
      onChange={(e) => changeLanguage(e.target.value)}
      className={`border rounded px-2 py-1 ${className}`}
    >
      {Object.entries(supportedLanguages).map(([code, name]) => (
        <option key={code} value={code}>
          {name}
        </option>
      ))}
    </select>
  );
};
