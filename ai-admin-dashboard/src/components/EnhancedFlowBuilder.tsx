import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  type Node,
  type Edge,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  type NodeChange,
  type EdgeChange,
  type Connection,
  Controls,
  Background,
  MiniMap,
  Panel,
  type NodeTypes,
  Handle,
  Position,
  useReactFlow,
  MarkerType,
  BackgroundVariant
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  Play, 
  Save, 
  Download, 
  Upload, 
  Plus, 
  Settings, 
  Eye,
  TestTube,
  Brain,
  MessageSquare,
  GitBranch,
  Clock,
  Database,
  User,
  Package,
  BarChart,
  Globe,
  Repeat,
  Zap,
  ChevronRight,
  X,
  Copy,
  Trash2,
  Edit3,
  HelpCircle,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';

// Enhanced node type definitions
interface FlowVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  value?: any;
  scope: 'global' | 'local';
}

interface NodeData {
  label: string;
  description?: string;
  icon?: string;
  config?: any;
  variables?: FlowVariable[];
  aiPersonality?: string;
  validation?: any;
  analytics?: {
    trackEvent?: string;
    metrics?: string[];
  };
}

// Custom enhanced node components
function AIIntentNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl p-4 min-w-[240px] shadow-xl ${selected ? 'ring-4 ring-purple-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Brain className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 mb-2">{data.description || 'AI analyzes customer intent'}</div>
      {data.config?.intents && (
        <div className="text-xs bg-white/20 rounded p-2">
          Detects: {data.config.intents.join(', ')}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function ProductSearchNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl p-4 min-w-[240px] shadow-xl ${selected ? 'ring-4 ring-green-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Package className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 mb-2">
        {data.config?.searchType || 'AI-powered search'}
      </div>
      {data.config?.filters && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(data.config.filters).map(([key, value]: [string, any]) => (
            <span key={key} className="text-xs bg-white/20 rounded px-2 py-1">
              {key}: {value}
            </span>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function LoopNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl p-4 min-w-[220px] shadow-xl ${selected ? 'ring-4 ring-orange-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Repeat className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90">
        {data.config?.condition || 'Loop condition'}
      </div>
      <div className="text-xs mt-2 bg-white/20 rounded px-2 py-1">
        Max: {data.config?.maxIterations || 10}
      </div>
      <Handle type="source" position={Position.Right} id="loop" className="w-3 h-3" />
      <Handle type="source" position={Position.Bottom} id="continue" className="w-3 h-3" />
    </div>
  );
}

function PersonalitySwitchNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl p-4 min-w-[240px] shadow-xl ${selected ? 'ring-4 ring-indigo-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <User className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 mb-2">
        Switch to: {data.config?.personality || 'Default'}
      </div>
      {data.config?.reason && (
        <div className="text-xs bg-white/20 rounded p-2">
          {data.config.reason}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function DataCollectionNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl p-4 min-w-[260px] shadow-xl ${selected ? 'ring-4 ring-blue-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Database className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="space-y-1">
        {data.config?.fields?.map((field: any, idx: number) => (
          <div key={idx} className="text-xs bg-white/20 rounded px-2 py-1 flex justify-between">
            <span>{field.name}</span>
            <span className="opacity-75">{field.type}</span>
          </div>
        ))}
      </div>
      {data.config?.validation && (
        <div className="text-xs mt-2 text-yellow-200">
          ✓ Validation enabled
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function WaitNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-xl p-4 min-w-[200px] shadow-xl ${selected ? 'ring-4 ring-gray-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Clock className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90">
        Wait: {data.config?.duration || 1}s
      </div>
      {data.config?.showTyping && (
        <div className="text-xs mt-2">Shows typing indicator</div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function AnalyticsNode({ data, selected }: any) {
  return (
    <div className={`bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl p-4 min-w-[220px] shadow-xl ${selected ? 'ring-4 ring-pink-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <BarChart className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 mb-2">
        Event: {data.config?.event || 'custom_event'}
      </div>
      {data.config?.metrics && (
        <div className="text-xs space-y-1">
          {data.config.metrics.map((metric: string, idx: number) => (
            <div key={idx} className="bg-white/20 rounded px-2 py-1">
              📊 {metric}
            </div>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

// Enhanced node types mapping
const nodeTypes: NodeTypes = {
  aiIntent: AIIntentNode,
  productSearch: ProductSearchNode,
  loop: LoopNode,
  personalitySwitch: PersonalitySwitchNode,
  dataCollection: DataCollectionNode,
  wait: WaitNode,
  analytics: AnalyticsNode,
  // Keep existing basic nodes
  start: StartNode,
  question: QuestionNode,
  condition: ConditionNode,
  action: ActionNode,
  response: ResponseNode,
  end: EndNode
};

// Keep existing basic node components (StartNode, QuestionNode, etc.)
function StartNode({ data }: any) {
  return (
    <div className="bg-green-500 text-white rounded-xl p-4 min-w-[150px] shadow-xl">
      <div className="text-center font-bold flex items-center justify-center gap-2">
        <Play className="w-5 h-5" />
        {data.label}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function QuestionNode({ data, selected }: any) {
  return (
    <div className={`bg-blue-500 text-white rounded-xl p-4 min-w-[240px] shadow-xl ${selected ? 'ring-4 ring-blue-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 mb-2">{data.question}</div>
      {data.variable && (
        <div className="text-xs bg-blue-600 rounded px-2 py-1 inline-block">
          → {data.variable}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function ConditionNode({ data, selected }: any) {
  return (
    <div className={`bg-yellow-500 text-white rounded-xl p-4 min-w-[200px] shadow-xl ${selected ? 'ring-4 ring-yellow-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <GitBranch className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90">if: {data.condition}</div>
      <div className="flex justify-between mt-2 text-xs">
        <span className="bg-green-600 rounded px-2 py-1">Yes</span>
        <span className="bg-red-600 rounded px-2 py-1">No</span>
      </div>
      <Handle type="source" position={Position.Bottom} id="yes" className="w-3 h-3 left-1/4" />
      <Handle type="source" position={Position.Bottom} id="no" className="w-3 h-3 left-3/4" />
    </div>
  );
}

function ActionNode({ data, selected }: any) {
  return (
    <div className={`bg-purple-500 text-white rounded-xl p-4 min-w-[200px] shadow-xl ${selected ? 'ring-4 ring-purple-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <Zap className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90">{data.action}</div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function ResponseNode({ data, selected }: any) {
  return (
    <div className={`bg-indigo-500 text-white rounded-xl p-4 min-w-[260px] shadow-xl ${selected ? 'ring-4 ring-indigo-300' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare className="w-5 h-5" />
        <span className="font-bold">{data.label}</span>
      </div>
      <div className="text-sm opacity-90 line-clamp-3">{data.template}</div>
      {data.aiPersonality && (
        <div className="text-xs mt-2 bg-white/20 rounded px-2 py-1">
          🤖 {data.aiPersonality}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

function EndNode({ data }: any) {
  return (
    <div className="bg-red-500 text-white rounded-xl p-4 min-w-[150px] shadow-xl">
      <div className="text-center font-bold flex items-center justify-center gap-2">
        <CheckCircle className="w-5 h-5" />
        {data.label}
      </div>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
    </div>
  );
}

export default function EnhancedFlowBuilder() {
  // Memoize node types to avoid React Flow warning
  const memoizedNodeTypes = React.useMemo(() => nodeTypes, []);
  
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showNodePanel, setShowNodePanel] = useState(false);
  const [showSimulator, setShowSimulator] = useState(false);
  const [flowVariables, setFlowVariables] = useState<FlowVariable[]>([]);
  const [testMode, setTestMode] = useState(false);
  const [currentFlowId, setCurrentFlowId] = useState<string | null>(null);
  const [flowName, setFlowName] = useState<string>('New Flow');
  const queryClient = useQueryClient();

  // Fetch conversation flows from API
  const { data: flowsData, isLoading: isLoadingFlows, error: flowsError } = useQuery({
    queryKey: ['conversation-flows'],
    queryFn: () => apiService.getConversationFlows(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  // Fetch AI personalities for personality switch nodes
  const { data: personalities, isLoading: isLoadingPersonalities } = useQuery({
    queryKey: ['ai-personalities'],
    queryFn: () => apiService.getPersonalities()
  });

  // Node configuration panel
  const NodeConfigPanel = () => {
    if (!selectedNode) return null;

    return (
      <AnimatePresence>
        {showNodePanel && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            className="absolute right-0 top-0 h-full w-96 bg-white shadow-2xl z-50 overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">Configure Node</h3>
                <button
                  onClick={() => setShowNodePanel(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Node Type</label>
                  <div className="bg-gray-100 p-3 rounded-lg font-mono text-sm">
                    {selectedNode.type}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Label</label>
                  <input
                    type="text"
                    value={selectedNode.data.label}
                    onChange={(e) => updateNodeData('label', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                {selectedNode.type === 'aiIntent' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Intents to Detect</label>
                    <div className="space-y-2">
                      {['greeting', 'product_search', 'purchase', 'support', 'general'].map(intent => (
                        <label key={intent} className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedNode.data.config?.intents?.includes(intent)}
                            onChange={(e) => {
                              const intents = selectedNode.data.config?.intents || [];
                              if (e.target.checked) {
                                updateNodeConfig('intents', [...intents, intent]);
                              } else {
                                updateNodeConfig('intents', intents.filter((i: string) => i !== intent));
                              }
                            }}
                          />
                          <span className="capitalize">{intent.replace('_', ' ')}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {selectedNode.type === 'personalitySwitch' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Select Personality</label>
                    <select
                      value={selectedNode.data.config?.personality || ''}
                      onChange={(e) => updateNodeConfig('personality', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                      disabled={isLoadingPersonalities}
                    >
                      <option value="">{isLoadingPersonalities ? 'Loading...' : 'Default'}</option>
                      {personalities?.personalities?.map((p: any) => (
                        <option key={p.id} value={p.name}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                {selectedNode.type === 'wait' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Duration (seconds)</label>
                    <input
                      type="number"
                      min="0.5"
                      max="10"
                      step="0.5"
                      value={selectedNode.data.config?.duration || 1}
                      onChange={(e) => updateNodeConfig('duration', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                    <label className="flex items-center gap-2 mt-2">
                      <input
                        type="checkbox"
                        checked={selectedNode.data.config?.showTyping || false}
                        onChange={(e) => updateNodeConfig('showTyping', e.target.checked)}
                      />
                      <span>Show typing indicator</span>
                    </label>
                  </div>
                )}

                <div className="pt-4 border-t space-y-2">
                  <button
                    onClick={() => {
                      const newNode = {
                        ...selectedNode,
                        id: `node-${Date.now()}`,
                        position: {
                          x: selectedNode.position.x + 50,
                          y: selectedNode.position.y + 50
                        }
                      };
                      setNodes(nodes => [...nodes, newNode]);
                      toast.success('Node duplicated');
                    }}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center justify-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Duplicate Node
                  </button>
                  <button
                    onClick={() => {
                      setNodes(nodes => nodes.filter(n => n.id !== selectedNode.id));
                      setEdges(edges => edges.filter(e => 
                        e.source !== selectedNode.id && e.target !== selectedNode.id
                      ));
                      setShowNodePanel(false);
                      toast.success('Node deleted');
                    }}
                    className="w-full px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete Node
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  };

  const updateNodeData = (key: string, value: any) => {
    if (!selectedNode) return;
    
    setNodes(nodes => 
      nodes.map(node => 
        node.id === selectedNode.id 
          ? { ...node, data: { ...node.data, [key]: value } }
          : node
      )
    );
    
    setSelectedNode(prev => prev ? { ...prev, data: { ...prev.data, [key]: value } } : null);
  };

  const updateNodeConfig = (key: string, value: any) => {
    if (!selectedNode) return;
    
    const newConfig = { ...(selectedNode.data.config || {}), [key]: value };
    updateNodeData('config', newConfig);
  };

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        type: 'smoothstep',
        animated: testMode,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [testMode]
  );

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
    setShowNodePanel(true);
  }, []);

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type,
      position: { x: 250, y: nodes.length * 150 },
      data: getDefaultNodeData(type)
    };
    setNodes((nds) => [...nds, newNode]);
    toast.success(`Added ${type} node`);
  };

  const getDefaultNodeData = (type: string) => {
    switch (type) {
      case 'aiIntent':
        return { 
          label: 'AI Intent Detection',
          description: 'Analyze customer intent',
          config: { intents: ['greeting', 'product_search'] }
        };
      case 'productSearch':
        return { 
          label: 'Product Search',
          config: { searchType: 'AI-powered', filters: {} }
        };
      case 'loop':
        return { 
          label: 'Loop',
          config: { condition: 'hasMoreProducts', maxIterations: 5 }
        };
      case 'personalitySwitch':
        return { 
          label: 'Switch Personality',
          config: { personality: 'Default', reason: 'Context change' }
        };
      case 'dataCollection':
        return { 
          label: 'Collect Data',
          config: { 
            fields: [
              { name: 'email', type: 'email', required: true },
              { name: 'phone', type: 'tel', required: false }
            ],
            validation: true
          }
        };
      case 'wait':
        return { 
          label: 'Wait',
          config: { duration: 1.5, showTyping: true }
        };
      case 'analytics':
        return { 
          label: 'Track Event',
          config: { 
            event: 'flow_checkpoint',
            metrics: ['conversion_rate', 'engagement_score']
          }
        };
      default:
        return getBasicNodeData(type);
    }
  };

  // Load initial flow data from API
  useEffect(() => {
    if (flowsData?.flows && flowsData.flows.length > 0 && nodes.length === 0) {
      // Load the first available flow or create a default one
      const firstFlow = flowsData.flows[0];
      if (firstFlow?.nodes && firstFlow?.edges) {
        setNodes(firstFlow.nodes || []);
        setEdges(firstFlow.edges || []);
        setCurrentFlowId(firstFlow.id);
        setFlowName(firstFlow.name || 'Conversation Flow');
        toast.success(`Loaded flow: ${firstFlow.name}`);
      } else {
        // Create default starting flow if no valid flows exist
        createDefaultFlow();
      }
    } else if (flowsData?.flows && flowsData.flows.length === 0 && nodes.length === 0) {
      // No flows exist, create a default one
      createDefaultFlow();
    }
  }, [flowsData, nodes.length]);

  const createDefaultFlow = () => {
    const defaultNodes: Node[] = [
      {
        id: 'start-1',
        type: 'start',
        position: { x: 250, y: 50 },
        data: { label: 'Start' },
      },
      {
        id: 'welcome-1',
        type: 'response',
        position: { x: 250, y: 200 },
        data: { 
          label: 'Welcome Message', 
          template: 'Welcome! How can I help you today?' 
        },
      },
      {
        id: 'end-1',
        type: 'end',
        position: { x: 250, y: 350 },
        data: { label: 'End' },
      },
    ];

    const defaultEdges: Edge[] = [
      {
        id: 'e-start-welcome',
        source: 'start-1',
        target: 'welcome-1',
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed },
      },
      {
        id: 'e-welcome-end',
        source: 'welcome-1',
        target: 'end-1',
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed },
      },
    ];

    setNodes(defaultNodes);
    setEdges(defaultEdges);
    setFlowName('Welcome Flow');
    toast.success('Created default flow');
  };

  // Save flow mutation
  const saveFlowMutation = useMutation({
    mutationFn: async (flowData: any) => {
      const payload = {
        id: currentFlowId,
        name: flowName,
        nodes,
        edges,
        variables: flowVariables,
        ...flowData,
      };
      
      if (currentFlowId) {
        // Update existing flow
        return apiService.saveConversationFlow({ ...payload, id: currentFlowId });
      } else {
        // Create new flow
        const result = await apiService.saveConversationFlow(payload);
        setCurrentFlowId(result.id);
        return result;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation-flows'] });
      toast.success('Flow saved successfully!');
    },
    onError: (error: any) => {
      console.error('Failed to save flow:', error);
      toast.error(error.message || 'Failed to save flow');
    },
  });

  const handleSaveFlow = () => {
    if (!flowName.trim()) {
      toast.error('Please enter a flow name');
      return;
    }
    
    if (nodes.length === 0) {
      toast.error('Cannot save empty flow');
      return;
    }

    saveFlowMutation.mutate({});
  };

  const getBasicNodeData = (type: string) => {
    switch (type) {
      case 'start':
        return { label: 'Start' };
      case 'question':
        return { label: 'Question', question: 'Your question here?', variable: 'variable_name' };
      case 'condition':
        return { label: 'Condition', condition: 'condition_expression' };
      case 'action':
        return { label: 'Action', action: 'action_type' };
      case 'response':
        return { label: 'Response', template: 'Response template' };
      case 'end':
        return { label: 'End' };
      default:
        return { label: 'Node' };
    }
  };

  return (
    <div className="h-full relative">
      {isLoadingFlows ? (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading conversation flows...</p>
          </div>
        </div>
      ) : flowsError ? (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 z-10">
          <div className="text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-red-600 mb-2">Failed to load flows</p>
            <p className="text-sm text-red-500 mb-4">{flowsError.message}</p>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['conversation-flows'] })}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              Retry
            </button>
          </div>
        </div>
      ) : null}
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={memoizedNodeTypes}
        fitView
        className="bg-gray-50"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <MiniMap 
          className="bg-white shadow-lg rounded-lg"
          nodeColor={(node) => {
            const colors: Record<string, string> = {
              start: '#10b981',
              end: '#ef4444',
              question: '#3b82f6',
              condition: '#eab308',
              action: '#a855f7',
              response: '#6366f1',
              aiIntent: '#ec4899',
              productSearch: '#14b8a6',
              loop: '#f97316',
              personalitySwitch: '#8b5cf6',
              dataCollection: '#06b6d4',
              wait: '#6b7280',
              analytics: '#f43f5e'
            };
            return colors[node.type || 'default'] || '#9ca3af';
          }}
        />
        <Controls className="bg-white shadow-lg rounded-lg" />
        
        <Panel position="top-left" className="bg-white shadow-lg rounded-lg p-4 space-y-4 max-w-xs">
          <h3 className="font-bold text-lg">Add Nodes</h3>
          
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-600">Basic Nodes</h4>
            <div className="grid grid-cols-3 gap-2">
              <button onClick={() => addNode('start')} className="p-2 bg-green-100 hover:bg-green-200 rounded-lg text-xs">
                <Play className="w-4 h-4 mx-auto mb-1" />
                Start
              </button>
              <button onClick={() => addNode('question')} className="p-2 bg-blue-100 hover:bg-blue-200 rounded-lg text-xs">
                <MessageSquare className="w-4 h-4 mx-auto mb-1" />
                Question
              </button>
              <button onClick={() => addNode('condition')} className="p-2 bg-yellow-100 hover:bg-yellow-200 rounded-lg text-xs">
                <GitBranch className="w-4 h-4 mx-auto mb-1" />
                Condition
              </button>
              <button onClick={() => addNode('action')} className="p-2 bg-purple-100 hover:bg-purple-200 rounded-lg text-xs">
                <Zap className="w-4 h-4 mx-auto mb-1" />
                Action
              </button>
              <button onClick={() => addNode('response')} className="p-2 bg-indigo-100 hover:bg-indigo-200 rounded-lg text-xs">
                <MessageSquare className="w-4 h-4 mx-auto mb-1" />
                Response
              </button>
              <button onClick={() => addNode('end')} className="p-2 bg-red-100 hover:bg-red-200 rounded-lg text-xs">
                <CheckCircle className="w-4 h-4 mx-auto mb-1" />
                End
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-600">AI-Powered Nodes</h4>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => addNode('aiIntent')} className="p-2 bg-pink-100 hover:bg-pink-200 rounded-lg text-xs">
                <Brain className="w-4 h-4 mx-auto mb-1" />
                AI Intent
              </button>
              <button onClick={() => addNode('productSearch')} className="p-2 bg-teal-100 hover:bg-teal-200 rounded-lg text-xs">
                <Package className="w-4 h-4 mx-auto mb-1" />
                Product Search
              </button>
              <button onClick={() => addNode('personalitySwitch')} className="p-2 bg-violet-100 hover:bg-violet-200 rounded-lg text-xs">
                <User className="w-4 h-4 mx-auto mb-1" />
                Personality
              </button>
              <button onClick={() => addNode('dataCollection')} className="p-2 bg-cyan-100 hover:bg-cyan-200 rounded-lg text-xs">
                <Database className="w-4 h-4 mx-auto mb-1" />
                Data Collection
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-600">Control Nodes</h4>
            <div className="grid grid-cols-3 gap-2">
              <button onClick={() => addNode('loop')} className="p-2 bg-orange-100 hover:bg-orange-200 rounded-lg text-xs">
                <Repeat className="w-4 h-4 mx-auto mb-1" />
                Loop
              </button>
              <button onClick={() => addNode('wait')} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-xs">
                <Clock className="w-4 h-4 mx-auto mb-1" />
                Wait
              </button>
              <button onClick={() => addNode('analytics')} className="p-2 bg-rose-100 hover:bg-rose-200 rounded-lg text-xs">
                <BarChart className="w-4 h-4 mx-auto mb-1" />
                Analytics
              </button>
            </div>
          </div>
        </Panel>

        <Panel position="top-right" className="bg-white shadow-lg rounded-lg p-4">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={flowName}
                onChange={(e) => setFlowName(e.target.value)}
                placeholder="Flow name"
                className="px-3 py-1 border rounded text-sm flex-1 min-w-[150px]"
              />
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setTestMode(!testMode)}
                className={`px-3 py-2 rounded-lg flex items-center gap-2 text-sm ${
                  testMode ? 'bg-green-500 text-white' : 'bg-gray-100'
                }`}
              >
                <TestTube className="w-4 h-4" />
                Test
              </button>
              <button
                onClick={() => setShowSimulator(true)}
                className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 text-sm"
              >
                <Eye className="w-4 h-4" />
                Preview
              </button>
              <button
                onClick={handleSaveFlow}
                disabled={saveFlowMutation.isLoading}
                className={`px-3 py-2 rounded-lg flex items-center gap-2 text-sm ${
                  saveFlowMutation.isLoading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-500 hover:bg-green-600'
                } text-white`}
              >
                <Save className="w-4 h-4" />
                {saveFlowMutation.isLoading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </Panel>
      </ReactFlow>

      <NodeConfigPanel />

      {/* Flow Simulator Modal */}
      <AnimatePresence>
        {showSimulator && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
            >
              <div className="p-6 border-b flex justify-between items-center">
                <h2 className="text-xl font-bold">Flow Preview</h2>
                <button
                  onClick={() => setShowSimulator(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="space-y-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-800">
                      This preview shows how your conversation flow will execute. 
                      Click "Run Simulation" to see it in action.
                    </p>
                  </div>
                  
                  {/* Flow Summary */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Flow Summary</h4>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p>Nodes: {nodes.length}</p>
                      <p>Connections: {edges.length}</p>
                      <p>Flow Name: {flowName}</p>
                      <p>Status: {currentFlowId ? 'Saved' : 'Unsaved'}</p>
                    </div>
                  </div>
                  
                  <button 
                    className="w-full px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center justify-center gap-2"
                    disabled={nodes.length === 0}
                  >
                    <Play className="w-5 h-5" />
                    Run Simulation
                  </button>
                  
                  {nodes.length === 0 && (
                    <p className="text-sm text-gray-500 text-center">
                      Add some nodes to enable simulation
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}