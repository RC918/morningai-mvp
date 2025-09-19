import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, BarChart3, Calendar } from 'lucide-react';

const HistoryAnalysis = () => {
  const decisions = [
    {
      id: 1,
      date: '2024-09-19',
      strategy: 'CPU優化策略',
      action: '自動擴容',
      result: 'success',
      impact: 'CPU使用率降低25%',
      cost: '$18.50',
      duration: '3分鐘'
    },
    {
      id: 2,
      date: '2024-09-18',
      strategy: '成本優化策略',
      action: '雲端資源調整',
      result: 'success',
      impact: '月度成本節省20%',
      cost: '-$2,500',
      duration: '15分鐘'
    },
    {
      id: 3,
      date: '2024-09-17',
      strategy: '風險評估策略',
      action: '投資組合調整',
      result: 'partial',
      impact: '風險降低15%',
      cost: '$1,200',
      duration: '1小時'
    },
    {
      id: 4,
      date: '2024-09-16',
      strategy: '決策支援策略',
      action: '人力資源優化',
      result: 'success',
      impact: '效率提升30%',
      cost: '$5,000',
      duration: '2小時'
    }
  ];

  const getResultBadge = (result) => {
    const variants = {
      success: 'default',
      partial: 'secondary',
      failed: 'destructive'
    };
    
    const labels = {
      success: '成功',
      partial: '部分成功',
      failed: '失敗'
    };

    return (
      <Badge variant={variants[result]}>
        {labels[result]}
      </Badge>
    );
  };

  const getImpactIcon = (cost) => {
    const isPositive = cost.startsWith('-');
    return isPositive ? (
      <TrendingDown className="w-4 h-4 text-green-600" />
    ) : (
      <TrendingUp className="w-4 h-4 text-red-600" />
    );
  };

  const stats = {
    totalDecisions: decisions.length,
    successRate: Math.round((decisions.filter(d => d.result === 'success').length / decisions.length) * 100),
    totalSavings: decisions.reduce((acc, d) => {
      const cost = parseFloat(d.cost.replace(/[$,]/g, ''));
      return acc + (d.cost.startsWith('-') ? Math.abs(cost) : -cost);
    }, 0),
    avgDuration: '45分鐘'
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">歷史分析</h1>
          <p className="text-gray-600 mt-2">回顧和分析過往決策的執行結果</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-500" />
          <span className="text-sm text-gray-600">最近30天</span>
        </div>
      </div>

      {/* 統計摘要 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總決策數</p>
                <p className="text-2xl font-bold">{stats.totalDecisions}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">成功率</p>
                <p className="text-2xl font-bold text-green-600">{stats.successRate}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總節省</p>
                <p className="text-2xl font-bold text-green-600">${stats.totalSavings.toLocaleString()}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均執行時間</p>
                <p className="text-2xl font-bold">{stats.avgDuration}</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 決策歷史列表 */}
      <div className="space-y-4">
        {decisions.map((decision) => (
          <Card key={decision.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {decision.strategy}
                    {getResultBadge(decision.result)}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    執行動作：{decision.action}
                  </CardDescription>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">{decision.date}</p>
                  <p className="text-sm text-gray-500">耗時：{decision.duration}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500">執行結果：</span>
                  <span className="font-medium">{decision.impact}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">成本影響：</span>
                  {getImpactIcon(decision.cost)}
                  <span className={`font-medium ${decision.cost.startsWith('-') ? 'text-green-600' : 'text-red-600'}`}>
                    {decision.cost}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default HistoryAnalysis;
