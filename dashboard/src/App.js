
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { 
  Activity, 
  AlertTriangle, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  Play,
  Square,
  RefreshCw,
  Bot,
  Shield
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState(null);

  // WebSocket接続
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setStatus(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    websocket.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, []);

  // ログ取得
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/logs?limit=20`);
        const data = await response.json();
        setLogs(data);
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    };
    
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    
    return () => clearInterval(interval);
  }, []);

  // 緊急停止
  const handleEmergencyStop = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/control/stop`, {
        method: 'POST',
      });
      const data = await response.json();
      console.log('Emergency stop:', data);
    } catch (error) {
      console.error('Error stopping bot:', error);
    }
  };

  // ボット開始
  const handleStartBot = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/control/start`, {
        method: 'POST',
      });
      const data = await response.json();
      console.log('Start bot:', data);
    } catch (error) {
      console.error('Error starting bot:', error);
    }
  };

  // 再配分実行
  const handleRebalance = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/control/rebalance`, {
        method: 'POST',
      });
      const data = await response.json();
      console.log('Rebalance:', data);
    } catch (error) {
      console.error('Error rebalancing:', error);
    }
  };

  const getStatusColor = (isRunning) => {
    return isRunning ? 'bg-green-500' : 'bg-red-500';
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'safe': return 'bg-green-100 text-green-800';
      case 'balanced': return 'bg-yellow-100 text-yellow-800';
      case 'aggressive': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatCurrency = (value) => {
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Bot className="h-8 w-8 text-blue-600" />
            AI Trading Bot Dashboard
          </h1>
          <div className="flex items-center gap-4 mt-2">
            <Badge className={getStatusColor(status?.is_running)}>
              {status?.is_running ? 'Running' : 'Stopped'}
            </Badge>
            <Badge className={getRiskLevelColor(status?.risk_level)}>
              Risk: {status?.risk_level?.toUpperCase()}
            </Badge>
            <Badge className={isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
        </div>

        {/* メインコンテンツ */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="management">Management</TabsTrigger>
          </TabsList>

          {/* 概要タブ */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* システム状態 */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">System Status</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {status?.is_running ? 'Active' : 'Stopped'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Last update: {status?.last_rebalance ? new Date(status.last_rebalance).toLocaleTimeString() : 'N/A'}
                  </p>
                </CardContent>
              </Card>

              {/* リスクレベル */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Risk Level</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold capitalize">
                    {status?.risk_level || 'Unknown'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Current risk profile
                  </p>
                </CardContent>
              </Card>

              {/* 現在のドローダウン */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Current Drawdown</CardTitle>
                  <TrendingDown className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">
                    {formatPercentage(status?.risk_metrics?.current_drawdown || 0)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Daily loss: {formatPercentage(status?.risk_metrics?.daily_loss || 0)}
                  </p>
                </CardContent>
              </Card>

              {/* 同時取引数 */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Trades</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {status?.risk_metrics?.concurrent_trades || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Circuit breaker: {status?.risk_metrics?.circuit_breaker_failures || 0}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* 資金配分 */}
            <Card>
              <CardHeader>
                <CardTitle>Current Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {status?.allocation && Object.entries(status.allocation).map(([bot, ratio]) => (
                    <div key={bot} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                        <span className="font-medium capitalize">{bot}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{formatPercentage(ratio)}</div>
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${ratio * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* パフォーマンスタブ */}
          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {status?.performance_data && Object.entries(status.performance_data).map(([bot, data]) => (
                <Card key={bot}>
                  <CardHeader>
                    <CardTitle className="capitalize">{bot} Bot</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Win Rate</span>
                      <span className="font-bold">{formatPercentage(data.win_rate)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Total Return</span>
                      <span className="font-bold text-green-600">{formatPercentage(data.total_return)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Max Drawdown</span>
                      <span className="font-bold text-red-600">{formatPercentage(data.max_drawdown)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Trade Count</span>
                      <span className="font-bold">{data.trade_count}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* 管理タブ */}
          <TabsContent value="management" className="space-y-6">
            {/* コントロールパネル */}
            <Card>
              <CardHeader>
                <CardTitle>Bot Control</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Button 
                    onClick={handleStartBot}
                    disabled={status?.is_running}
                    className="flex items-center gap-2"
                  >
                    <Play className="h-4 w-4" />
                    Start Bot
                  </Button>
                  <Button 
                    onClick={handleEmergencyStop}
                    disabled={!status?.is_running}
                    variant="destructive"
                    className="flex items-center gap-2"
                  >
                    <Square className="h-4 w-4" />
                    Emergency Stop
                  </Button>
                  <Button 
                    onClick={handleRebalance}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Rebalance
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* ログ */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Logs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {logs.map((log, index) => (
                    <div key={index} className="flex items-start gap-3 p-2 rounded border">
                      <Badge 
                        className={
                          log.level === 'ERROR' ? 'bg-red-100 text-red-800' :
                          log.level === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                          log.level === 'INFO' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }
                      >
                        {log.level}
                      </Badge>
                      <div className="flex-1">
                        <div className="text-sm font-mono text-gray-600">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                        <div className="text-sm">{log.message}</div>
                        <div className="text-xs text-gray-500">{log.source}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;
