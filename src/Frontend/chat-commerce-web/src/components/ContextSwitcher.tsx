import React, { useState, useEffect } from 'react';
import { unifiedAuthApi, UserContext } from '../services/unifiedAuth';

interface ContextSwitcherProps {
  onContextChange?: (newContext: 'customer' | 'admin') => void;
}

const ContextSwitcher: React.FC<ContextSwitcherProps> = ({ onContextChange }) => {
  const [currentContext, setCurrentContext] = useState<'customer' | 'admin' | null>(null);
  const [availableContexts, setAvailableContexts] = useState<UserContext[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    // Load current context and available contexts
    const current = unifiedAuthApi.getCurrentContext();
    const contexts = unifiedAuthApi.getStoredContexts();
    
    setCurrentContext(current);
    setAvailableContexts(contexts);
  }, []);

  const handleContextSwitch = async (targetContext: 'customer' | 'admin') => {
    if (targetContext === currentContext) {
      setShowDropdown(false);
      return;
    }

    setIsLoading(true);
    try {
      await unifiedAuthApi.switchContext(targetContext);
      setCurrentContext(targetContext);
      onContextChange?.(targetContext);
      setShowDropdown(false);
      
      // Reload the page to apply new context
      window.location.reload();
    } catch (error) {
      console.error('Failed to switch context:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Don't show if user doesn't have multiple contexts
  if (availableContexts.length <= 1) {
    return null;
  }

  const getCurrentContextInfo = () => {
    const context = availableContexts.find(ctx => ctx.type === currentContext);
    return context;
  };

  const contextInfo = getCurrentContextInfo();

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        disabled={isLoading}
        className="flex items-center space-x-2 px-4 py-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg hover:bg-white/20 transition-all duration-200"
      >
        <div className="flex items-center space-x-2">
          {/* Context Icon */}
          {currentContext === 'admin' ? (
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          )}
          
          <div className="text-left">
            <div className="text-xs text-gray-400">Mode</div>
            <div className="text-sm font-medium text-white">
              {currentContext === 'admin' ? 'Admin' : 'Customer'}
            </div>
          </div>
        </div>
        
        {/* Dropdown Arrow */}
        <svg 
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-white/95 backdrop-blur-xl rounded-xl shadow-2xl border border-gray-200 overflow-hidden z-50">
          <div className="p-3 bg-gradient-to-r from-green-50 to-purple-50 border-b border-gray-200">
            <p className="text-xs font-medium text-gray-600">Switch Context</p>
          </div>
          
          {availableContexts.map((context) => (
            <button
              key={context.type}
              onClick={() => handleContextSwitch(context.type)}
              disabled={isLoading || context.type === currentContext}
              className={`w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
                context.type === currentContext ? 'bg-gray-50' : ''
              }`}
            >
              <div className="flex items-center space-x-3">
                {/* Context Icon */}
                {context.type === 'admin' ? (
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                ) : (
                  <div className="p-2 bg-green-100 rounded-lg">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                    </svg>
                  </div>
                )}
                
                <div className="text-left">
                  <p className="font-medium text-gray-900">
                    {context.type === 'admin' ? 'Admin Mode' : 'Shopping Mode'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {context.type === 'admin' 
                      ? `${context.role.replace('_', ' ')} privileges`
                      : 'Browse and purchase products'
                    }
                  </p>
                </div>
              </div>
              
              {context.type === currentContext && (
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
          
          {contextInfo && contextInfo.permissions.length > 0 && (
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
              <p className="text-xs font-medium text-gray-600 mb-2">Current Permissions</p>
              <div className="flex flex-wrap gap-1">
                {contextInfo.permissions.slice(0, 3).map((perm, idx) => (
                  <span 
                    key={idx}
                    className="px-2 py-1 text-xs bg-white rounded-md text-gray-600 border border-gray-200"
                  >
                    {perm.replace('.', ' ')}
                  </span>
                ))}
                {contextInfo.permissions.length > 3 && (
                  <span className="px-2 py-1 text-xs bg-gray-100 rounded-md text-gray-500">
                    +{contextInfo.permissions.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContextSwitcher;