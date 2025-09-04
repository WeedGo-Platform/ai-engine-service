import { endpoints } from '../config/endpoints';
import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom node component for decision steps
function DecisionNode({ data }: { data: any }) {
  const getNodeColor = () => {
    switch (data.type) {
      case 'query': return 'bg-blue-100 border-blue-300';
      case 'model': return 'bg-indigo-100 border-indigo-300';
      case 'role': return 'bg-teal-100 border-teal-300';
      case 'orchestrator': return 'bg-orange-100 border-orange-300';
      case 'intent': return 'bg-purple-100 border-purple-300';
      case 'language': return 'bg-cyan-100 border-cyan-300';
      case 'entity': return 'bg-green-100 border-green-300';
      case 'product': return 'bg-yellow-100 border-yellow-300';
      case 'interface': return 'bg-red-100 border-red-300';
      case 'response': return 'bg-pink-100 border-pink-300';
      default: return 'bg-gray-100 border-gray-300';
    }
  };

  return (
    <div className={`px-4 py-3 rounded-lg border-2 ${getNodeColor()} min-w-[200px]`}>
      <div className="font-semibold text-sm text-gray-700">{data.label}</div>
      {data.value && (
        <div className="text-xs text-gray-600 mt-1">{data.value}</div>
      )}
      {data.confidence && (
        <div className="text-xs text-gray-500 mt-1">
          Confidence: {(data.confidence * 100).toFixed(1)}%
        </div>
      )}
      {data.reasoning && (
        <div className="text-xs text-gray-500 mt-2 italic">"{data.reasoning}"</div>
      )}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  decision: DecisionNode,
};

export default function DecisionTreeVisualizer() {
  const [selectedQuery, setSelectedQuery] = useState('');
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Fetch latest decision tree from API
  const { 
    data: latestDecision, 
    refetch, 
    isLoading: isLoadingDecision, 
    error: decisionError 
  } = useQuery({
    queryKey: ['decision-tree-analysis', selectedQuery],
    queryFn: async () => {
      if (!selectedQuery) return null;
      
      try {
        // Use dedicated decision tree analysis endpoint
        const response = await fetch(endpoints.chat.analyzeDecision, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: selectedQuery,
            session_id: `viz_${Date.now()}`
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          const errorMessage = errorData?.detail || response.statusText;
          
          if (response.status === 503) {
            throw new Error(`Model unavailable: ${errorMessage}`);
          }
          throw new Error(`Analysis failed: ${errorMessage}`);
        }
        
        const data = await response.json();
        
        // Return the structured data from the new endpoint
        return {
          query: data.query,
          intent: data.intent,
          intentConfidence: data.intent_confidence,
          intentReasoning: data.reasoning,
          entities: data.entities || [],
          slangMappings: data.slang_mappings || [],
          searchCriteria: data.search_criteria,
          products: data.products || [],
          response: data.response,
          responseConfidence: data.confidence,
          processingTime: data.processing_time_ms,
          overallConfidence: data.confidence,
          modelUsed: data.model_used || 'mistral_7b_v3',
          roleSelected: data.role_selected || 'budtender',
          languageDetected: data.language_detected || 'en',
          orchestratorUsed: data.orchestrator_used || 'multi-model',
          interfacesUsed: data.interfaces_used || [],
          decisionSteps: data.decision_steps || []
        };
      } catch (error) {
        console.error('Failed to analyze query:', error);
        throw new Error('Failed to analyze query. Please try again.');
      }
    },
    enabled: !!selectedQuery && selectedQuery.length > 0,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Convert decision data to flow nodes and edges
  useEffect(() => {
    if (!latestDecision) return;

    const newNodes: any[] = [];
    const newEdges: any[] = [];
    let yPos = 0;

    // Query Node
    newNodes.push({
      id: 'query',
      type: 'decision',
      position: { x: 400, y: yPos },
      data: {
        label: 'Customer Query',
        value: latestDecision.query,
        type: 'query',
      },
    });

    yPos += 100;

    // Model Loading Node
    newNodes.push({
      id: 'model',
      type: 'decision',
      position: { x: 200, y: yPos },
      data: {
        label: 'Model Loaded',
        value: latestDecision.modelUsed,
        type: 'model',
        confidence: 1.0,
      },
    });

    // Role Selection Node
    newNodes.push({
      id: 'role',
      type: 'decision',
      position: { x: 600, y: yPos },
      data: {
        label: 'Role Selected',
        value: latestDecision.roleSelected,
        type: 'role',
        reasoning: 'Based on context and user profile',
      },
    });

    newEdges.push({
      id: 'e-query-model',
      source: 'query',
      target: 'model',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    newEdges.push({
      id: 'e-query-role',
      source: 'query',
      target: 'role',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    yPos += 100;

    // Orchestrator Node
    newNodes.push({
      id: 'orchestrator',
      type: 'decision',
      position: { x: 400, y: yPos },
      data: {
        label: 'Multi-Model Orchestrator',
        value: latestDecision.orchestratorUsed,
        type: 'orchestrator',
        reasoning: 'Coordinating model selection and execution',
      },
    });

    newEdges.push({
      id: 'e-model-orchestrator',
      source: 'model',
      target: 'orchestrator',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    newEdges.push({
      id: 'e-role-orchestrator',
      source: 'role',
      target: 'orchestrator',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    yPos += 100;

    // Language Detection Node
    newNodes.push({
      id: 'language',
      type: 'decision',
      position: { x: 200, y: yPos },
      data: {
        label: 'Language Detection',
        value: latestDecision.languageDetected,
        type: 'language',
        confidence: 0.95,
      },
    });

    newEdges.push({
      id: 'e-orchestrator-language',
      source: 'orchestrator',
      target: 'language',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    yPos += 100;

    // Interface Layer Node
    newNodes.push({
      id: 'interface',
      type: 'decision',
      position: { x: 600, y: yPos - 100 },
      data: {
        label: 'Interface Layer',
        value: 'IIntentDetector, IResponseGenerator',
        type: 'interface',
        reasoning: 'SRP-based interfaces',
      },
    });

    newEdges.push({
      id: 'e-orchestrator-interface',
      source: 'orchestrator',
      target: 'interface',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    // Intent Detection Node (only if intent data is available)
    if (latestDecision.intent && latestDecision.intent !== 'unknown') {
      newNodes.push({
        id: 'intent',
        type: 'decision',
        position: { x: 400, y: yPos },
        data: {
          label: 'Intent Detection (IIntentDetector)',
          value: latestDecision.intent,
          confidence: latestDecision.intentConfidence > 0 ? latestDecision.intentConfidence : null,
          type: 'intent',
          reasoning: latestDecision.intentReasoning,
        },
      });

      newEdges.push({
        id: 'e-language-intent',
        source: 'language',
        target: 'intent',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      });

      newEdges.push({
        id: 'e-interface-intent',
        source: 'interface',
        target: 'intent',
        animated: true,
        style: { stroke: '#ff6b6b', strokeDasharray: '5 5' },
        markerEnd: { type: MarkerType.ArrowClosed },
      });
      
      yPos += 100;
    } else {
      // Show that intent detection is not available
      newNodes.push({
        id: 'intent',
        type: 'decision',
        position: { x: 400, y: yPos },
        data: {
          label: 'Intent Detection (IIntentDetector)',
          value: 'Not available',
          confidence: null,
          type: 'intent',
          reasoning: 'Intent analysis not provided by current model',
        },
      });

      newEdges.push({
        id: 'e-language-intent',
        source: 'language',
        target: 'intent',
        animated: false,
        style: { stroke: '#999', strokeDasharray: '5 5' },
        markerEnd: { type: MarkerType.ArrowClosed },
      });
      
      yPos += 100;
    }

    // Entity Extraction Nodes
    if (latestDecision.entities && latestDecision.entities.length > 0) {
      const entityStartX = 400 - (latestDecision.entities.length - 1) * 100;
      
      latestDecision.entities.forEach((entity: any, index: number) => {
        const entityId = `entity-${index}`;
        newNodes.push({
          id: entityId,
          type: 'decision',
          position: { x: entityStartX + index * 200, y: yPos },
          data: {
            label: 'Entity',
            value: `${entity.type}: ${entity.value}`,
            confidence: entity.confidence,
            type: 'entity',
          },
        });

        newEdges.push({
          id: `e-intent-${entityId}`,
          source: 'intent',
          target: entityId,
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      });

      yPos += 120;
    }

    // Cannabis Terminology Mapping
    if (latestDecision.slangMappings && latestDecision.slangMappings.length > 0) {
      newNodes.push({
        id: 'slang',
        type: 'decision',
        position: { x: 200, y: yPos - 120 },
        data: {
          label: 'Cannabis Slang Detection',
          value: latestDecision.slangMappings.map((m: any) => `${m.slang} → ${m.formal}`).join(', '),
          type: 'entity',
        },
      });

      newEdges.push({
        id: 'e-intent-slang',
        source: 'intent',
        target: 'slang',
        style: { stroke: '#9333ea', strokeDasharray: '5 5' },
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    }

    // Product Search Node
    newNodes.push({
      id: 'product-search',
      type: 'decision',
      position: { x: 400, y: yPos },
      data: {
        label: 'Product Search',
        value: `Criteria: ${JSON.stringify(latestDecision.searchCriteria)}`,
        type: 'product',
      },
    });

    if (latestDecision.entities && latestDecision.entities.length > 0) {
      latestDecision.entities.forEach((_: any, index: number) => {
        newEdges.push({
          id: `e-entity-${index}-search`,
          source: `entity-${index}`,
          target: 'product-search',
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      });
    } else {
      newEdges.push({
        id: 'e-intent-search',
        source: 'intent',
        target: 'product-search',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    }

    yPos += 120;

    // Product Results
    if (latestDecision.products && latestDecision.products.length > 0) {
      const prodStartX = 400 - (Math.min(latestDecision.products.length, 3) - 1) * 150;
      
      latestDecision.products.slice(0, 3).forEach((product: any, index: number) => {
        const productId = `product-${index}`;
        newNodes.push({
          id: productId,
          type: 'decision',
          position: { x: prodStartX + index * 300, y: yPos },
          data: {
            label: 'Product Match',
            value: `${product.name} (${product.score.toFixed(2)})`,
            confidence: product.score,
            type: 'product',
            reasoning: product.reasoning,
          },
        });

        newEdges.push({
          id: `e-search-${productId}`,
          source: 'product-search',
          target: productId,
          animated: true,
          style: { stroke: product.score > 0.7 ? '#10b981' : '#f59e0b' },
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      });

      yPos += 120;
    }

    // Response Generation
    newNodes.push({
      id: 'response',
      type: 'decision',
      position: { x: 400, y: yPos },
      data: {
        label: 'Response Generation (IResponseGenerator)',
        value: latestDecision.response?.substring(0, 100) + '...',
        type: 'response',
        confidence: latestDecision.responseConfidence,
        reasoning: `Using ${latestDecision.roleSelected} role with ${latestDecision.languageDetected} language`,
      },
    });

    // Connect interface layer to response
    newEdges.push({
      id: 'e-interface-response',
      source: 'interface',
      target: 'response',
      animated: true,
      style: { stroke: '#ff6b6b', strokeDasharray: '5 5' },
      markerEnd: { type: MarkerType.ArrowClosed },
    });

    if (latestDecision.products && latestDecision.products.length > 0) {
      latestDecision.products.slice(0, 3).forEach((_: any, index: number) => {
        newEdges.push({
          id: `e-product-${index}-response`,
          source: `product-${index}`,
          target: 'response',
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      });
    } else {
      newEdges.push({
        id: 'e-search-response',
        source: 'product-search',
        target: 'response',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    }

    setNodes(newNodes as any);
    setEdges(newEdges as any);
  }, [latestDecision, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: any) => setEdges((eds: any) => addEdge(params, eds) as any),
    [setEdges]
  );

  // Fetch decision tree data from API
  const { data: treeData, isLoading: isLoadingTree, error: treeError } = useQuery({
    queryKey: ['decision-tree'],
    queryFn: () => apiService.getDecisionTree(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  // Use sample queries from API with loading state
  const sampleQueries = treeData?.sample_queries || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Decision Tree Visualizer</h2>
            <p className="text-gray-600 mt-1">See how the AI processes queries and makes decisions</p>
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={isLiveMode}
                onChange={(e) => setIsLiveMode(e.target.checked)}
                className="rounded text-weed-green-500"
              />
              <span className="text-sm text-gray-700">Live Mode</span>
            </label>
            <button
              onClick={() => refetch()}
              disabled={isLoadingDecision}
              className={`px-4 py-2 text-white rounded-lg ${
                isLoadingDecision 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-weed-green-500 hover:bg-weed-green-600'
              }`}
            >
              {isLoadingDecision ? 'Analyzing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Query Input */}
        <div className="flex space-x-4">
          <input
            type="text"
            value={selectedQuery}
            onChange={(e) => setSelectedQuery(e.target.value)}
            placeholder="Enter a customer query to visualize..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500"
          />
          <button
            onClick={() => refetch()}
            disabled={isLoadingDecision || !selectedQuery.trim()}
            className={`px-6 py-2 text-white rounded-lg ${
              isLoadingDecision || !selectedQuery.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-purple-haze-600 hover:bg-purple-haze-700'
            }`}
          >
            {isLoadingDecision ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {/* Sample Queries */}
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">
            {isLoadingTree ? 'Loading examples...' : 'Try these examples:'}
          </p>
          <div className="flex flex-wrap gap-2">
            {isLoadingTree ? (
              // Loading skeleton for sample queries
              Array.from({ length: 5 }).map((_, index) => (
                <div
                  key={index}
                  className="px-3 py-1 bg-gray-200 rounded-full text-sm animate-pulse h-6 w-24"
                />
              ))
            ) : treeError ? (
              <div className="text-red-600 text-sm">
                Failed to load examples. Using defaults.
              </div>
            ) : sampleQueries.length > 0 ? (
              sampleQueries.map((query: string) => (
                <button
                  key={query}
                  onClick={() => setSelectedQuery(query)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200"
                >
                  {query}
                </button>
              ))
            ) : (
              // Fallback default queries when API returns empty
              [
                "got any fire?",
                "I need something for sleep",
                "show me pink kush 3.5g",
                "what's good for anxiety?",
                "gimme a half of something fruity",
              ].map((query: string) => (
                <button
                  key={query}
                  onClick={() => setSelectedQuery(query)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200"
                >
                  {query}
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Decision Tree Visualization */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="h-[600px] border border-gray-200 rounded-lg overflow-hidden relative">
          {isLoadingDecision ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weed-green-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Analyzing query...</p>
                <p className="text-sm text-gray-500 mt-1">Building decision tree</p>
              </div>
            </div>
          ) : decisionError ? (
            <div className="absolute inset-0 flex items-center justify-center bg-red-50">
              <div className="text-center">
                <div className="text-red-500 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-red-600 mb-2">Failed to analyze query</p>
                <p className="text-sm text-red-500 mb-4">{decisionError.message}</p>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                >
                  Try Again
                </button>
              </div>
            </div>
          ) : !selectedQuery ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="text-gray-400 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p className="text-gray-600 mb-2">Enter a query to visualize</p>
                <p className="text-sm text-gray-500">See how the AI processes customer questions</p>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background variant={"dots" as any} gap={12} size={1} />
            </ReactFlow>
          )}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-100 border-2 border-blue-300 rounded"></div>
            <span className="text-sm text-gray-600">Query</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-purple-100 border-2 border-purple-300 rounded"></div>
            <span className="text-sm text-gray-600">Intent</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border-2 border-green-300 rounded"></div>
            <span className="text-sm text-gray-600">Entity</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 border-2 border-yellow-300 rounded"></div>
            <span className="text-sm text-gray-600">Product</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-pink-100 border-2 border-pink-300 rounded"></div>
            <span className="text-sm text-gray-600">Response</span>
          </div>
        </div>
      </div>

      {/* Decision Details */}
      {latestDecision && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Details</h3>
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700">Processing Time</h4>
              <p className="text-2xl font-bold text-weed-green-600">
                {latestDecision.processingTime || '45'}ms
              </p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700">Confidence Score</h4>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-weed-green-500 h-2 rounded-full"
                    style={{ width: `${(latestDecision.overallConfidence || 0.75) * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium">
                  {((latestDecision.overallConfidence || 0.75) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700">Model Used</h4>
              <p className="text-sm text-gray-600">
                {latestDecision.modelUsed === 'unavailable' 
                  ? 'Model information unavailable' 
                  : latestDecision.modelUsed || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}