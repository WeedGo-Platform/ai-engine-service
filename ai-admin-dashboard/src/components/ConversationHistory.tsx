import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import apiService from '../services/api';

interface Conversation {
  id: string;
  session_id: string;
  customer_id: string;
  customer_name: string;
  customer_contact: string;
  budtender_personality: string;
  messages: ConversationMessage[];
  start_time: string;
  end_time: string;
  total_messages: number;
  products_recommended: number;
  intents_detected: string[];
  satisfaction_score?: number;
  conversion?: boolean;
}

interface ConversationMessage {
  id: string;
  timestamp: string;
  sender: 'customer' | 'budtender' | 'system';
  message: string;
  intent?: string;
  confidence?: number;
  products?: any[];
  metadata?: any;
}

interface FilterOptions {
  dateRange: {
    start: string;
    end: string;
  };
  customer: string;
  budtender: string;
  intent: string;
  hasProducts: boolean | null;
  converted: boolean | null;
}

export default function ConversationHistory() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: {
      start: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    customer: '',
    budtender: '',
    intent: '',
    hasProducts: null,
    converted: null
  });
  const [stats, setStats] = useState({
    totalConversations: 0,
    avgMessagesPerConversation: 0,
    conversionRate: 0,
    topIntents: [] as { intent: string; count: number }[],
    activeBudtenders: [] as { name: string; conversations: number }[]
  });
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchConversations();
  }, [filters]);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      
      const data = await apiService.getConversationHistory({
        start_date: filters.dateRange.start,
        end_date: filters.dateRange.end,
        customer: filters.customer || undefined,
        budtender: filters.budtender || undefined,
        intent: filters.intent || undefined,
        has_products: filters.hasProducts,
        converted: filters.converted
      });
      setConversations(data.conversations || []);
      
      // Calculate stats
      if (data.conversations && data.conversations.length > 0) {
        const totalMessages = data.conversations.reduce((sum: number, c: Conversation) => sum + c.total_messages, 0);
        const conversionsCount = data.conversations.filter((c: Conversation) => c.conversion).length;
        
        // Calculate top intents
        const intentCounts: { [key: string]: number } = {};
        data.conversations.forEach((c: Conversation) => {
          c.intents_detected?.forEach(intent => {
            intentCounts[intent] = (intentCounts[intent] || 0) + 1;
          });
        });
        
        const topIntents = Object.entries(intentCounts)
          .map(([intent, count]) => ({ intent, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
        
        // Calculate budtender activity
        const budtenderCounts: { [key: string]: number } = {};
        data.conversations.forEach((c: Conversation) => {
          budtenderCounts[c.budtender_personality] = (budtenderCounts[c.budtender_personality] || 0) + 1;
        });
        
        const activeBudtenders = Object.entries(budtenderCounts)
          .map(([name, conversations]) => ({ name, conversations }))
          .sort((a, b) => b.conversations - a.conversations);
        
        setStats({
          totalConversations: data.conversations.length,
          avgMessagesPerConversation: Math.round(totalMessages / data.conversations.length),
          conversionRate: Math.round((conversionsCount / data.conversations.length) * 100),
          topIntents,
          activeBudtenders
        });
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast.error('Failed to load conversation history');
      setConversations([]);
      setStats({
        totalConversations: 0,
        avgMessagesPerConversation: 0,
        conversionRate: 0,
        topIntents: [],
        activeBudtenders: []
      });
    } finally {
      setLoading(false);
    }
  };

  const exportConversation = (conversation: Conversation) => {
    const data = JSON.stringify(conversation, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${conversation.session_id}-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Conversation exported successfully');
  };

  const exportAllConversations = () => {
    const data = JSON.stringify(conversations, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversations-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('All conversations exported successfully');
  };

  const refreshConversations = async () => {
    setRefreshing(true);
    await fetchConversations();
    setRefreshing(false);
    toast.success('Conversations refreshed');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Conversation History</h2>
            <p className="text-sm text-gray-500 mt-1">
              Review and analyze customer interactions
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={refreshConversations}
              disabled={refreshing}
              className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <svg className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refresh</span>
            </button>
            <button
              onClick={exportAllConversations}
              className="flex items-center space-x-2 px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Export All</span>
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.totalConversations}</div>
            <div className="text-sm text-gray-500">Total Conversations</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.avgMessagesPerConversation}</div>
            <div className="text-sm text-gray-500">Avg Messages</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.conversionRate}%</div>
            <div className="text-sm text-gray-500">Conversion Rate</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.topIntents[0]?.intent || 'N/A'}</div>
            <div className="text-sm text-gray-500">Top Intent</div>
          </div>
        </div>

        {/* Filters */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, start: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, end: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer</label>
              <input
                type="text"
                placeholder="Name or ID"
                value={filters.customer}
                onChange={(e) => setFilters(prev => ({ ...prev, customer: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Budtender</label>
              <select
                value={filters.budtender}
                onChange={(e) => setFilters(prev => ({ ...prev, budtender: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              >
                <option value="">All Budtenders</option>
                {stats.activeBudtenders.map(bt => (
                  <option key={bt.name} value={bt.name}>{bt.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Has Products</label>
              <select
                value={filters.hasProducts === null ? '' : filters.hasProducts.toString()}
                onChange={(e) => setFilters(prev => ({ 
                  ...prev, 
                  hasProducts: e.target.value === '' ? null : e.target.value === 'true' 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              >
                <option value="">All</option>
                <option value="true">With Products</option>
                <option value="false">No Products</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Converted</label>
              <select
                value={filters.converted === null ? '' : filters.converted.toString()}
                onChange={(e) => setFilters(prev => ({ 
                  ...prev, 
                  converted: e.target.value === '' ? null : e.target.value === 'true' 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
              >
                <option value="">All</option>
                <option value="true">Converted</option>
                <option value="false">Not Converted</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Conversations List and Detail View */}
      <div className="grid grid-cols-3 gap-6">
        {/* Conversations List */}
        <div className="col-span-1 bg-white rounded-lg shadow-sm p-4 max-h-[600px] overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">Conversations</h3>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-weed-green-500"></div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No conversations found
            </div>
          ) : (
            <div className="space-y-3">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedConversation?.id === conv.id
                      ? 'bg-weed-green-50 border-2 border-weed-green-500'
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-medium text-gray-900">{conv.customer_name}</div>
                    <div className="text-xs text-gray-500">
                      {format(new Date(conv.start_time), 'MMM d, h:mm a')}
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 mb-1">{conv.budtender_personality}</div>
                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-500">
                      {conv.total_messages} messages
                    </div>
                    {conv.conversion && (
                      <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                        Converted
                      </span>
                    )}
                  </div>
                  {conv.intents_detected.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {conv.intents_detected.slice(0, 3).map((intent) => (
                        <span
                          key={intent}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded"
                        >
                          {intent}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Conversation Detail */}
        <div className="col-span-2 bg-white rounded-lg shadow-sm p-6">
          {selectedConversation ? (
            <div>
              {/* Conversation Header */}
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {selectedConversation.customer_name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {selectedConversation.customer_contact} • Session: {selectedConversation.session_id}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {format(new Date(selectedConversation.start_time), 'PPP p')} - 
                    {format(new Date(selectedConversation.end_time), 'p')}
                  </p>
                </div>
                <button
                  onClick={() => exportConversation(selectedConversation)}
                  className="flex items-center space-x-2 px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span className="text-sm">Export</span>
                </button>
              </div>

              {/* Conversation Metadata */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Budtender</div>
                  <div className="font-medium">{selectedConversation.budtender_personality}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Messages</div>
                  <div className="font-medium">{selectedConversation.total_messages}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Products Shown</div>
                  <div className="font-medium">{selectedConversation.products_recommended}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Satisfaction</div>
                  <div className="font-medium">
                    {selectedConversation.satisfaction_score ? 
                      `${selectedConversation.satisfaction_score}/5` : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-4">Conversation Flow</h4>
                <div className="space-y-4 max-h-[400px] overflow-y-auto">
                  {selectedConversation.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.sender === 'customer' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-lg p-3 ${
                          msg.sender === 'customer'
                            ? 'bg-weed-green-500 text-white'
                            : msg.sender === 'system'
                            ? 'bg-gray-100 text-gray-700 italic'
                            : 'bg-gray-200 text-gray-900'
                        }`}
                      >
                        <div className="text-sm">{msg.message}</div>
                        {msg.intent && (
                          <div className="mt-2 text-xs opacity-75">
                            Intent: {msg.intent} ({Math.round((msg.confidence || 0) * 100)}%)
                          </div>
                        )}
                        {msg.products && msg.products.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-white/20">
                            <div className="text-xs mb-1">Products recommended:</div>
                            {msg.products.map((product: any, idx: number) => (
                              <div key={idx} className="text-xs">
                                • {product.name} - ${product.price}
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="text-xs mt-1 opacity-50">
                          {format(new Date(msg.timestamp), 'h:mm:ss a')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select a conversation to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}