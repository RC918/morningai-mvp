import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Settings, Play, Pause, Trash2 } from 'lucide-react';

const StrategyManagement = () => {
  const strategies = [
    {
      id: 1,
      name: '風險評估策略',
      description: '基於機器學習的風險評估模型',
      status: 'active',
      lastUpdated: '2024-09-19',
      accuracy: '94.2%'
    },
    {
      id: 2,
      name: '成本優化策略',
      description: '自動化成本分析和優化建議',
      status: 'paused',
      lastUpdated: '2024-09-18',
      accuracy: '87.5%'
    },
    {
      id: 3,
      name: '決策支援策略',
      description: '多維度決策分析和建議系統',
      status: 'active',
      lastUpdated: '2024-09-19',
      accuracy: '91.8%'
    }
  ];

  const getStatusBadge = (status) => {
    const variants = {
      active: 'default',
      paused: 'secondary',
      inactive: 'destructive'
    };
    
    const labels = {
      active: '運行中',
      paused: '暫停',
      inactive: '停用'
    };

    return (
      <Badge variant={variants[status]}>
        {labels[status]}
      </Badge>
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">策略管理</h1>
          <p className="text-gray-600 mt-2">管理和配置 AI 決策策略</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          新增策略
        </Button>
      </div>

      <div className="grid gap-6">
        {strategies.map((strategy) => (
          <Card key={strategy.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {strategy.name}
                    {getStatusBadge(strategy.status)}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    {strategy.description}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    {strategy.status === 'active' ? (
                      <Pause className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </Button>
                  <Button variant="outline" size="sm">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">準確率：</span>
                  <span className="font-medium">{strategy.accuracy}</span>
                </div>
                <div>
                  <span className="text-gray-500">最後更新：</span>
                  <span className="font-medium">{strategy.lastUpdated}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default StrategyManagement;
