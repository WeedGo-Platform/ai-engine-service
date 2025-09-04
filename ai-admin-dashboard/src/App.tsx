import { useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { ChatProvider } from './contexts/ChatContext';
import Dashboard from './components/Dashboard';
import ExamplesLibrary from './components/ExamplesLibrary';
import ContextManager from './components/ContextManager';
import DecisionTreeVisualizer from './components/DecisionTreeVisualizer';
import UnifiedChatTestingHistory from './components/UnifiedChatTestingHistory';
import EnhancedFlowBuilderWrapper from './components/EnhancedFlowBuilderWrapper';
import Analytics from './components/Analytics';
import ServiceManager from './components/ServiceManager';
import ModelDeploymentEnhanced from './components/ModelDeploymentEnhanced';
import AIPersonality from './components/AIPersonality';
import AIConfiguration from './components/AIConfiguration';
import AISoulWindow from './components/AISoulWindow';
import CannabisKnowledgeBase from './components/CannabisKnowledgeBase';
import ComprehensiveTutorial from './components/ComprehensiveTutorial';
import InteractiveTutorial from './components/InteractiveTutorial';
import Navigation from './components/Navigation';
import SearchTesting from './components/SearchTesting';
import LiveChat from './components/LiveChat';
import VoiceEnabledChat from './components/VoiceEnabledChat';
import TestImports from './components/TestImports';
import PromptManagement from './components/PromptManagement';
import ModelTestChat from './components/ModelTestChat';

const queryClient = new QueryClient();

type TabType = 'dashboard' | 'tutorial' | 'comprehensive-tutorial' | 'examples-library' | 'context-manager' | 'ai-config' | 'decision-tree' | 'unified-chat' | 'enhanced-flow' | 'analytics' | 'services' | 'models' | 'personality' | 'ai-soul' | 'knowledge-base' | 'search-testing' | 'live-chat' | 'voice-chat' | 'test-imports' | 'prompt-management' | 'model-test';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <ChatProvider>
        <div className="min-h-screen bg-zinc-50">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#18181b',
              border: '1px solid #e4e4e7',
              borderRadius: '0.75rem',
              fontSize: '0.875rem',
            },
            success: {
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
        
        {/* Header */}
        <header className="bg-white border-b border-zinc-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="flex items-center space-x-3">
                  {/* WeedGo Logo - Modern, clean design */}
                  <div className="relative group">
                    <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110">
                      <span className="text-white font-bold text-lg">W</span>
                    </div>
                    <div className="absolute inset-0 bg-primary-400 rounded-xl blur-lg opacity-30 group-hover:opacity-50 transition-opacity"></div>
                  </div>
                  <div>
                    <h1 className="text-xl font-semibold text-zinc-900">WeedGo AI Admin</h1>
                    <p className="text-xs text-zinc-500">Virtual AI Budtender Platform</p>
                  </div>
                </div>
              </div>
              
              {/* System Status */}
              <div className="flex items-center space-x-4">
                {/* Service Health Indicators - Cleaner design */}
                <div className="hidden lg:flex items-center space-x-2">
                  <ServiceHealthIndicator name="AI Engine" status="online" />
                  <ServiceHealthIndicator name="Inventory" status="online" />
                  <ServiceHealthIndicator name="Pricing" status="warning" />
                </div>
                
                {/* AI Model Status - Modern badge */}
                <div className="flex items-center space-x-2 px-3 py-1.5 bg-zinc-100 rounded-full">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-medium text-zinc-700">Llama2-7B</span>
                </div>
                
                {/* Settings Button */}
                <button 
                  onClick={() => setShowSettings(true)}
                  className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'tutorial' && <InteractiveTutorial />}
          {activeTab === 'comprehensive-tutorial' && <ComprehensiveTutorial />}
          {activeTab === 'examples-library' && <ExamplesLibrary />}
          {activeTab === 'context-manager' && <ContextManager />}
          {activeTab === 'ai-config' && <AIConfiguration />}
          {activeTab === 'decision-tree' && <DecisionTreeVisualizer />}
          {activeTab === 'unified-chat' && <UnifiedChatTestingHistory />}
          {activeTab === 'enhanced-flow' && <EnhancedFlowBuilderWrapper />}
          {activeTab === 'analytics' && <Analytics />}
          {activeTab === 'services' && <ServiceManager />}
          {activeTab === 'models' && <ModelDeploymentEnhanced />}
          {activeTab === 'personality' && <AIPersonality />}
          {activeTab === 'ai-soul' && <AISoulWindow />}
          {activeTab === 'knowledge-base' && <CannabisKnowledgeBase />}
          {activeTab === 'search-testing' && <SearchTesting />}
          {activeTab === 'live-chat' && <LiveChat />}
          {activeTab === 'voice-chat' && <VoiceEnabledChat />}
          {activeTab === 'test-imports' && <TestImports />}
          {activeTab === 'prompt-management' && <PromptManagement />}
          {activeTab === 'model-test' && <ModelTestChat />}
        </main>
        
        {/* Settings Modal */}
        {showSettings && (
          <SettingsModal onClose={() => setShowSettings(false)} />
        )}
      </div>
      </ChatProvider>
    </QueryClientProvider>
  );
}

