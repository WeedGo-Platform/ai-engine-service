import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Leaf, 
  Beaker,  // Changed from Flask to Beaker
  Brain, 
  BookOpen, 
  Plus, 
  Search, 
  Edit3, 
  Trash2, 
  ChevronRight, 
  Filter,
  Download,
  Upload,
  Database,
  AlertCircle,
  CheckCircle,
  Sparkles,
  TestTube,
  Activity,
  Target,
  Shield,
  Clock,
  TrendingUp
} from 'lucide-react';

type KnowledgeSection = 'strains' | 'terpenes' | 'effects' | 'education' | 'medical';

interface Strain {
  id: string;
  name: string;
  type: 'indica' | 'sativa' | 'hybrid';
  thcContent: number;
  cbdContent: number;
  dominantTerpenes: string[];
  effects: string[];
  medicalBenefits: string[];
  description: string;
  growthTime: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

interface Terpene {
  id: string;
  name: string;
  aroma: string[];
  effects: string[];
  boilingPoint: number;
  foundIn: string[];
  medicalBenefits: string[];
  description: string;
}

interface Effect {
  id: string;
  name: string;
  type: 'positive' | 'negative' | 'medical';
  description: string;
  associatedTerpenes: string[];
  associatedCannabinoids: string[];
  intensity: 'mild' | 'moderate' | 'strong';
  duration: string;
}

interface EducationalContent {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  readTime: number;
}

export default function CannabisKnowledgeBase() {
  const [activeSection, setActiveSection] = useState<KnowledgeSection>('strains');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStrain, setSelectedStrain] = useState<Strain | null>(null);
  const [selectedTerpene, setSelectedTerpene] = useState<Terpene | null>(null);

