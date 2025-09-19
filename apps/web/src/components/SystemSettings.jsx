import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, Bell, Shield, Database, Cloud, Save } from 'lucide-react';

const SystemSettings = () => {
  const [settings, setSettings] = useState({
    // 通知設定
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
    criticalAlerts: true,
    
    // 系統設定
    autoApprovalThreshold: 85,
    maxConcurrentDecisions: 10,
    decisionTimeout: 300,
    logLevel: 'info',
    
    // 安全設定
    sessionTimeout: 30,
    maxLoginAttempts: 5,
    requireMFA: false,
    passwordExpiry: 90,
    
    // 資料庫設定
    backupFrequency: 'daily',
    retentionPeriod: 30,
    compressionEnabled: true,
    encryptionEnabled: true
  });

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = () => {
    // 這裡會調用 API 保存設定
    console.log('Saving settings:', settings);
    // 顯示成功訊息
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">系統設置</h1>
          <p className="text-gray-600 mt-2">配置系統參數和偏好設定</p>
        </div>
        <Button onClick={handleSave}>
          <Save className="w-4 h-4 mr-2" />
          保存設定
        </Button>
      </div>

      <Tabs defaultValue="notifications" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="notifications">通知設定</TabsTrigger>
          <TabsTrigger value="system">系統設定</TabsTrigger>
          <TabsTrigger value="security">安全設定</TabsTrigger>
          <TabsTrigger value="database">資料庫設定</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                通知設定
              </CardTitle>
              <CardDescription>
                配置系統通知和警報設定
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>電子郵件通知</Label>
                  <p className="text-sm text-gray-600">接收系統狀態和決策通知</p>
                </div>
                <Switch
                  checked={settings.emailNotifications}
                  onCheckedChange={(checked) => handleSettingChange('emailNotifications', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>簡訊通知</Label>
                  <p className="text-sm text-gray-600">接收緊急警報簡訊</p>
                </div>
                <Switch
                  checked={settings.smsNotifications}
                  onCheckedChange={(checked) => handleSettingChange('smsNotifications', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>推播通知</Label>
                  <p className="text-sm text-gray-600">瀏覽器推播通知</p>
                </div>
                <Switch
                  checked={settings.pushNotifications}
                  onCheckedChange={(checked) => handleSettingChange('pushNotifications', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>緊急警報</Label>
                  <p className="text-sm text-gray-600">系統故障和緊急事件通知</p>
                </div>
                <Switch
                  checked={settings.criticalAlerts}
                  onCheckedChange={(checked) => handleSettingChange('criticalAlerts', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                系統設定
              </CardTitle>
              <CardDescription>
                配置系統運行參數
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="autoApproval">自動批准閾值 (%)</Label>
                  <Input
                    id="autoApproval"
                    type="number"
                    value={settings.autoApprovalThreshold}
                    onChange={(e) => handleSettingChange('autoApprovalThreshold', parseInt(e.target.value))}
                    min="0"
                    max="100"
                  />
                  <p className="text-sm text-gray-600">信心度超過此值時自動批准決策</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxDecisions">最大並發決策數</Label>
                  <Input
                    id="maxDecisions"
                    type="number"
                    value={settings.maxConcurrentDecisions}
                    onChange={(e) => handleSettingChange('maxConcurrentDecisions', parseInt(e.target.value))}
                    min="1"
                    max="50"
                  />
                  <p className="text-sm text-gray-600">同時處理的最大決策數量</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="timeout">決策超時時間 (秒)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    value={settings.decisionTimeout}
                    onChange={(e) => handleSettingChange('decisionTimeout', parseInt(e.target.value))}
                    min="60"
                    max="3600"
                  />
                  <p className="text-sm text-gray-600">決策等待批准的最長時間</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="logLevel">日誌級別</Label>
                  <Select
                    value={settings.logLevel}
                    onValueChange={(value) => handleSettingChange('logLevel', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="debug">Debug</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                      <SelectItem value="warning">Warning</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-600">系統日誌記錄級別</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                安全設定
              </CardTitle>
              <CardDescription>
                配置系統安全和認證設定
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sessionTimeout">會話超時 (分鐘)</Label>
                  <Input
                    id="sessionTimeout"
                    type="number"
                    value={settings.sessionTimeout}
                    onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                    min="5"
                    max="480"
                  />
                  <p className="text-sm text-gray-600">用戶會話自動過期時間</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxAttempts">最大登入嘗試次數</Label>
                  <Input
                    id="maxAttempts"
                    type="number"
                    value={settings.maxLoginAttempts}
                    onChange={(e) => handleSettingChange('maxLoginAttempts', parseInt(e.target.value))}
                    min="3"
                    max="10"
                  />
                  <p className="text-sm text-gray-600">帳號鎖定前的最大嘗試次數</p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>強制多因素認證</Label>
                  <p className="text-sm text-gray-600">要求所有用戶啟用 2FA</p>
                </div>
                <Switch
                  checked={settings.requireMFA}
                  onCheckedChange={(checked) => handleSettingChange('requireMFA', checked)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="passwordExpiry">密碼過期天數</Label>
                <Input
                  id="passwordExpiry"
                  type="number"
                  value={settings.passwordExpiry}
                  onChange={(e) => handleSettingChange('passwordExpiry', parseInt(e.target.value))}
                  min="30"
                  max="365"
                />
                <p className="text-sm text-gray-600">密碼強制更新週期</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                資料庫設定
              </CardTitle>
              <CardDescription>
                配置資料庫備份和維護設定
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="backupFreq">備份頻率</Label>
                  <Select
                    value={settings.backupFrequency}
                    onValueChange={(value) => handleSettingChange('backupFrequency', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">每小時</SelectItem>
                      <SelectItem value="daily">每日</SelectItem>
                      <SelectItem value="weekly">每週</SelectItem>
                      <SelectItem value="monthly">每月</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-600">自動備份執行頻率</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="retention">保留期限 (天)</Label>
                  <Input
                    id="retention"
                    type="number"
                    value={settings.retentionPeriod}
                    onChange={(e) => handleSettingChange('retentionPeriod', parseInt(e.target.value))}
                    min="7"
                    max="365"
                  />
                  <p className="text-sm text-gray-600">備份檔案保留天數</p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>啟用壓縮</Label>
                  <p className="text-sm text-gray-600">壓縮備份檔案以節省空間</p>
                </div>
                <Switch
                  checked={settings.compressionEnabled}
                  onCheckedChange={(checked) => handleSettingChange('compressionEnabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>啟用加密</Label>
                  <p className="text-sm text-gray-600">加密備份檔案以提高安全性</p>
                </div>
                <Switch
                  checked={settings.encryptionEnabled}
                  onCheckedChange={(checked) => handleSettingChange('encryptionEnabled', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemSettings;
