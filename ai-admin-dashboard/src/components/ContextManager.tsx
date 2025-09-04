import { endpoints } from '../config/endpoints';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { 
  Database,
  MessageSquare,
  User,
  Clock,
  TrendingUp,
  RefreshCw,
  Search,
  Filter,
  ChevronRight,
  Settings,
  Trash2,
  Eye,
  History,
  Brain,
  Tag,
  AlertCircle,
  CheckCircle,
  Info,
  Archive,
  Activity
} from 'lucide-react';

interface ConversationContext {
  sessionId: string;
  userId?: string;
  timestamp: string;
  lastIntent: string;
  lastProducts: any[];
  conversationHistory: Array<{
    role: 'user' | 'assistant';
    message: string;
    timestamp: string;
    intent?: string;
    confidence?: number;
  }>;
  customerProfile?: {
    preferences: string[];
    purchaseHistory: string[];
    medicalNeeds?: string[];
  };
  metadata: {
    source: string;
    version: string;
    modelUsed?: string;
  };
}

interface ContextStats {
  totalSessions: number;
  activeSessions: number;
  averageLength: number;
  topIntents: { intent: string; count: number }[];
  peakHours: { hour: number; count: number }[];
}

export default function ContextManager() {
  const [selectedSession, setSelectedSession] = useState<ConversationContext | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIntent, setFilterIntent] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  
  // Fetch context data
  const { data: contexts = [], refetch: refetchContexts } = useQuery({
    queryKey: ['conversation-contexts', timeRange],
    queryFn: async () => {
      const response = await fetch(`${endpoints.base}/conversation/contexts?range=${timeRange}`);
      if (!response.ok) return [];
      return response.json();
    },
    refetchInterval: 10000 // Refresh every 10 seconds for real-time updates
  });
  
  // Calculate stats
  const stats: ContextStats = {
    totalSessions: contexts.length,
    activeSessions: contexts.filter((c: ConversationContext) => {
      const lastMessage = c.conversationHistory[c.conversationHistory.length - 1];
      if (!lastMessage) return false;
      const lastTime = new Date(lastMessage.timestamp);
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      return lastTime > fiveMinutesAgo;
    }).length,
    averageLength: contexts.reduce((sum: number, c: ConversationContext) => 
      sum + c.conversationHistory.length, 0) / (contexts.length || 1),
    topIntents: Object.entries(
      contexts.reduce((acc: Record<string, number>, c: ConversationContext) => {
        if (c.lastIntent) {
          acc[c.lastIntent] = (acc[c.lastIntent] || 0) + 1;
        }
        return acc;
      }, {})
    ).map(([intent, count]) => ({ intent, count }))
     .sort((a, b) => b.count - a.count)
     .slice(0, 5),
    peakHours: Object.entries(
      contexts.reduce((acc: Record<number, number>, c: ConversationContext) => {
        const hour = new Date(c.timestamp).getHours();
        acc[hour] = (acc[hour] || 0) + 1;
        return acc;
      }, {})
    ).map(([hour, count]) => ({ hour: parseInt(hour), count }))
     .sort((a, b) => a.hour - b.hour)
  };
  
  // Filter contexts
  const filteredContexts = contexts.filter((c: ConversationContext) => {
    const matchesSearch = !searchTerm || 
      c.sessionId.includes(searchTerm) ||
      c.conversationHistory.some(msg => 
        msg.message.toLowerCase().includes(searchTerm.toLowerCase())
      );
    const matchesIntent = filterIntent === 'all' || c.lastIntent === filterIntent;
    return matchesSearch && matchesIntent;
  });
  
  // Clear context mutation
  const clearContextMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await fetch(`${endpoints.base}/conversation/context/${sessionId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to clear context');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Context cleared');
      refetchContexts();
      setSelectedSession(null);
    },
    onError: () => {
      toast.error('Failed to clear context');
    }
  });
  
  // Archive old contexts mutation
  const archiveOldContextsMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${endpoints.base}/conversation/contexts/archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ olderThan: '7d' })
      });
      if (!response.ok) throw new Error('Failed to archive contexts');
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Archived ${data.count} old contexts`);
      refetchContexts();
    },
    onError: () => {
      toast.error('Failed to archive contexts');
    }
  });
  
  const intents = ['all', 'search', 'purchase', 'question', 'greeting', 'navigation', 'recommendation'];
  
  return (
    <div className="max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-zinc-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-zinc-900">Context Manager</h2>
                <p className="text-sm text-zinc-500">Manage conversation context and session data</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="px-4 py-2 border border-zinc-300 rounded-lg"
              >
                <option value="1h">Last Hour</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
              <button
                onClick={() => refetchContexts()}
                className="px-4 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-50 flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={() => archiveOldContextsMutation.mutate()}
                className="px-4 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-50 flex items-center gap-2"
              >
                <Archive className="w-4 h-4" />
                Archive Old
              </button>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-5 gap-4">
            <div className="p-4 bg-zinc-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Database className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-600">Total Sessions</span>
              </div>
              <p className="text-2xl font-bold text-zinc-900">{stats.totalSessions}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600">Active Now</span>
              </div>
              <p className="text-2xl font-bold text-green-900">{stats.activeSessions}</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <MessageSquare className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-blue-600">Avg Length</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">{stats.averageLength.toFixed(1)} msgs</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Brain className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-purple-600">Top Intent</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {stats.topIntents[0]?.intent || 'None'}
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-orange-500" />
                <span className="text-sm text-orange-600">Peak Hour</span>
              </div>
              <p className="text-2xl font-bold text-orange-900">
                {stats.peakHours.reduce((max, h) => h.count > (max?.count || 0) ? h : max, null)?.hour || 0}:00
              </p>
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Sessions List */}
          <div className="col-span-5">
            <div className="bg-white rounded-xl shadow-sm border border-zinc-200">
              {/* Filters */}
              <div className="p-4 border-b border-zinc-200 space-y-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search sessions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-zinc-300 rounded-lg"
                  />
                </div>
                <select
                  value={filterIntent}
                  onChange={(e) => setFilterIntent(e.target.value)}
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg"
                >
                  {intents.map(intent => (
                    <option key={intent} value={intent}>
                      {intent === 'all' ? 'All Intents' : intent}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Sessions */}
              <div className="max-h-[600px] overflow-y-auto">
                {filteredContexts.map((context: ConversationContext) => {
                  const isActive = stats.activeSessions > 0 && 
                    new Date(context.timestamp) > new Date(Date.now() - 5 * 60 * 1000);
                  
                  return (
                    <motion.div
                      key={context.sessionId}
                      className={`p-4 border-b border-zinc-200 hover:bg-zinc-50 cursor-pointer ${
                        selectedSession?.sessionId === context.sessionId ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedSession(context)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${
                            isActive ? 'bg-green-500 animate-pulse' : 'bg-zinc-300'
                          }`} />
                          <span className="font-medium text-zinc-900">
                            {context.sessionId.substring(0, 8)}...
                          </span>
                        </div>
                        <span className="text-xs text-zinc-500">
                          {new Date(context.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Tag className="w-3 h-3 text-zinc-400" />
                          <span className="text-sm text-zinc-600">
                            Intent: {context.lastIntent || 'unknown'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-3 h-3 text-zinc-400" />
                          <span className="text-sm text-zinc-600">
                            {context.conversationHistory.length} messages
                          </span>
                        </div>
                        {context.lastProducts && context.lastProducts.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Info className="w-3 h-3 text-zinc-400" />
                            <span className="text-sm text-zinc-600">
                              {context.lastProducts.length} products shown
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
                
                {filteredContexts.length === 0 && (
                  <div className="p-8 text-center text-zinc-500">
                    No sessions found
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Session Details */}
          <div className="col-span-7">
            {selectedSession ? (
              <div className="bg-white rounded-xl shadow-sm border border-zinc-200">
                {/* Session Header */}
                <div className="p-4 border-b border-zinc-200">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-zinc-900">
                        Session: {selectedSession.sessionId}
                      </h3>
                      <p className="text-sm text-zinc-500">
                        Started: {new Date(selectedSession.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => clearContextMutation.mutate(selectedSession.sessionId)}
                      className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 flex items-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Clear Context
                    </button>
                  </div>
                </div>
                
                {/* Conversation History */}
                <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                  <h4 className="font-semibold text-zinc-900 mb-3">Conversation History</h4>
                  {selectedSession.conversationHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${
                        msg.role === 'assistant' ? 'justify-start' : 'justify-end'
                      }`}
                    >
                      <div className={`max-w-[70%] p-3 rounded-lg ${
                        msg.role === 'assistant'
                          ? 'bg-zinc-100 text-zinc-900'
                          : 'bg-blue-600 text-white'
                      }`}>
                        <p className="text-sm">{msg.message}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs opacity-70">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                          {msg.intent && (
                            <span className="text-xs px-2 py-0.5 bg-white/20 rounded">
                              {msg.intent}
                            </span>
                          )}
                          {msg.confidence && (
                            <span className="text-xs">
                              {(msg.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Context Details */}
                <div className="p-4 border-t border-zinc-200">
                  <h4 className="font-semibold text-zinc-900 mb-3">Context Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {selectedSession.customerProfile && (
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-zinc-700">Customer Profile</h5>
                        <div className="space-y-1">
                          {selectedSession.customerProfile.preferences.map((pref, idx) => (
                            <span key={idx} className="inline-block px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded mr-1">
                              {pref}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {selectedSession.lastProducts && selectedSession.lastProducts.length > 0 && (
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-zinc-700">Products Shown</h5>
                        <div className="space-y-1">
                          {selectedSession.lastProducts.slice(0, 3).map((product: any, idx) => (
                            <div key={idx} className="text-xs text-zinc-600">
                              • {product.name || product.product_name}
                            </div>
                          ))}
                          {selectedSession.lastProducts.length > 3 && (
                            <div className="text-xs text-zinc-500">
                              +{selectedSession.lastProducts.length - 3} more
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    <div className="space-y-2">
                      <h5 className="text-sm font-medium text-zinc-700">Metadata</h5>
                      <div className="space-y-1 text-xs text-zinc-600">
                        <div>Source: {selectedSession.metadata.source}</div>
                        <div>Version: {selectedSession.metadata.version}</div>
                        {selectedSession.metadata.modelUsed && (
                          <div>Model: {selectedSession.metadata.modelUsed}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-12">
                <div className="text-center text-zinc-500">
                  <Database className="w-12 h-12 mx-auto mb-4 text-zinc-300" />
                  <p>Select a session to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Activity Timeline */}
        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
          <h3 className="font-bold text-zinc-900 mb-4">Activity Timeline</h3>
          <div className="flex items-end gap-2 h-32">
            {stats.peakHours.map(({ hour, count }) => {
              const maxCount = Math.max(...stats.peakHours.map(h => h.count));
              const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
              
              return (
                <div key={hour} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-gradient-to-t from-blue-500 to-blue-300 rounded-t"
                    style={{ height: `${height}%` }}
                  />
                  <span className="text-xs text-zinc-500 mt-1">{hour}</span>
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </div>
  );
}