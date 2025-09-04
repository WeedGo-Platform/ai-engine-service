import React, { useState, useEffect, useRef } from 'react';
import { Send, Cpu, Zap, Download, RefreshCw, Activity, FolderOpen, FileText, GitCompare, Loader2, CheckCircle2, Copy, Check } from 'lucide-react';

interface Model {
  name: string;
  path: string;
  size_gb: number;
  loaded: boolean;
  prompts_loaded?: boolean;
  prompt_folder?: string;
}

interface Message {
  role: 'user' | 'assistant' | 'system' | 'comparison';
  content: string;
  timestamp: Date;
  model?: string;
  time_ms?: number;
  tokens?: number;
  tokens_per_sec?: number;
  error?: string;
  used_prompt?: boolean;
  prompt_template?: string;
  loaded_prompts_count?: number;
  loaded_files?: string[];
  comparison_data?: any;
}

interface PromptFolder {
  path: string;
  files: string[];
}

const ModelTestChat: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingModel, setLoadingModel] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(512);
  const [topP, setTopP] = useState(0.95);
  const [topK, setTopK] = useState(40);
  
  // Prompt configuration state
  const [basePromptFolder, setBasePromptFolder] = useState<string>('');
  const [agentFolder, setAgentFolder] = useState<string>('');
  const [personalityFile, setPersonalityFile] = useState<string>('');
  
  const [availableFolders, setAvailableFolders] = useState<PromptFolder[]>([]);
  const [availablePersonalities, setAvailablePersonalities] = useState<string[]>([]);
  const [loadedPrompts, setLoadedPrompts] = useState<Record<string, string[]>>({});
  const [selectedPromptType, setSelectedPromptType] = useState<string>('');
  const [compareMode, setCompareMode] = useState(false);
  const [promptsInfo, setPromptsInfo] = useState<{count: number, files: string[]}>({count: 0, files: []});
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchModels();
    fetchAvailableFolders();
    const timeoutId = setTimeout(() => {
      connectWebSocket();
    }, 100);
    
    return () => {
      clearTimeout(timeoutId);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update available personalities when agent folder changes
  useEffect(() => {
    if (agentFolder) {
      // Look for personality folder within the selected agent folder
      const personalityPath = `${agentFolder}/personality`;
      fetchPersonalitiesForAgent(personalityPath);
    } else {
      setAvailablePersonalities([]);
      setPersonalityFile('');
    }
  }, [agentFolder]);

  const fetchModels = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/v1/test-engine/models');
      const data = await response.json();
      setModels(data.models);
      if (data.current_model) {
        setCurrentModel(data.current_model);
        setSelectedModel(data.current_model);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchLoadedPrompts = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/v1/test-engine/prompts');
      const data = await response.json();
      if (data.prompts) {
        setLoadedPrompts(data.prompts);
        setPromptsInfo({count: data.count || 0, files: Object.keys(data.prompts)});
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    }
  };

  const fetchAvailableFolders = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/v1/test-engine/prompt-folders');
      const data = await response.json();
      if (data.folders) {
        setAvailableFolders(data.folders.filter((f: any) => typeof f === 'object'));
      }
    } catch (error) {
      console.error('Failed to fetch folders:', error);
    }
  };

  const fetchPersonalitiesForAgent = async (personalityPath: string) => {
    try {
      // Fetch the personality files for the selected agent
      const response = await fetch('http://localhost:5024/api/v1/test-engine/prompt-folders');
      const data = await response.json();
      if (data.folders) {
        const personalityFolder = data.folders.find((f: any) => 
          typeof f === 'object' && f.path === personalityPath
        );
        if (personalityFolder && personalityFolder.files) {
          // Filter for JSON files and store full paths
          const personalities = personalityFolder.files
            .filter((f: string) => f.endsWith('.json'))
            .map((f: string) => `${personalityPath}/${f}`);
          setAvailablePersonalities(personalities);
        } else {
          setAvailablePersonalities([]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch personalities:', error);
      setAvailablePersonalities([]);
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    
    const ws = new WebSocket('ws://localhost:5024/api/v1/test-engine/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      ws.send(JSON.stringify({ action: 'list_models' }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'models_list') {
        setModels(data.models);
        setCurrentModel(data.current);
      } else if (data.type === 'model_loaded') {
        setLoadingModel(false);
        if (data.success) {
          setCurrentModel(data.model);
          
          // Use backend data to determine actual loaded status
          const promptsLoaded = data.prompts_loaded || false;
          const promptFolder = data.prompt_folder;
          
          // Build configuration status from backend response
          let configStatus = [];
          if (basePromptFolder) configStatus.push(`System: ${basePromptFolder.split('/').pop()}`);
          if (agentFolder) configStatus.push(`Agent: ${agentFolder.split('/').pop()}`);
          if (personalityFile) configStatus.push(`Personality: ${personalityFile.split('/').pop()?.replace('.json', '')}`);
          
          // Determine the actual load status
          let loadMsg;
          if (promptsLoaded && configStatus.length > 0) {
            loadMsg = `✓ Model ${data.model} loaded with prompts\nConfiguration: ${configStatus.join(' | ')}`;
            if (promptFolder) {
              loadMsg += `\nPrompts folder: ${promptFolder}`;
            }
          } else if (promptsLoaded) {
            loadMsg = `✓ Model ${data.model} loaded with prompts`;
            if (promptFolder) {
              loadMsg += ` from ${promptFolder}`;
            }
          } else {
            loadMsg = `✓ Model ${data.model} loaded (raw mode - no prompts)`;
          }
          
          addSystemMessage(loadMsg);
          
          fetchModels();
          // Fetch prompts based on backend response
          if (promptsLoaded) {
            fetchLoadedPrompts();
            // Also send explicit request for loaded prompts info
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ action: 'get_loaded_prompts' }));
            }
          } else {
            setPromptsInfo({count: 0, files: []});
            setLoadedPrompts({});
          }
        } else {
          addSystemMessage(`Failed to load model ${data.model}`);
        }
      } else if (data.type === 'prompts_loaded' || data.type === 'loaded_prompts_info') {
        setLoadedPrompts(data.prompts);
        const fileList = data.prompts ? Object.keys(data.prompts) : [];
        const promptCount = data.count || (data.prompts ? Object.values(data.prompts).flat().length : 0);
        
        if (fileList.length > 0) {
          setPromptsInfo({count: promptCount, files: fileList});
          addSystemMessage(`Loaded ${promptCount} prompts from ${fileList.length} JSON files:\n${fileList.map(f => `• ${f}`).join('\n')}`);
        }
      } else if (data.type === 'response') {
        setLoading(false);
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.text || data.error || 'No response',
          timestamp: new Date(),
          model: data.model,
          time_ms: data.time_ms,
          tokens: data.tokens,
          tokens_per_sec: data.tokens_per_sec,
          error: data.error,
          used_prompt: data.used_prompt,
          prompt_template: data.prompt_template,
          loaded_prompts_count: data.loaded_prompts_count,
          loaded_files: data.loaded_files
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else if (data.type === 'comparison') {
        setLoading(false);
        const comparisonMessage: Message = {
          role: 'comparison',
          content: '',
          timestamp: new Date(),
          comparison_data: data
        };
        setMessages(prev => [...prev, comparisonMessage]);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        addSystemMessage('WebSocket connection error');
      }
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket disconnected');
      if (wsRef.current === ws) {
        wsRef.current = null;
        setTimeout(() => {
          if (!wsRef.current) {
            connectWebSocket();
          }
        }, 3000);
      }
    };
    
    wsRef.current = ws;
  };

  const addSystemMessage = (content: string) => {
    const systemMessage: Message = {
      role: 'system',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const loadModel = async () => {
    if (!selectedModel) {
      addSystemMessage('Please select a model first');
      return;
    }
    
    // Validate personality selection
    if (personalityFile && !agentFolder) {
      addSystemMessage('Error: Personality requires an agent to be selected');
      return;
    }
    
    setLoadingModel(true);
    const loadingDetails = [];
    let configDescription = '';
    
    // Build configuration description
    if (basePromptFolder && agentFolder && personalityFile) {
      configDescription = 'System + Agent + Personality';
      loadingDetails.push('system prompts', 'agent prompts', 'personality');
    } else if (basePromptFolder && agentFolder) {
      configDescription = 'System + Agent';
      loadingDetails.push('system prompts', 'agent prompts');
    } else if (agentFolder && personalityFile) {
      configDescription = 'Agent + Personality (no system)';
      loadingDetails.push('agent prompts', 'personality');
    } else if (basePromptFolder) {
      configDescription = 'System prompts only';
      loadingDetails.push('system prompts');
    } else if (agentFolder) {
      configDescription = 'Agent only (no system)';
      loadingDetails.push('agent prompts');
    } else {
      configDescription = 'Raw mode (no prompts)';
    }
    
    const loadingMsg = `Loading ${selectedModel} - ${configDescription}`;
    addSystemMessage(loadingMsg);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'load_model',
        model: selectedModel,
        base_folder: basePromptFolder || null,
        role_folder: agentFolder || null,  // Backend expects role_folder parameter
        personality_file: personalityFile || null
      }));
    } else {
      try {
        const response = await fetch('http://localhost:5024/api/v1/test-engine/load', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            model_name: selectedModel,
            base_folder: basePromptFolder || null,
            role_folder: agentFolder || null,  // Backend expects role_folder parameter
            personality_file: personalityFile || null
          })
        });
        
        const data = await response.json();
        setLoadingModel(false);
        
        if (response.ok) {
          setCurrentModel(selectedModel);
          const successMsg = `✓ Loaded: ${configDescription}\n${data.message}`;
          addSystemMessage(successMsg);
          fetchModels();
          if (basePromptFolder || agentFolder || personalityFile) {
            fetchLoadedPrompts();
          }
        } else {
          addSystemMessage(`Failed to load model: ${data.detail}`);
        }
      } catch (error) {
        setLoadingModel(false);
        addSystemMessage(`Error loading model: ${error}`);
      }
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !currentModel) return;
    
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      if (compareMode) {
        wsRef.current.send(JSON.stringify({
          action: 'compare',
          user_input: input,
          prompt_type: selectedPromptType || undefined
        }));
      } else {
        wsRef.current.send(JSON.stringify({
          action: 'generate',
          prompt: input,
          prompt_type: selectedPromptType || undefined,
          max_tokens: maxTokens,
          temperature,
          top_p: topP,
          top_k: topK
        }));
      }
    }
  };

  const benchmarkModel = async () => {
    if (!currentModel) return;
    
    try {
      const params = new URLSearchParams();
      if (basePromptFolder || agentFolder || personalityFile) {
        params.append('with_prompts', 'true');
        if (basePromptFolder) params.append('prompt_folder', basePromptFolder);
      }
      
      addSystemMessage(`Starting benchmark for ${currentModel}...`);
      const response = await fetch(`http://localhost:5024/api/v1/test-engine/benchmark/${currentModel}?${params}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (response.ok) {
        let benchmarkResults = `Benchmark Results for ${currentModel}:\n`;
        benchmarkResults += `Average Response Time: ${data.avg_time_ms}ms\n`;
        benchmarkResults += `Average Tokens/Sec: ${data.avg_tokens_per_sec}\n\n`;
        
        data.tests.forEach((test: any, index: number) => {
          benchmarkResults += `Test ${index + 1}:\n`;
          benchmarkResults += `  Prompt: ${test.prompt}\n`;
          if (test.prompt_type) {
            benchmarkResults += `  Template: ${test.prompt_type}\n`;
          }
          benchmarkResults += `  Response: ${test.response}\n`;
          benchmarkResults += `  Time: ${test.time_ms}ms\n`;
          benchmarkResults += `  Tokens/Sec: ${test.tokens_per_sec}\n\n`;
        });
        
        addSystemMessage(benchmarkResults);
      } else {
        addSystemMessage(`Benchmark failed: ${data.detail}`);
      }
    } catch (error) {
      addSystemMessage(`Benchmark error: ${error}`);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const copyChat = () => {
    // Format messages for copying
    const chatText = messages.map(msg => {
      let prefix = '';
      if (msg.role === 'user') prefix = 'User: ';
      else if (msg.role === 'assistant') prefix = 'Assistant: ';
      else if (msg.role === 'system') prefix = 'System: ';
      else if (msg.role === 'comparison') {
        // Format comparison messages
        const without = msg.comparison_data?.without_prompts?.text || '';
        const withPrompts = msg.comparison_data?.with_prompts?.text || '';
        return `--- Comparison ---\nWithout Prompts:\n${without}\n\nWith Prompts (${msg.comparison_data?.with_prompts?.prompt_template || 'N/A'}):\n${withPrompts}\n---`;
      }
      
      // Add metadata if available
      let metadata = '';
      if (msg.time_ms) metadata += ` [${msg.time_ms}ms]`;
      if (msg.tokens_per_sec) metadata += ` [${msg.tokens_per_sec} tok/s]`;
      if (msg.prompt_template) metadata += ` [Template: ${msg.prompt_template}]`;
      
      return prefix + msg.content + metadata;
    }).join('\n\n');
    
    // Copy to clipboard
    navigator.clipboard.writeText(chatText).then(() => {
      setCopiedToClipboard(true);
      setTimeout(() => setCopiedToClipboard(false), 2000);
    }).catch(err => {
      console.error('Failed to copy:', err);
      addSystemMessage('Failed to copy chat to clipboard');
    });
  };

  // Get all available prompt types with unique keys
  const allPromptTypes = Object.entries(loadedPrompts).flatMap(([file, prompts]) =>
    prompts.map(prompt => ({ 
      value: prompt, 
      label: `${prompt} (${file})`,
      key: `${file}-${prompt}` // Unique key combining file and prompt
    }))
  );

  const hasPromptsLoaded = basePromptFolder || agentFolder || personalityFile;

  return (
    <div className="flex h-full">
      {/* Configuration Sidebar */}
      <div className="w-96 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div className="p-4 space-y-4">
          <h3 className="text-lg font-semibold mb-4">Model Configuration</h3>
          
          {/* Model Selection */}
          <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Model Selection
            </h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Select Model
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-lg text-sm"
                  disabled={loadingModel}
                >
                  <option value="">Choose a model...</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name} ({model.size_gb} GB) {model.loaded && '✓'}
                    </option>
                  ))}
                </select>
              </div>
              
              {currentModel && (
                <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Current: {currentModel}
                </div>
              )}
            </div>
          </div>
          
          {/* Prompt Configuration */}
          <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Prompt Configuration
            </h4>
            
            <div className="space-y-3">
              {/* System Configuration */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  1. System Configuration
                </label>
                <select
                  value={basePromptFolder}
                  onChange={(e) => setBasePromptFolder(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-lg text-sm"
                >
                  <option value="">No system configuration</option>
                  {availableFolders
                    .filter(f => f.path === 'prompts/system') // System configuration folder
                    .map((folder) => (
                      <option key={folder.path} value={folder.path}>
                        System Configuration ({folder.files.join(', ')})
                      </option>
                    ))}
                </select>
              </div>
              
              {/* Agent Selection (Role Prompts) */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  2. Agent Selection
                </label>
                <select
                  value={agentFolder}
                  onChange={(e) => setAgentFolder(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-lg text-sm"
                >
                  <option value="">No agent selected</option>
                  {availableFolders
                    .filter(f => f.path.startsWith('prompts/agents/') && 
                             !f.path.includes('/personality') &&
                             f.path.split('/').length === 3) // Only direct agent folders
                    .map((folder) => {
                      const agentName = folder.path.split('/').pop();
                      return (
                        <option key={folder.path} value={folder.path}>
                          {agentName}
                        </option>
                      );
                    })}
                </select>
              </div>
              
              {/* Personality */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  3. Personality
                </label>
                <select
                  value={personalityFile}
                  onChange={(e) => setPersonalityFile(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-lg text-sm"
                  disabled={!agentFolder}
                >
                  <option value="">No personality</option>
                  {availablePersonalities.map((personality) => {
                    const fileName = personality.split('/').pop()?.replace('.json', '') || '';
                    return (
                      <option key={personality} value={personality}>
                        {fileName}
                      </option>
                    );
                  })}
                </select>
              </div>
              
              {/* Configuration Summary */}
              {(basePromptFolder || agentFolder || personalityFile) && (
                <div className="text-xs bg-blue-50 dark:bg-blue-900/20 rounded p-2 space-y-1">
                  <div className="font-medium">Configuration Preview:</div>
                  {basePromptFolder && <div>• System: {basePromptFolder.split('/').pop()}</div>}
                  {agentFolder && <div>• Agent: {agentFolder.split('/').pop()}</div>}
                  {personalityFile && <div>• Personality: {personalityFile.split('/').pop()?.replace('.json', '')}</div>}
                  {!basePromptFolder && agentFolder && <div className="text-yellow-600 dark:text-yellow-400">⚠ No system prompts (agent-only mode)</div>}
                </div>
              )}
              
              {/* Load Button */}
              <button
                onClick={loadModel}
                disabled={!selectedModel || loadingModel || (personalityFile && !agentFolder)}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loadingModel ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Load Configuration
                  </>
                )}
              </button>
              
              {promptsInfo.count > 0 && (
                <div className="text-xs text-green-600 dark:text-green-400 p-2 bg-green-50 dark:bg-green-900/20 rounded">
                  <div className="font-medium">✓ {promptsInfo.count} prompts loaded from {promptsInfo.files.length} JSON files:</div>
                  <div className="mt-1 text-[10px] opacity-90">
                    {promptsInfo.files.map((file, idx) => (
                      <div key={idx}>• {file}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Interaction Options */}
          <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
            <h4 className="text-sm font-semibold mb-3">Interaction Options</h4>
            
            <div className="space-y-2">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Prompt Type (for responses)
                </label>
                <select
                  value={selectedPromptType}
                  onChange={(e) => setSelectedPromptType(e.target.value)}
                  className="w-full px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-sm"
                >
                  <option value="">Auto-detect</option>
                  <option value="greeting_response">Greeting</option>
                  <option value="general_conversation">General</option>
                  <option value="product_search">Product Search</option>
                  {allPromptTypes.map(({ value, label, key }) => (
                    <option key={key} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={compareMode}
                  onChange={(e) => setCompareMode(e.target.checked)}
                  className="rounded text-blue-500"
                />
                <GitCompare className="w-3 h-3" />
                Compare Mode
              </label>
              
              <button
                onClick={benchmarkModel}
                disabled={!currentModel || loadingModel}
                className="w-full px-3 py-1.5 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 disabled:opacity-50"
              >
                <Activity className="w-3 h-3 inline mr-1" />
                Run Benchmark
              </button>
            </div>
          </div>
          
          {/* Generation Parameters */}
          <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
            <h4 className="text-sm font-semibold mb-3">Generation Parameters</h4>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-600 dark:text-gray-400">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 dark:text-gray-400">
                  Max Tokens: {maxTokens}
                </label>
                <input
                  type="range"
                  min="50"
                  max="2000"
                  step="50"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold">Model Test Chat</h2>
            {currentModel && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Model: <span className="font-medium">{currentModel}</span>
                {hasPromptsLoaded && <span className="ml-2 text-blue-600">(with prompts)</span>}
                {compareMode && <span className="ml-2 text-purple-600">(compare mode)</span>}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={copyChat}
              className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center gap-1"
              disabled={messages.length === 0}
            >
              {copiedToClipboard ? (
                <>
                  <Check className="w-4 h-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Chat
                </>
              )}
            </button>
            <button
              onClick={clearChat}
              className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              <RefreshCw className="w-4 h-4 inline mr-1" />
              Clear Chat
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[calc(100vh-16rem)]">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
              {currentModel ? (
                <div>
                  <Cpu className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Model {currentModel} is ready</p>
                  <p className="text-sm mt-2">
                    {compareMode ? 'Compare mode enabled - responses will show with/without prompts' : 
                     hasPromptsLoaded ? (
                       <>
                         Configuration: 
                         {basePromptFolder && ' System'}
                         {agentFolder && ` + ${agentFolder.split('/').pop()}`}
                         {personalityFile && ` + ${personalityFile.split('/').pop()?.replace('.json', '')}`}
                       </>
                     ) : 'Raw mode - no prompt templates'}
                  </p>
                  <p className="text-xs mt-2 text-blue-500">
                    Tip: Type "list prompts" to see all loaded prompts
                  </p>
                </div>
              ) : (
                <div>
                  <Cpu className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>No model loaded</p>
                  <p className="text-sm mt-2">Configure and load a model to start</p>
                </div>
              )}
            </div>
          )}
          
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'comparison' ? (
                // Render comparison results
                <div className="max-w-4xl w-full">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
                      <h4 className="font-semibold mb-2 text-sm">Without Prompts</h4>
                      <div className="whitespace-pre-wrap text-sm">
                        {message.comparison_data?.without_prompts?.text || 'Error'}
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        {message.comparison_data?.without_prompts?.time_ms}ms
                        {message.comparison_data?.without_prompts?.tokens_per_sec && 
                          ` • ${message.comparison_data.without_prompts.tokens_per_sec} tok/s`}
                      </div>
                    </div>
                    <div className="bg-blue-100 dark:bg-blue-900/20 rounded-lg p-4">
                      <h4 className="font-semibold mb-2 text-sm">
                        With Prompts
                        {message.comparison_data?.with_prompts?.prompt_template && 
                          ` (${message.comparison_data.with_prompts.prompt_template})`}
                      </h4>
                      <div className="whitespace-pre-wrap text-sm">
                        {message.comparison_data?.with_prompts?.text || 'Error'}
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        {message.comparison_data?.with_prompts?.time_ms}ms
                        {message.comparison_data?.with_prompts?.tokens_per_sec && 
                          ` • ${message.comparison_data.with_prompts.tokens_per_sec} tok/s`}
                        {message.comparison_data?.time_difference_pct !== undefined && 
                          ` • ${message.comparison_data.time_difference_pct > 0 ? '+' : ''}${message.comparison_data.time_difference_pct}%`}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  className={`max-w-3xl px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : message.role === 'system'
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  {message.time_ms !== undefined && (
                    <div className="mt-2 text-xs opacity-75 flex items-center gap-3">
                      <span>
                        <Zap className="w-3 h-3 inline mr-1" />
                        {message.time_ms}ms
                      </span>
                      {message.tokens_per_sec && (
                        <span>{message.tokens_per_sec} tokens/sec</span>
                      )}
                      {message.prompt_template && (
                        <span>Template: {message.prompt_template}</span>
                      )}
                      {message.loaded_prompts_count !== undefined && message.loaded_prompts_count > 0 && (
                        <span className="text-green-400">📝 {message.loaded_prompts_count} prompts active</span>
                      )}
                    </div>
                  )}
                  {message.error && (
                    <div className="mt-2 text-xs text-red-300">
                      Error: {message.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 dark:border-gray-100"></div>
                  <span>{compareMode ? 'Comparing...' : 'Generating...'}</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder={
                currentModel 
                  ? compareMode 
                    ? "Type to compare with/without prompts..." 
                    : "Type your message..." 
                  : "Load a model first..."
              }
              disabled={!currentModel || loading}
              className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={!currentModel || loading || !input.trim()}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelTestChat;