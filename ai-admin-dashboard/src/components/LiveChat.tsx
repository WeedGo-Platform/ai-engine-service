import { endpoints } from '../config/endpoints';
import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Clock, MessageSquare, Search, RefreshCw, ShoppingCart, Package, Loader2, Brain, Database, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

interface ChatUser {
  customer_id: string;
  last_session_id: string;
  last_message: string;
  last_response: string;
  last_interaction: string;
  total_messages: number;
}

interface Product {
  id: string;
  product_name: string;
  brand?: string;
  category?: string;
  sub_category?: string;
  size?: string;
  price: number;
  thc?: number;
  cbd?: number;
  description?: string;
  image?: string;
  image_url?: string;
}

interface ChatMessage {
  message_id?: string;
  user_message: string;
  ai_response: string;
  created_at?: string;
  intent?: string;
  response_time?: number;
  isNew?: boolean;
  products?: Product[];
  quick_actions?: Array<{
    label: string;
    action: string;
    data?: any;
  }>;
}

const LiveChat: React.FC = () => {
  const [users, setUsers] = useState<ChatUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [loadingStartTime, setLoadingStartTime] = useState<number | null>(null);
  const [loadingPhase, setLoadingPhase] = useState<'thinking' | 'searching' | 'analyzing' | 'finalizing'>('thinking');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const loadingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch all users who have chatted
  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await fetch(endpoints.chat.users);
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoadingUsers(false);
    }
  };

  // Fetch chat history for selected user
  const fetchChatHistory = async (customerId: string) => {
    setLoadingHistory(true);
    try {
      const response = await fetch(`${endpoints.chat.history(customerId)}?limit=100`);
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      
      // Transform history to messages format
      const formattedMessages: ChatMessage[] = data.history.map((item: any) => ({
        message_id: item.message_id,
        user_message: item.user_message,
        ai_response: item.ai_response,
        created_at: item.created_at,
        intent: item.intent,
        response_time: item.response_time
      })).reverse(); // Reverse to show oldest first
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      toast.error('Failed to load chat history');
    } finally {
      setLoadingHistory(false);
    }
  };

  // Handle quick action click
  const handleQuickAction = async (actionLabel: string) => {
    setNewMessage(actionLabel);
    // Auto-send the message
    await sendMessageWithText(actionLabel);
  };

  // Send a new message
  const sendMessage = async () => {
    await sendMessageWithText(newMessage);
  };

  // Core message sending logic
  const sendMessageWithText = async (messageText: string) => {
    if (!messageText.trim() || !selectedUser) return;

    const userMessage = messageText.trim();
    setNewMessage('');
    
    // Add user message to chat immediately
    const tempMessage: ChatMessage = {
      user_message: userMessage,
      ai_response: '',
      isNew: true
    };
    setMessages(prev => [...prev, tempMessage]);
    
    setLoading(true);
    const startTime = Date.now();
    setLoadingStartTime(startTime);
    setLoadingPhase('thinking');
    
    // Start animation timer with rotating phases
    if (loadingTimerRef.current) clearInterval(loadingTimerRef.current);
    loadingTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      
      // Create a rotating cycle every 8 seconds
      const cycleTime = elapsed % 8000;
      
      if (cycleTime < 2000) {
        setLoadingPhase('thinking');
      } else if (cycleTime < 4000) {
        setLoadingPhase('searching');
      } else if (cycleTime < 6000) {
        setLoadingPhase('analyzing');
      } else {
        setLoadingPhase('finalizing');
      }
    }, 100);
    try {
      const response = await fetch(endpoints.chat.base, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          customer_id: selectedUser,
          session_id: users.find(u => u.customer_id === selectedUser)?.last_session_id || 'admin-chat'
        })
      });

      if (!response.ok) throw new Error('Failed to send message');
      const data = await response.json();
      
      // Update the last message with AI response and products
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          user_message: userMessage,
          ai_response: data.message,
          created_at: new Date().toISOString(),
          isNew: true,
          products: data.products,
          quick_actions: data.quick_actions
        };
        return updated;
      });
      
      toast.success('Message sent');
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
      // Remove the failed message
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
    }
  };

  // Load users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);

  // Load chat history when user is selected
  useEffect(() => {
    if (selectedUser) {
      fetchChatHistory(selectedUser);
    }
  }, [selectedUser]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Filter users based on search
  const filteredUsers = users.filter(user => 
    user.customer_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_message?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white rounded-xl shadow-sm border border-zinc-200">
      {/* Users Sidebar */}
      <div className="w-80 border-r border-zinc-200 flex flex-col">
        {/* Search Header */}
        <div className="p-4 border-b border-zinc-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-zinc-50 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={fetchUsers}
            className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-100 transition-colors text-sm"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh Users
          </button>
        </div>

        {/* Users List */}
        <div className="flex-1 overflow-y-auto">
          {loadingUsers ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center text-zinc-500 py-8 px-4">
              {searchTerm ? 'No users found' : 'No chat history yet'}
            </div>
          ) : (
            <div className="divide-y divide-zinc-100">
              {filteredUsers.map((user) => (
                <div
                  key={user.customer_id}
                  onClick={() => setSelectedUser(user.customer_id)}
                  className={`p-4 cursor-pointer hover:bg-zinc-50 transition-colors ${
                    selectedUser === user.customer_id ? 'bg-emerald-50 border-l-4 border-emerald-600' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-zinc-200 rounded-full flex items-center justify-center">
                      <User className="h-5 w-5 text-zinc-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-zinc-900 truncate">
                        {user.customer_id}
                      </h4>
                      <p className="text-sm text-zinc-600 truncate">
                        {user.last_message}
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-xs text-zinc-500 flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {user.total_messages} messages
                        </span>
                        <span className="text-xs text-zinc-500 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(user.last_interaction).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedUser ? (
          <>
            {/* Chat Header */}
            <div className="px-6 py-4 border-b border-zinc-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                  <User className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900">{selectedUser}</h3>
                  <p className="text-sm text-zinc-600">
                    Customer ID • {messages.length} messages in history
                  </p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingHistory ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center text-zinc-500 py-8">
                  No messages yet. Start a conversation!
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div key={msg.message_id || index} className="space-y-2">
                    {/* User Message */}
                    <div className="flex justify-end">
                      <div className={`max-w-2xl px-4 py-2 rounded-lg ${
                        msg.isNew ? 'bg-emerald-600 text-white' : 'bg-zinc-100 text-zinc-900'
                      }`}>
                        <p className="text-sm">{msg.user_message}</p>
                        {msg.created_at && (
                          <p className={`text-xs mt-1 ${
                            msg.isNew ? 'text-emerald-100' : 'text-zinc-500'
                          }`}>
                            {new Date(msg.created_at).toLocaleTimeString()}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* AI Response or Loading */}
                    {(msg.ai_response || (loading && index === messages.length - 1)) && (
                      <div className="flex justify-start">
                        <div className="max-w-3xl">
                          <div className="px-4 py-2 bg-white border border-zinc-200 rounded-lg">
                            {msg.ai_response ? (
                              <p className="text-sm text-zinc-900 whitespace-pre-wrap">{msg.ai_response}</p>
                            ) : (
                              /* Loading Animation */
                              <div className="flex items-center gap-3">
                                {loadingPhase === 'thinking' && (
                                  <>
                                    <Brain className="h-5 w-5 text-emerald-600 animate-pulse" />
                                    <span className="text-sm text-zinc-600">AI is thinking...</span>
                                  </>
                                )}
                                {loadingPhase === 'searching' && (
                                  <>
                                    <Database className="h-5 w-5 text-blue-600 animate-spin" />
                                    <span className="text-sm text-zinc-600">Searching our inventory...</span>
                                  </>
                                )}
                                {loadingPhase === 'analyzing' && (
                                  <>
                                    <Sparkles className="h-5 w-5 text-purple-600 animate-pulse" />
                                    <span className="text-sm text-zinc-600">Analyzing best matches...</span>
                                  </>
                                )}
                                {loadingPhase === 'finalizing' && (
                                  <>
                                    <Loader2 className="h-5 w-5 text-emerald-600 animate-spin" />
                                    <span className="text-sm text-zinc-600">Almost there...</span>
                                  </>
                                )}
                              </div>
                            )}
                            <div className="flex items-center gap-4 mt-2">
                              {msg.intent && (
                                <span className="text-xs text-zinc-500">
                                  Intent: {msg.intent}
                                </span>
                              )}
                              {msg.response_time && (
                                <span className="text-xs text-zinc-500">
                                  {msg.response_time}ms
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Product Cards */}
                          {msg.products && msg.products.length > 0 && (
                            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                              {msg.products.map((product, idx) => (
                                <div key={product.id || idx} className="bg-white border border-zinc-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                                  {/* Product Image */}
                                  {(product.image || product.image_url) && (
                                    <div className="h-48 bg-zinc-100 relative">
                                      <img 
                                        src={product.image || product.image_url}
                                        alt={product.product_name}
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%23a1a1aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"%3E%3Crect x="3" y="3" width="18" height="18" rx="2" ry="2"%3E%3C/rect%3E%3Ccircle cx="8.5" cy="8.5" r="1.5"%3E%3C/circle%3E%3Cpolyline points="21 15 16 10 5 21"%3E%3C/polyline%3E%3C/svg%3E';
                                        }}
                                      />
                                      {product.category && (
                                        <span className="absolute top-2 left-2 px-2 py-1 bg-black/70 text-white text-xs rounded">
                                          {product.category}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Product Details */}
                                  <div className="p-4">
                                    <h4 className="font-medium text-zinc-900 text-sm mb-1">
                                      {product.product_name}
                                    </h4>
                                    {product.brand && (
                                      <p className="text-xs text-zinc-600 mb-2">{product.brand}</p>
                                    )}
                                    
                                    {/* Product Info Grid */}
                                    <div className="grid grid-cols-2 gap-2 mb-3">
                                      {product.size && (
                                        <div className="text-xs">
                                          <span className="text-zinc-500">Size:</span>
                                          <span className="ml-1 text-zinc-700 font-medium">{product.size}</span>
                                        </div>
                                      )}
                                      {product.thc !== undefined && (
                                        <div className="text-xs">
                                          <span className="text-zinc-500">THC:</span>
                                          <span className="ml-1 text-zinc-700 font-medium">{product.thc}%</span>
                                        </div>
                                      )}
                                      {product.cbd !== undefined && (
                                        <div className="text-xs">
                                          <span className="text-zinc-500">CBD:</span>
                                          <span className="ml-1 text-zinc-700 font-medium">{product.cbd}%</span>
                                        </div>
                                      )}
                                      {product.sub_category && (
                                        <div className="text-xs">
                                          <span className="text-zinc-500">Type:</span>
                                          <span className="ml-1 text-zinc-700 font-medium">{product.sub_category}</span>
                                        </div>
                                      )}
                                    </div>
                                    
                                    {/* Price and Action */}
                                    <div className="flex items-center justify-between">
                                      <span className="text-lg font-bold text-emerald-600">
                                        ${product.price.toFixed(2)}
                                      </span>
                                      <button className="flex items-center gap-1 px-3 py-1 bg-emerald-600 text-white text-xs rounded hover:bg-emerald-700 transition-colors">
                                        <ShoppingCart className="h-3 w-3" />
                                        Add to Cart
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Quick Actions */}
                          {msg.quick_actions && msg.quick_actions.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {msg.quick_actions.map((action, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => handleQuickAction(action.label)}
                                  className="px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-sm hover:bg-emerald-100 transition-colors"
                                >
                                  {action.label}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="px-6 py-4 border-t border-zinc-200">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 bg-zinc-50 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !newMessage.trim()}
                  className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <Send className="h-4 w-4" />
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-zinc-900 mb-2">Select a user to start chatting</h3>
              <p className="text-sm text-zinc-600">
                Choose a customer from the sidebar to view their history and continue the conversation
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveChat;