import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DollarSign, TrendingUp, TrendingDown, PieChart, BarChart3 } from 'lucide-react';

const CostAnalysis = () => {
  const costData = {
    today: 45.67,
    thisMonth: 1234.56,
    lastMonth: 1456.78,
    yearToDate: 14567.89,
    trend: -15.2 // 負數表示節省
  };

  const services = [
    {
      name: 'AI 計算服務',
      cost: 567.89,
      percentage: 46,
      trend: 5.2,
      description: '機器學習模型訓練和推理'
    },
    {
      name: '雲端儲存',
      cost: 234.56,
      percentage: 19,
      trend: -8.1,
      description: '數據存儲和備份服務'
    },
    {
      name: '網路流量',
      cost: 189.34,
      percentage: 15,
      trend: 12.3,
      description: 'CDN 和數據傳輸費用'
    },
    {
      name: '數據庫服務',
      cost: 156.78,
      percentage: 13,
      trend: -3.4,
      description: '關聯式和 NoSQL 數據庫'
    },
    {
      name: '監控與日誌',
      cost: 85.99,
      percentage: 7,
      trend: 2.1,
      description: '系統監控和日誌分析'
    }
  ];

  const optimizations = [
    {
      id: 1,
      title: '閒置資源清理',
      description: '清理未使用的計算實例和存儲',
      potentialSaving: 234.56,
      effort: 'low',
      status: 'recommended'
    },
    {
      id: 2,
      title: '預留實例購買',
      description: '購買預留實例以獲得折扣',
      potentialSaving: 456.78,
      effort: 'medium',
      status: 'in_progress'
    },
    {
      id: 3,
      title: '自動擴縮容優化',
      description: '調整自動擴縮容策略',
      potentialSaving: 123.45,
      effort: 'high',
      status: 'completed'
    }
  ];

  const getEffortBadge = (effort) => {
    const variants = {
      low: 'secondary',
      medium: 'default',
      high: 'destructive'
    };
    
    const labels = {
      low: '低',
      medium: '中',
      high: '高'
    };

    return (
      <Badge variant={variants[effort]}>
        {labels[effort]}
      </Badge>
    );
  };

  const getStatusBadge = (status) => {
    const variants = {
      recommended: 'secondary',
      in_progress: 'default',
      completed: 'outline'
    };
    
    const labels = {
      recommended: '建議',
      in_progress: '進行中',
      completed: '已完成'
    };

    return (
      <Badge variant={variants[status]}>
        {labels[status]}
      </Badge>
    );
  };

  const getTrendIcon = (trend) => {
    return trend > 0 ? (
      <TrendingUp className="w-4 h-4 text-red-600" />
    ) : (
      <TrendingDown className="w-4 h-4 text-green-600" />
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">成本分析</h1>
          <p className="text-gray-600 mt-2">監控和優化 AI 服務成本</p>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-green-500" />
          <span className="text-sm text-gray-600">本月節省 ${Math.abs(costData.trend).toFixed(2)}%</span>
        </div>
      </div>

      {/* 成本概覽 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">今日成本</p>
                <p className="text-2xl font-bold">${costData.today}</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">本月成本</p>
                <p className="text-2xl font-bold">${costData.thisMonth.toLocaleString()}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">月度趨勢</p>
                <p className={`text-2xl font-bold ${costData.trend < 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {costData.trend > 0 ? '+' : ''}{costData.trend}%
                </p>
              </div>
              {costData.trend < 0 ? (
                <TrendingDown className="w-8 h-8 text-green-500" />
              ) : (
                <TrendingUp className="w-8 h-8 text-red-500" />
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">年度累計</p>
                <p className="text-2xl font-bold">${costData.yearToDate.toLocaleString()}</p>
              </div>
              <PieChart className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 服務成本分解 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>服務成本分解</CardTitle>
          <CardDescription>各項服務的成本佔比和趨勢</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {services.map((service, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium">{service.name}</h3>
                    <span className="text-sm text-gray-500">{service.percentage}%</span>
                    {getTrendIcon(service.trend)}
                    <span className={`text-sm ${service.trend > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {service.trend > 0 ? '+' : ''}{service.trend}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{service.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">${service.cost}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 優化建議 */}
      <Card>
        <CardHeader>
          <CardTitle>成本優化建議</CardTitle>
          <CardDescription>AI 系統識別的成本節省機會</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {optimizations.map((opt) => (
              <div key={opt.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-medium">{opt.title}</h3>
                    {getStatusBadge(opt.status)}
                    <span className="text-sm text-gray-500">實施難度：</span>
                    {getEffortBadge(opt.effort)}
                  </div>
                  <p className="text-sm text-gray-600">{opt.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">潛在節省</p>
                  <p className="text-lg font-bold text-green-600">${opt.potentialSaving}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CostAnalysis;