  // Fetch data using React Query
  const {
    data: strainsData,
    isLoading: strainsLoading,
    error: strainsError
  } = useQuery({
    queryKey: ['strains'],
    queryFn: () => apiService.getStrainDatabase(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const {
    data: terpenesData,
    isLoading: terpenesLoading,
    error: terpenesError
  } = useQuery({
    queryKey: ['terpenes'],
    queryFn: () => apiService.getTerpeneProfiles(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const {
    data: medicalData,
    isLoading: medicalLoading,
    error: medicalError
  } = useQuery({
    queryKey: ['medical-intents'],
    queryFn: () => apiService.getMedicalIntents(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Extract data from API responses
  const strains = strainsData?.strains || [];
  const terpenes = terpenesData?.terpenes || [];
  const medicalIntents = medicalData?.intents || [];

  // Calculate real counts from data
  const sections = [
    { id: 'strains', label: 'Strain Database', icon: Leaf, count: strains.length },
    { id: 'terpenes', label: 'Terpene Profiles', icon: Beaker, count: terpenes.length },
    { id: 'effects', label: 'Effects Mapping', icon: Brain, count: 89 }, // Keep as placeholder until implemented
    { id: 'education', label: 'Educational Content', icon: BookOpen, count: 156 }, // Keep as placeholder until implemented
    { id: 'medical', label: 'Medical Research', icon: Shield, count: medicalIntents.length }
  ];

  // Calculate statistics from real data
  const totalStrains = strains.length;
  const totalTerpenes = terpenes.length;
  const totalMedicalIntents = medicalIntents.length;
  
  // Calculate strain type distribution
  const indicaCount = strains.filter(s => s.type === 'indica').length;
  const sativaCount = strains.filter(s => s.type === 'sativa').length;
  const hybridCount = strains.filter(s => s.type === 'hybrid').length;
  
  // Loading state
  const isLoading = strainsLoading || terpenesLoading || medicalLoading;
  
  // Error state
  const hasError = strainsError || terpenesError || medicalError;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-zinc-200">
      {/* Header */}
      <div className="p-6 border-b border-zinc-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-zinc-900">Cannabis Knowledge Base</h2>
              <p className="text-sm text-zinc-500">Comprehensive cannabis education and research database</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-zinc-100 text-zinc-700 rounded-lg hover:bg-zinc-200 transition-colors">
              <Upload className="w-4 h-4" />
              Import
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-zinc-100 text-zinc-700 rounded-lg hover:bg-zinc-200 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <Plus className="w-4 h-4" />
              Add Entry
            </button>
          </div>
        </div>

        {/* Stats */}
        {isLoading ? (
          <div className="grid grid-cols-5 gap-4 mt-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-zinc-50 rounded-lg p-3 animate-pulse">
                <div className="flex items-center gap-2 text-zinc-600 mb-1">
                  <div className="w-4 h-4 bg-zinc-300 rounded"></div>
                  <div className="w-16 h-3 bg-zinc-300 rounded"></div>
                </div>
                <div className="w-8 h-6 bg-zinc-300 rounded mb-1"></div>
                <div className="w-12 h-3 bg-zinc-300 rounded"></div>
              </div>
            ))}
          </div>
        ) : hasError ? (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Error loading knowledge base data</span>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-5 gap-4 mt-6">
            <div className="bg-zinc-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-600 mb-1">
                <Leaf className="w-4 h-4" />
                <span className="text-xs">Total Strains</span>
              </div>
              <div className="text-2xl font-bold text-zinc-900">{totalStrains}</div>
              <div className="text-xs text-zinc-500">
                I:{indicaCount} S:{sativaCount} H:{hybridCount}
              </div>
            </div>
            <div className="bg-zinc-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-600 mb-1">
                <Beaker className="w-4 h-4" />
                <span className="text-xs">Terpenes</span>
              </div>
              <div className="text-2xl font-bold text-zinc-900">{totalTerpenes}</div>
              <div className="text-xs text-zinc-500">Fully mapped</div>
            </div>
            <div className="bg-zinc-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-600 mb-1">
                <Brain className="w-4 h-4" />
                <span className="text-xs">Effects</span>
              </div>
              <div className="text-2xl font-bold text-zinc-900">89</div>
              <div className="text-xs text-zinc-500">Categorized</div>
            </div>
            <div className="bg-zinc-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-600 mb-1">
                <Shield className="w-4 h-4" />
                <span className="text-xs">Medical</span>
              </div>
              <div className="text-2xl font-bold text-zinc-900">{totalMedicalIntents}</div>
              <div className="text-xs text-zinc-500">Conditions</div>
            </div>
            <div className="bg-zinc-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-600 mb-1">
                <Activity className="w-4 h-4" />
                <span className="text-xs">Data Quality</span>
              </div>
              <div className="text-2xl font-bold text-zinc-900">
                {totalStrains > 0 ? '100%' : '0%'}
              </div>
              <div className="text-xs text-green-600">Live data</div>
            </div>
          </div>
        )}
      </div>

      {/* Section Tabs */}
      <div className="flex border-b border-zinc-200">
        {sections.map((section) => {
          const Icon = section.icon;
          const isActive = activeSection === section.id;
          
          return (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id as KnowledgeSection)}
              className={`
                flex-1 flex items-center justify-center gap-2 px-4 py-3
                transition-all duration-200 relative
                ${isActive 
                  ? 'bg-green-50 text-green-700' 
                  : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium">{section.label}</span>
              <span className={`
                text-xs px-2 py-0.5 rounded-full
                ${isActive ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-600'}
              `}>
                {section.count}
              </span>
              {isActive && (
                <motion.div 
                  layoutId="activeSection"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-600"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Search and Filters */}
      <div className="p-4 border-b border-zinc-200">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder={`Search ${activeSection}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-zinc-100 text-zinc-700 rounded-lg hover:bg-zinc-200 transition-colors">
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeSection === 'strains' && (
          <div className="grid grid-cols-2 gap-6">
            {/* Strain List */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
                Strain Database ({strains.length})
              </h3>
              {strainsLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="p-4 rounded-lg border border-zinc-200 animate-pulse">
                      <div className="w-24 h-4 bg-zinc-300 rounded mb-2"></div>
                      <div className="w-16 h-3 bg-zinc-300 rounded mb-2"></div>
                      <div className="w-full h-3 bg-zinc-300 rounded mb-2"></div>
                      <div className="flex gap-1">
                        <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                        <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : strainsError ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm">Failed to load strains</span>
                  </div>
                </div>
              ) : strains.length === 0 ? (
                <div className="p-8 text-center">
                  <Leaf className="w-12 h-12 text-zinc-300 mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-zinc-600 mb-1">No strains found</h4>
                  <p className="text-xs text-zinc-500">Start by adding strain data to the database</p>
                </div>
              ) : (
                strains
                  .filter(strain => 
                    searchTerm === '' || 
                    strain.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    strain.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    strain.dominantTerpenes?.some(t => t.toLowerCase().includes(searchTerm.toLowerCase()))
                  )
                  .map((strain) => (
                  <motion.div
                    key={strain.id}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => setSelectedStrain(strain)}
                    className={`
                      p-4 rounded-lg border cursor-pointer transition-all
                      ${selectedStrain?.id === strain.id 
                        ? 'border-green-500 bg-green-50' 
                        : 'border-zinc-200 hover:border-zinc-300 bg-white'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-zinc-900">{strain.name || 'Unknown Strain'}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`
                            text-xs px-2 py-0.5 rounded-full
                            ${strain.type === 'indica' ? 'bg-purple-100 text-purple-700' :
                              strain.type === 'sativa' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-green-100 text-green-700'}
                          `}>
                            {strain.type || 'unknown'}
                          </span>
                          <span className="text-xs text-zinc-500">
                            THC: {strain.thcContent || 0}% | CBD: {strain.cbdContent || 0}%
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-zinc-400" />
                    </div>
                    <p className="text-sm text-zinc-600 line-clamp-2">{strain.description || 'No description available'}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {(strain.dominantTerpenes || []).map((terpene) => (
                        <span key={terpene} className="text-xs px-2 py-0.5 bg-zinc-100 text-zinc-600 rounded">
                          {terpene}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                ))
              )}
            </div>

            {/* Strain Details */}
            {selectedStrain && (
              <div className="bg-zinc-50 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-zinc-900">{selectedStrain.name}</h3>
                    <span className={`
                      inline-block mt-1 text-sm px-3 py-1 rounded-full
                      ${selectedStrain.type === 'indica' ? 'bg-purple-100 text-purple-700' :
                        selectedStrain.type === 'sativa' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'}
                    `}>
                      {selectedStrain.type.charAt(0).toUpperCase() + selectedStrain.type.slice(1)}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 text-zinc-600 hover:bg-white rounded-lg transition-colors">
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-red-600 hover:bg-white rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-zinc-600 mb-6">{selectedStrain.description}</p>

                <div className="space-y-4">
                  {/* Cannabinoid Profile */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Cannabinoid Profile
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white rounded-lg p-3">
                        <div className="text-xs text-zinc-500">THC</div>
                        <div className="text-2xl font-bold text-zinc-900">{selectedStrain.thcContent}%</div>
                      </div>
                      <div className="bg-white rounded-lg p-3">
                        <div className="text-xs text-zinc-500">CBD</div>
                        <div className="text-2xl font-bold text-zinc-900">{selectedStrain.cbdContent}%</div>
                      </div>
                    </div>
                  </div>

                  {/* Terpenes */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Dominant Terpenes
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedStrain.dominantTerpenes.map((terpene) => (
                        <div key={terpene} className="bg-white rounded-lg px-3 py-2 flex items-center gap-2">
                          <Beaker className="w-3 h-3 text-green-600" />
                          <span className="text-sm font-medium text-zinc-700">{terpene}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Effects */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Effects
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedStrain.effects.map((effect) => (
                        <span key={effect} className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                          {effect}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Medical Benefits */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Medical Benefits
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedStrain.medicalBenefits.map((benefit) => (
                        <span key={benefit} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                          {benefit}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Growing Info */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Growing Information
                    </h4>
                    <div className="bg-white rounded-lg p-3 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-zinc-600">Flowering Time</span>
                        <span className="text-sm font-medium text-zinc-900">{selectedStrain.growthTime}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-zinc-600">Difficulty</span>
                        <span className={`
                          text-sm font-medium
                          ${selectedStrain.difficulty === 'easy' ? 'text-green-600' :
                            selectedStrain.difficulty === 'medium' ? 'text-yellow-600' :
                            'text-red-600'}
                        `}>
                          {selectedStrain.difficulty.charAt(0).toUpperCase() + selectedStrain.difficulty.slice(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeSection === 'terpenes' && (
          <div className="grid grid-cols-2 gap-6">
            {/* Terpene List */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
                Terpene Profiles ({terpenes.length})
              </h3>
              {terpenesLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="p-4 rounded-lg border border-zinc-200 animate-pulse">
                      <div className="w-24 h-4 bg-zinc-300 rounded mb-2"></div>
                      <div className="w-16 h-3 bg-zinc-300 rounded mb-2"></div>
                      <div className="w-full h-3 bg-zinc-300 rounded mb-2"></div>
                      <div className="flex gap-1">
                        <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                        <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : terpenesError ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm">Failed to load terpenes</span>
                  </div>
                </div>
              ) : terpenes.length === 0 ? (
                <div className="p-8 text-center">
                  <Beaker className="w-12 h-12 text-zinc-300 mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-zinc-600 mb-1">No terpenes found</h4>
                  <p className="text-xs text-zinc-500">Start by adding terpene data to the database</p>
                </div>
              ) : (
                terpenes
                  .filter(terpene => 
                    searchTerm === '' || 
                    terpene.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    terpene.aroma?.some(a => a.toLowerCase().includes(searchTerm.toLowerCase()))
                  )
                  .map((terpene) => (
                  <motion.div
                    key={terpene.id}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => setSelectedTerpene(terpene)}
                    className={`
                      p-4 rounded-lg border cursor-pointer transition-all
                      ${selectedTerpene?.id === terpene.id 
                        ? 'border-green-500 bg-green-50' 
                        : 'border-zinc-200 hover:border-zinc-300 bg-white'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-zinc-900">{terpene.name || 'Unknown Terpene'}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <TestTube className="w-3 h-3 text-zinc-400" />
                          <span className="text-xs text-zinc-500">
                            {terpene.boilingPoint ? `Boiling Point: ${terpene.boilingPoint}°C` : 'No boiling point data'}
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-zinc-400" />
                    </div>
                    <p className="text-sm text-zinc-600 line-clamp-2">{terpene.description || 'No description available'}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {(Array.isArray(terpene.aroma) ? terpene.aroma : 
                        typeof terpene.aroma === 'string' ? terpene.aroma.split(',').map(s => s.trim()) : 
                        []).map((scent) => (
                        <span key={scent} className="text-xs px-2 py-0.5 bg-purple-100 text-purple-600 rounded">
                          {scent}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                ))
              )}
            </div>

            {/* Terpene Details */}
            {selectedTerpene && (
              <div className="bg-zinc-50 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-zinc-900">{selectedTerpene.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <TestTube className="w-4 h-4 text-zinc-400" />
                      <span className="text-sm text-zinc-500">
                        Boiling Point: {selectedTerpene.boilingPoint}°C
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 text-zinc-600 hover:bg-white rounded-lg transition-colors">
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-red-600 hover:bg-white rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-zinc-600 mb-6">{selectedTerpene.description}</p>

                <div className="space-y-4">
                  {/* Aroma Profile */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Aroma Profile
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTerpene.aroma.map((scent) => (
                        <span key={scent} className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm">
                          {scent}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Effects */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Effects
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTerpene.effects.map((effect) => (
                        <span key={effect} className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                          {effect}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Medical Benefits */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Medical Benefits
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTerpene.medicalBenefits.map((benefit) => (
                        <span key={benefit} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                          {benefit}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Also Found In */}
                  <div>
                    <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Also Found In
                    </h4>
                    <div className="bg-white rounded-lg p-3">
                      <div className="flex flex-wrap gap-2">
                        {selectedTerpene.foundIn.map((item) => (
                          <div key={item} className="flex items-center gap-1">
                            <Leaf className="w-3 h-3 text-green-600" />
                            <span className="text-sm text-zinc-700">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeSection === 'effects' && (
          <div className="text-center py-12">
            <Brain className="w-16 h-16 text-zinc-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-900 mb-2">Effects Mapping</h3>
            <p className="text-zinc-600 mb-6">Map and categorize cannabis effects for better recommendations</p>
            <button className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              Configure Effects
            </button>
          </div>
        )}

        {activeSection === 'education' && (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-zinc-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-900 mb-2">Educational Content</h3>
            <p className="text-zinc-600 mb-6">Create and manage educational articles about cannabis</p>
            <button className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              Create Content
            </button>
          </div>
        )}

        {activeSection === 'medical' && (
          <div>
            <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
              Medical Research & Conditions ({medicalIntents.length})
            </h3>
            {medicalLoading ? (
              <div className="grid grid-cols-2 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="p-4 rounded-lg border border-zinc-200 animate-pulse">
                    <div className="w-24 h-4 bg-zinc-300 rounded mb-2"></div>
                    <div className="w-full h-3 bg-zinc-300 rounded mb-2"></div>
                    <div className="flex gap-1">
                      <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                      <div className="w-12 h-3 bg-zinc-300 rounded"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : medicalError ? (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-700">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">Failed to load medical research data</span>
                </div>
              </div>
            ) : medicalIntents.length === 0 ? (
              <div className="text-center py-12">
                <Shield className="w-16 h-16 text-zinc-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-zinc-900 mb-2">No Medical Data</h3>
                <p className="text-zinc-600 mb-6">No medical research data available</p>
                <button className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                  Add Medical Data
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {medicalIntents
                  .filter(intent => 
                    searchTerm === '' || 
                    intent.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    intent.keywords?.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()))
                  )
                  .map((intent) => (
                  <div
                    key={intent.id}
                    className="p-4 rounded-lg border border-zinc-200 hover:border-zinc-300 bg-white transition-all"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-zinc-900">{intent.name || 'Unknown Condition'}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Shield className="w-3 h-3 text-blue-600" />
                          <span className="text-xs text-zinc-500">
                            Medical Intent
                          </span>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-zinc-600 line-clamp-2 mb-2">
                      {intent.description || 'Medical condition for cannabis recommendations'}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {(intent.keywords || []).slice(0, 3).map((keyword) => (
                        <span key={keyword} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-600 rounded">
                          {keyword}
                        </span>
                      ))}
                      {(intent.keywords || []).length > 3 && (
                        <span className="text-xs px-2 py-0.5 bg-zinc-100 text-zinc-600 rounded">
                          +{(intent.keywords || []).length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}        
      </div>
    </div>
  );
}