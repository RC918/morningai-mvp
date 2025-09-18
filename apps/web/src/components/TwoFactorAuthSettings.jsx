import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '../hooks/useAuth'; // 假設有一個 useAuth hook 來獲取用戶信息和 token

const TwoFactorAuthSettings = () => {
  const { user, token } = useAuth(); // 從 Auth Context 獲取用戶和 token
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(user?.two_factor_enabled || false);
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "https://morningai-mvp.onrender.com/api";

  const fetchTwoFactorStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/auth/2fa/status`, {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      const data = await response.json();
      if (response.ok) {
        setTwoFactorEnabled(data.two_factor_enabled);
      } else {
        setMessage(data.message || "獲取 2FA 狀態失敗");
      }
    } catch (error) {
      console.error("Error fetching 2FA status:", error);
      setMessage("獲取 2FA 狀態時發生錯誤");
    }
  }, [token, API_URL]);

  useEffect(() => {
    if (token) {
      fetchTwoFactorStatus();
    }
  }, [token, fetchTwoFactorStatus]);

  const handleSetup2FA = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/2fa/setup`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      if (response.ok) {
        setQrCode(data.qr_code);
        setSecret(data.secret);
        setMessage("請掃描 QR 碼並輸入 OTP 進行驗證");
      } else {
        setMessage(data.message || "2FA 設置失敗");
      }
    } catch (error) {
      console.error("Error setting up 2FA:", error);
      setMessage("設置 2FA 時發生錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleEnable2FA = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/2fa/enable`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ otp }),
      });
      const data = await response.json();
      if (response.ok) {
        setTwoFactorEnabled(true);
        setQrCode("");
        setSecret("");
        setOtp("");
        setMessage("2FA 已成功啟用");
      } else {
        setMessage(data.message || "2FA 啟用失敗");
      }
    } catch (error) {
      console.error("Error enabling 2FA:", error);
      setMessage("啟用 2FA 時發生錯誤");
    }
  };

  const handleDisable2FA = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/2fa/disable`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ otp }),
      });
      const data = await response.json();
      if (response.ok) {
        setTwoFactorEnabled(false);
        setQrCode("");
        setSecret("");
        setOtp("");
        setMessage("2FA 已成功停用");
      } else {
        setMessage(data.message || "2FA 停用失敗");
      }
    } catch (error) {
      console.error("Error disabling 2FA:", error);
      setMessage("停用 2FA 時發生錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>雙重認證 (2FA) 設定</CardTitle>
        <CardDescription>保護您的帳戶，啟用雙重認證。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {message && <p className="text-sm text-red-500">{message}</p>}

        {twoFactorEnabled ? (
          <div className="space-y-2">
            <p className="text-green-600">雙重認證已啟用。</p>
            <Label htmlFor="otp">輸入 OTP 以停用 2FA</Label>
            <Input
              id="otp"
              type="text"
              placeholder="輸入 OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              disabled={loading}
            />
            <Button onClick={handleDisable2FA} disabled={loading} className="w-full">
              {loading ? '停用中...' : '停用 2FA'}
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {!qrCode ? (
              <Button onClick={handleSetup2FA} disabled={loading} className="w-full">
                {loading ? '設置中...' : '設置 2FA'}
              </Button>
            ) : (
              <div className="space-y-4">
                <p>請使用您的認證應用程式掃描以下 QR 碼，或手動輸入密鑰：</p>
                <div className="flex justify-center">
                  <img src={qrCode} alt="QR Code" className="w-48 h-48 border p-2" />
                </div>
                <p className="text-sm text-gray-600 break-all">密鑰: {secret}</p>
                <Label htmlFor="otp">輸入 OTP 以啟用 2FA</Label>
                <Input
                  id="otp"
                  type="text"
                  placeholder="輸入 OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  disabled={loading}
                />
                <Button onClick={handleEnable2FA} disabled={loading} className="w-full">
                  {loading ? '啟用中...' : '啟用 2FA'}
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TwoFactorAuthSettings;

