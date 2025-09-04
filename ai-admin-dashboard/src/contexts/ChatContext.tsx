import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface BudtenderPersonality {
  id: string;
  name: string;
  avatar: string;
  tagline: string;
  style: string;
  greeting: string;
}

interface Product {
  id: number;
  name: string;
  brand: string;
  category: string;
  price: number;
  thc?: number;
  cbd?: number;
  image_url?: string;
}

interface QuickAction {
  id: string;
  label: string;
  value: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'info';
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  products?: Product[];
  quickActions?: QuickAction[];
  metadata?: {
    processingTime?: number;
    confidence?: number;
    intent?: string;
    budtender?: string;
  };
}

interface CustomerProfile {
  customerId: string;
  name: string;
  phone?: string;
  email?: string;
  preferences: {
    strainType?: string;
    effects?: string[];
    priceRange?: string;
  };
  context: string;
}

interface ChatContextType {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  selectedBudtender: BudtenderPersonality | null;
  setSelectedBudtender: React.Dispatch<React.SetStateAction<BudtenderPersonality | null>>;
  customerProfile: CustomerProfile;
  setCustomerProfile: React.Dispatch<React.SetStateAction<CustomerProfile>>;
  isIdentified: boolean;
  setIsIdentified: React.Dispatch<React.SetStateAction<boolean>>;
  sessionId: string;
  clearConversation: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  // Load persisted state from localStorage
  const loadPersistedState = () => {
    try {
      const savedMessages = localStorage.getItem('chat_messages');
      const savedCustomerProfile = localStorage.getItem('chat_customer_profile');
      const savedBudtender = localStorage.getItem('chat_budtender');
      const savedIdentified = localStorage.getItem('chat_identified');
      const savedSessionId = localStorage.getItem('chat_session_id');
      
      return {
        messages: savedMessages ? JSON.parse(savedMessages, (key, value) => {
          if (key === 'timestamp') return new Date(value);
          return value;
        }) : [],
        customerProfile: savedCustomerProfile ? JSON.parse(savedCustomerProfile) : {
          customerId: '',
          name: '',
          preferences: {},
          context: 'New customer'
        },
        budtender: savedBudtender ? JSON.parse(savedBudtender) : null,
        isIdentified: savedIdentified === 'true',
        sessionId: savedSessionId || `session_${Date.now()}`
      };
    } catch (error) {
      console.error('Error loading persisted chat state:', error);
      return {
        messages: [],
        customerProfile: {
          customerId: '',
          name: '',
          preferences: {},
          context: 'New customer'
        },
        budtender: null,
        isIdentified: false,
        sessionId: `session_${Date.now()}`
      };
    }
  };

  const initialState = loadPersistedState();
  
  const [messages, setMessages] = useState<Message[]>(initialState.messages);
  const [selectedBudtender, setSelectedBudtender] = useState<BudtenderPersonality | null>(initialState.budtender);
  const [customerProfile, setCustomerProfile] = useState<CustomerProfile>(initialState.customerProfile);
  const [isIdentified, setIsIdentified] = useState(initialState.isIdentified);
  const [sessionId] = useState(initialState.sessionId);

  // Persist state changes to localStorage
  useEffect(() => {
    localStorage.setItem('chat_messages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem('chat_customer_profile', JSON.stringify(customerProfile));
  }, [customerProfile]);

  useEffect(() => {
    if (selectedBudtender) {
      localStorage.setItem('chat_budtender', JSON.stringify(selectedBudtender));
    }
  }, [selectedBudtender]);

  useEffect(() => {
    localStorage.setItem('chat_identified', String(isIdentified));
  }, [isIdentified]);

  useEffect(() => {
    localStorage.setItem('chat_session_id', sessionId);
  }, [sessionId]);

  const clearConversation = () => {
    setMessages([]);
    setIsIdentified(false);
    setCustomerProfile({
      customerId: '',
      name: '',
      preferences: {},
      context: 'New customer'
    });
    
    // Clear localStorage
    localStorage.removeItem('chat_messages');
    localStorage.removeItem('chat_customer_profile');
    localStorage.removeItem('chat_budtender');
    localStorage.removeItem('chat_identified');
    // Keep session ID for tracking
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        selectedBudtender,
        setSelectedBudtender,
        customerProfile,
        setCustomerProfile,
        isIdentified,
        setIsIdentified,
        sessionId,
        clearConversation
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}