// Service Health Indicator Component - Modern Design
function ServiceHealthIndicator({ name, status }: { name: string; status: 'online' | 'warning' | 'offline' }) {
  const statusConfig = {
    online: { 
      color: 'bg-green-500', 
      text: 'text-green-700',
      bg: 'bg-green-50',
      label: 'Operational'
    },
    offline: { 
      color: 'bg-red-500', 
      text: 'text-red-700',
      bg: 'bg-red-50',
      label: 'Offline'
    },
    warning: { 
      color: 'bg-amber-500', 
      text: 'text-amber-700',
      bg: 'bg-amber-50',
      label: 'Degraded'
    },
  };

  const config = statusConfig[status];

  return (
    <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full ${config.bg}`}>
      <div className={`w-1.5 h-1.5 ${config.color} rounded-full ${status !== 'offline' ? 'animate-pulse' : ''}`}></div>
      <span className={`text-xs font-medium ${config.text}`}>{name}</span>
    </div>
  );
}

// Settings Modal Component
function SettingsModal({ onClose }: { onClose: () => void }) {
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://localhost:5024');
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  
  const handleSave = useCallback(async () => {
    try {
      // Save settings to localStorage
      localStorage.setItem('api_url', apiUrl);
      localStorage.setItem('cache_enabled', String(cacheEnabled));
      localStorage.setItem('debug_mode', String(debugMode));
      localStorage.setItem('auto_refresh', String(autoRefresh));
      localStorage.setItem('refresh_interval', String(refreshInterval));
      
      // Clear cache if requested
      if (!cacheEnabled) {
        const response = await fetch(`${apiUrl}/api/v1/admin/cache/clear`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
          toast.success('Cache cleared successfully');
        }
      }
      
      toast.success('Settings saved successfully');
      onClose();
      
      // Reload page to apply new settings
      setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      toast.error('Failed to save settings');
      console.error('Settings save error:', error);
    }
  }, [apiUrl, cacheEnabled, debugMode, autoRefresh, refreshInterval, onClose]);
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-zinc-900">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Settings Form */}
        <div className="space-y-4">
          {/* API URL */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              API URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="http://localhost:8080"
            />
          </div>
          
          {/* Cache Settings */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-zinc-700">Enable Cache</label>
              <p className="text-xs text-zinc-500">Store responses for faster loading</p>
            </div>
            <button
              onClick={() => setCacheEnabled(!cacheEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                cacheEnabled ? 'bg-primary-500' : 'bg-zinc-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  cacheEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          {/* Debug Mode */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-zinc-700">Debug Mode</label>
              <p className="text-xs text-zinc-500">Show detailed logs in console</p>
            </div>
            <button
              onClick={() => setDebugMode(!debugMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                debugMode ? 'bg-primary-500' : 'bg-zinc-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  debugMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          {/* Auto Refresh */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-zinc-700">Auto Refresh</label>
              <p className="text-xs text-zinc-500">Automatically refresh data</p>
            </div>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                autoRefresh ? 'bg-primary-500' : 'bg-zinc-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autoRefresh ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          {/* Refresh Interval */}
          {autoRefresh && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-2">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                min="1"
                max="60"
                className="w-full px-3 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-zinc-200 text-zinc-700 rounded-lg hover:bg-zinc-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;