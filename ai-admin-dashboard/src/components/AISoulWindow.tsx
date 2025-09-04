import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Activity, 
  Eye, 
  Zap, 
  GitBranch,
  MessageSquare,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Package,
  Heart,
  Shield,
  BookOpen,
  Lightbulb,
  Target,
  Layers,
  Cpu,
  Database,
  Search,
  Filter,
  Settings,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  PauseCircle,
  PlayCircle,
  Info
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';

interface ThoughtProcess {
  timestamp: string;
  stage: 'intent' | 'context' | 'search' | 'reasoning' | 'generation' | 'validation';
  thought: string;
  confidence: number;
  alternatives?: string[];
  factors?: string[];
}

interface DecisionPath {
  id: string;
  decision: string;
  reasoning: string;
  confidence: number;
  selected: boolean;
  consequences?: string[];
}

interface ContextFactor {
  name: string;
  value: string | number;
  influence: 'high' | 'medium' | 'low';
  icon: any;
}

interface AIState {
  currentIntent: string;
  confidence: number;
  emotionalState: string;
  complianceStatus: 'compliant' | 'warning' | 'violation';
  knowledgeAccess: string[];
  activePersonality: string;
}

export default function AISoulWindow() {
  const [isLive, setIsLive] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [thoughtProcesses, setThoughtProcesses] = useState<ThoughtProcess[]>([]);
  const [currentStage, setCurrentStage] = useState<string>('idle');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['thoughts', 'context', 'decisions']));
  const [userInput, setUserInput] = useState<string>('');
  const thoughtStreamRef = useRef<HTMLDivElement>(null);

  // Fetch real AI decision stream
  const { data: decisionStream, refetch: refetchDecisionStream } = useQuery({
    queryKey: ['decision-stream'],
    queryFn: apiService.getDecisionStream,
    refetchInterval: isLive ? 3000 : false,
    enabled: isLive
  });
  
  // Fetch context factors
  const { data: contextData } = useQuery({
    queryKey: ['context-factors', selectedSession],
    queryFn: () => apiService.getContextFactors(selectedSession || undefined),
    refetchInterval: isLive ? 5000 : false
  });
  
  // Fetch decision paths
  const { data: decisionPaths } = useQuery({
    queryKey: ['decision-paths', userInput],
    queryFn: () => apiService.getDecisionPaths(userInput),
    enabled: userInput.length > 0
  });
  
  // Update thought processes from API data
  useEffect(() => {
    if (decisionStream?.thought_processes) {
      setThoughtProcesses(decisionStream.thought_processes);
      setCurrentStage(decisionStream.current_stage || 'idle');
    }
  }, [decisionStream]);

  // Auto-scroll thought stream
  useEffect(() => {
    if (thoughtStreamRef.current && thoughtProcesses.length > 0) {
      thoughtStreamRef.current.scrollTop = thoughtStreamRef.current.scrollHeight;
    }
  }, [thoughtProcesses]);
  
  // No simulation needed - we have real API data

  // Auto-scroll thought stream
  useEffect(() => {
    if (thoughtStreamRef.current) {
      thoughtStreamRef.current.scrollTop = thoughtStreamRef.current.scrollHeight;
    }
  }, [thoughtProcesses]);

  // Use AI state from API or defaults
  const aiState: AIState = decisionStream?.ai_state || {
    currentIntent: 'idle',
    confidence: 0,
    emotionalState: 'neutral',
    complianceStatus: 'compliant',
    knowledgeAccess: [],
    activePersonality: 'default'
  };

  // Map API context factors to component format
  const contextFactors: ContextFactor[] = contextData?.factors?.map((factor: any) => ({
    ...factor,
    icon: factor.name.includes('Time') ? Clock :
          factor.name.includes('Conversation') ? MessageSquare :
          factor.name.includes('Model') ? Brain :
          factor.name.includes('Inventory') ? Database :
          factor.name.includes('Compliance') ? Shield :
          Users
  })) || [];

  // Use decision paths from API or empty array
  const paths: DecisionPath[] = decisionPaths?.paths || [];

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      intent: 'text-blue-500',
      context: 'text-purple-500',
      search: 'text-green-500',
      reasoning: 'text-yellow-500',
      generation: 'text-indigo-500',
      validation: 'text-red-500'
    };
    return colors[stage] || 'text-gray-500';
  };

  const getStageIcon = (stage: string) => {
    const icons: Record<string, any> = {
      intent: Target,
      context: Layers,
      search: Search,
      reasoning: Brain,
      generation: Zap,
      validation: Shield
    };
    const Icon = icons[stage] || Brain;
    return <Icon className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Brain className="w-8 h-8 text-purple-500" />
              AI Soul Window
            </h2>
            <p className="text-gray-600 mt-1">Real-time insight into AI decision-making process</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsLive(!isLive)}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  isLive 
                    ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {isLive ? <PlayCircle className="w-4 h-4" /> : <PauseCircle className="w-4 h-4" />}
                {isLive ? 'Live' : 'Paused'}
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>

        {/* AI State Overview */}
        <div className="grid grid-cols-6 gap-4 mt-6">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-3">
            <div className="text-xs text-blue-600 font-medium">Current Intent</div>
            <div className="text-sm font-bold text-blue-900 mt-1">{aiState.currentIntent}</div>
          </div>
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-3">
            <div className="text-xs text-purple-600 font-medium">Confidence</div>
            <div className="text-sm font-bold text-purple-900 mt-1">{(aiState.confidence * 100).toFixed(0)}%</div>
          </div>
          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-3">
            <div className="text-xs text-green-600 font-medium">Emotional State</div>
            <div className="text-sm font-bold text-green-900 mt-1">{aiState.emotionalState}</div>
          </div>
          <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg p-3">
            <div className="text-xs text-yellow-600 font-medium">Compliance</div>
            <div className="text-sm font-bold text-yellow-900 mt-1">{aiState.complianceStatus}</div>
          </div>
          <div className="bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg p-3">
            <div className="text-xs text-indigo-600 font-medium">Personality</div>
            <div className="text-sm font-bold text-indigo-900 mt-1">{aiState.activePersonality}</div>
          </div>
          <div className="bg-gradient-to-r from-pink-50 to-pink-100 rounded-lg p-3">
            <div className="text-xs text-pink-600 font-medium">Knowledge Access</div>
            <div className="text-sm font-bold text-pink-900 mt-1">{aiState.knowledgeAccess.length} sources</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Thought Stream */}
        <div className="col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm">
            <div 
              className="p-4 border-b flex items-center justify-between cursor-pointer hover:bg-gray-50"
              onClick={() => toggleSection('thoughts')}
            >
              <h3 className="font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-500" />
                Thought Stream
              </h3>
              {expandedSections.has('thoughts') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            </div>
            
            <AnimatePresence>
              {expandedSections.has('thoughts') && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div 
                    ref={thoughtStreamRef}
                    className="p-4 space-y-3 max-h-96 overflow-y-auto"
                  >
                    {thoughtProcesses.map((thought, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        className="border-l-4 border-purple-200 pl-4 py-2"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              {getStageIcon(thought.stage)}
                              <span className={`text-xs font-medium ${getStageColor(thought.stage)}`}>
                                {thought.stage.toUpperCase()}
                              </span>
                              <span className="text-xs text-gray-400">
                                {new Date(thought.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700">{thought.thought}</p>
                            {thought.factors && thought.factors.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {thought.factors.map((factor, i) => (
                                  <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                    {factor}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            <div className="text-right">
                              <div className="text-xs text-gray-500">Confidence</div>
                              <div className="text-lg font-bold text-purple-600">
                                {(thought.confidence * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Decision Paths */}
          <div className="bg-white rounded-xl shadow-sm">
            <div 
              className="p-4 border-b flex items-center justify-between cursor-pointer hover:bg-gray-50"
              onClick={() => toggleSection('decisions')}
            >
              <h3 className="font-semibold flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-indigo-500" />
                Decision Paths Considered
              </h3>
              {expandedSections.has('decisions') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            </div>
            
            <AnimatePresence>
              {expandedSections.has('decisions') && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-4 space-y-4">
                    {paths.map((path) => (
                      <div 
                        key={path.id}
                        className={`border rounded-lg p-4 ${
                          path.selected 
                            ? 'border-green-500 bg-green-50' 
                            : 'border-gray-200 bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {path.selected ? (
                                <CheckCircle className="w-5 h-5 text-green-600" />
                              ) : (
                                <div className="w-5 h-5 rounded-full border-2 border-gray-400" />
                              )}
                              <span className={`font-medium ${path.selected ? 'text-green-900' : 'text-gray-700'}`}>
                                {path.decision}
                              </span>
                              {path.selected && (
                                <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
                                  SELECTED
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{path.reasoning}</p>
                            {path.consequences && (
                              <div className="flex flex-wrap gap-2">
                                {path.consequences.map((consequence, idx) => (
                                  <span key={idx} className="text-xs bg-white px-2 py-1 rounded border border-gray-200">
                                    {consequence}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className="ml-4 text-right">
                            <div className="text-xs text-gray-500">Confidence</div>
                            <div className={`text-2xl font-bold ${
                              path.confidence > 0.8 ? 'text-green-600' : 
                              path.confidence > 0.6 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                              {(path.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Context Factors */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm">
            <div 
              className="p-4 border-b flex items-center justify-between cursor-pointer hover:bg-gray-50"
              onClick={() => toggleSection('context')}
            >
              <h3 className="font-semibold flex items-center gap-2">
                <Layers className="w-5 h-5 text-green-500" />
                Context Factors
              </h3>
              {expandedSections.has('context') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            </div>
            
            <AnimatePresence>
              {expandedSections.has('context') && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-4 space-y-3">
                    {contextFactors.map((factor, idx) => {
                      const Icon = factor.icon;
                      return (
                        <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <Icon className="w-5 h-5 text-gray-600" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">{factor.name}</div>
                              <div className="text-xs text-gray-500">{factor.value}</div>
                            </div>
                          </div>
                          <div className={`px-2 py-1 rounded text-xs font-medium ${
                            factor.influence === 'high' ? 'bg-red-100 text-red-700' :
                            factor.influence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {factor.influence.toUpperCase()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Processing Stage */}
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-orange-500" />
              Processing Pipeline
            </h3>
            <div className="space-y-2">
              {['intent', 'context', 'search', 'reasoning', 'generation', 'validation'].map((stage) => (
                <div key={stage} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    currentStage === stage ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
                  }`} />
                  <span className={`text-sm capitalize ${
                    currentStage === stage ? 'font-medium text-gray-900' : 'text-gray-500'
                  }`}>
                    {stage}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Knowledge Sources */}
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-500" />
              Active Knowledge
            </h3>
            <div className="space-y-2">
              {aiState.knowledgeAccess.map((source, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <span className="text-sm text-blue-900">{source.replace('_', ' ').toUpperCase()}</span>
                  <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}