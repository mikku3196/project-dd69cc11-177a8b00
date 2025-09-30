"""
Webダッシュボード - React フロントエンド
"""
import os
import json
from pathlib import Path

# React アプリケーションのメインファイル
react_app_content = '''
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
'''

# package.json
package_json_content = '''
{
  "name": "trading-bot-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "lucide-react": "^0.263.1",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^1.14.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24"
  }
}
'''

# tailwind.config.js
tailwind_config_content = '''
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

# ディレクトリ作成
dashboard_dir = Path("dashboard")
dashboard_dir.mkdir(exist_ok=True)

src_dir = dashboard_dir / "src"
src_dir.mkdir(exist_ok=True)

components_dir = src_dir / "components"
components_dir.mkdir(exist_ok=True)

ui_dir = components_dir / "ui"
ui_dir.mkdir(exist_ok=True)

# ファイル作成
(dashboard_dir / "package.json").write_text(package_json_content)
(dashboard_dir / "tailwind.config.js").write_text(tailwind_config_content)
(src_dir / "App.js").write_text(react_app_content)

# 簡易UIコンポーネント（shadcn/ui風）
ui_components = {
    "card.js": '''
import React from 'react';
import { cn } from '../../utils/cn';

export const Card = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

export const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

export const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";
''',
    
    "button.js": '''
import React from 'react';
import { cn } from '../../utils/cn';

export const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    link: "text-primary underline-offset-4 hover:underline",
  };
  
  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-11 rounded-md px-8",
    icon: "h-10 w-10",
  };
  
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Button.displayName = "Button";
''',
    
    "badge.js": '''
import React from 'react';
import { cn } from '../../utils/cn';

export const Badge = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
    outline: "text-foreground",
  };
  
  return (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});
Badge.displayName = "Badge";
''',
    
    "alert.js": '''
import React from 'react';
import { cn } from '../../utils/cn';

export const Alert = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(
      "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
      className
    )}
    {...props}
  />
));
Alert.displayName = "Alert";

export const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";
''',
    
    "tabs.js": '''
import React, { createContext, useContext, useState } from 'react';
import { cn } from '../../utils/cn';

const TabsContext = createContext();

export const Tabs = ({ defaultValue, value, onValueChange, className, children, ...props }) => {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = (newValue) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };
  
  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const TabsList = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  />
));
TabsList.displayName = "TabsList";

export const TabsTrigger = React.forwardRef(({ className, value, ...props }, ref) => {
  const context = useContext(TabsContext);
  const isActive = context.value === value;
  
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive && "bg-background text-foreground shadow-sm",
        className
      )}
      onClick={() => context.onValueChange(value)}
      {...props}
    />
  );
});
TabsTrigger.displayName = "TabsTrigger";

export const TabsContent = React.forwardRef(({ className, value, ...props }, ref) => {
  const context = useContext(TabsContext);
  
  if (context.value !== value) {
    return null;
  }
  
  return (
    <div
      ref={ref}
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    />
  );
});
TabsContent.displayName = "TabsContent";
'''
}

# UIコンポーネントファイル作成
for filename, content in ui_components.items():
    (ui_dir / filename).write_text(content)

# ユーティリティファイル
utils_dir = src_dir / "utils"
utils_dir.mkdir(exist_ok=True)

cn_util_content = '''
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
'''

(utils_dir / "cn.js").write_text(cn_util_content)

# index.js
index_content = '''
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''

(src_dir / "index.js").write_text(index_content)

# index.css
index_css_content = '''
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 84% 4.9%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 84% 4.9%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
  --radius: 0.5rem;
}

body {
  color: rgb(var(--foreground));
  background: rgb(var(--background));
}
'''

(src_dir / "index.css").write_text(index_css_content)

# public/index.html
public_dir = dashboard_dir / "public"
public_dir.mkdir(exist_ok=True)

index_html_content = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="AI Trading Bot Dashboard" />
    <title>Trading Bot Dashboard</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''

(public_dir / "index.html").write_text(index_html_content)

print("[SUCCESS] React ダッシュボード作成完了")
print(f"[INFO] ディレクトリ: {dashboard_dir}")
print("[INFO] 起動方法:")
print("  cd dashboard")
print("  npm install")
print("  npm start")