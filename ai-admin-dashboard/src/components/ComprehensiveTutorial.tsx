import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, 
  ChevronRight, 
  CheckCircle, 
  Circle,
  PlayCircle,
  Target,
  Brain,
  MessageSquare,
  Database,
  Sparkles,
  ArrowRight,
  Award,
  Zap,
  Users,
  TrendingUp,
  Code,
  Package,
  Settings,
  Upload,
  Download,
  RefreshCw,
  Shield,
  GitBranch,
  Eye,
  BarChart3,
  Workflow,
  Cpu,
  HardDrive,
  AlertCircle,
  Info,
  FileText,
  Copy,
  Save,
  Trash2,
  Plus,
  Minus,
  Search,
  Filter,
  Clock,
  Calendar,
  Hash,
  List,
  Grid,
  Layers,
  Terminal,
  Globe,
  Lock,
  Unlock,
  Key,
  UserCheck,
  Bot,
  Lightbulb,
  Beaker,
  FlaskConical,
  TestTube,
  Activity,
  Gauge,
  Rocket,
  Server
} from 'lucide-react';
import toast from 'react-hot-toast';

interface TutorialStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action?: () => void;
  actionLabel?: string;
  tips?: string[];
  warnings?: string[];
  example?: {
    input: string;
    expectedOutput: string;
    explanation?: string;
  };
  codeExample?: {
    language: string;
    code: string;
  };
  bestPractices?: string[];
  completed?: boolean;
}

interface TutorialModule {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  steps: TutorialStep[];
  estimatedTime: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  prerequisites?: string[];
}

export default function ComprehensiveTutorial() {
  const [activeModule, setActiveModule] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5024';

  // Comprehensive Tutorial Modules
  const modules: TutorialModule[] = [
    // ============= GETTING STARTED =============
    {
      id: 'getting-started',
      title: '🚀 Getting Started & Overview',
      description: 'Complete introduction to the AI Admin Portal',
      icon: <PlayCircle className="w-5 h-5" />,
      estimatedTime: '20 mins',
      difficulty: 'beginner',
      steps: [
        {
          id: 'gs-1',
          title: 'Welcome to WeedGo AI Admin Portal',
          description: 'Your comprehensive guide to managing, training, and optimizing the cannabis AI assistant.',
          icon: <BookOpen className="w-4 h-4" />,
          tips: [
            'The portal is divided into functional areas for easy navigation',
            'Each component serves a specific purpose in the AI ecosystem',
            'Changes made here directly affect customer interactions',
            'Always test changes before deploying to production'
          ],
          bestPractices: [
            'Start with the Tutorial to understand the system',
            'Use the Dashboard to monitor overall health',
            'Test everything in the Chat Testing area first',
            'Keep regular backups of your training data'
          ]
        },
        {
          id: 'gs-2',
          title: 'Understanding the Architecture',
          description: 'Learn how all components work together to power the AI.',
          icon: <Layers className="w-4 h-4" />,
          example: {
            input: 'User asks: "What helps with anxiety?"',
            expectedOutput: 'AI processes through: Intent Detection → Knowledge Base → Training Data → Response Generation',
            explanation: 'The AI uses multiple layers to generate accurate, context-aware responses'
          },
          tips: [
            'Training Data: Your custom examples and corrections',
            'Knowledge Base: Cannabis strain and product information',
            'AI Model: The core language understanding engine',
            'Configuration: Rules and parameters that guide behavior'
          ]
        },
        {
          id: 'gs-3',
          title: 'Navigation & Key Areas',
          description: 'Master the portal layout and understand where to find everything.',
          icon: <Grid className="w-4 h-4" />,
          bestPractices: [
            'Dashboard: Monitor performance and key metrics',
            'Training Hub: Add and manage training examples',
            'Knowledge Base: Cannabis product database',
            'AI Soul: Real-time AI decision monitoring',
            'Analytics: Detailed performance analysis'
          ],
          actionLabel: 'Explore Dashboard',
          action: () => {
            window.location.hash = '#dashboard';
            toast.success('Navigate through each section to familiarize yourself');
          }
        }
      ]
    },

    // ============= UNIFIED TRAINING HUB =============
    {
      id: 'training-hub-mastery',
      title: '🎓 Unified Training Hub Mastery',
      description: 'Complete guide to using the Training Hub effectively',
      icon: <Brain className="w-5 h-5" />,
      estimatedTime: '45 mins',
      difficulty: 'intermediate',
      prerequisites: ['getting-started'],
      steps: [
        {
          id: 'th-1',
          title: 'Training Hub vs Training Center',
          description: 'Understanding the difference between these two critical components.',
          icon: <Info className="w-4 h-4" />,
          tips: [
            'Training Hub: Add individual training examples and manage existing ones',
            'Training Center: Advanced tools for batch training and model fine-tuning',
            'Use Training Hub for day-to-day improvements',
            'Use Training Center for major training operations'
          ],
          example: {
            input: 'Customer: "I need something for pain"',
            expectedOutput: 'Training Hub: Add this as a single example\nTraining Center: Import 100 similar medical queries',
            explanation: 'Training Hub is for incremental learning, Training Center for bulk operations'
          }
        },
        {
          id: 'th-2',
          title: 'Adding Effective Training Examples',
          description: 'Learn the art of creating high-quality training data.',
          icon: <Plus className="w-4 h-4" />,
          example: {
            input: 'What strains help with insomnia?',
            expectedOutput: 'For insomnia, I recommend indica strains like Granddaddy Purple (23% THC), Northern Lights (18% THC), or Purple Kush (22% THC). These strains contain myrcene and linalool terpenes that promote relaxation. Start with 0.25g about 1 hour before bed. For a milder option, try a 1:1 THC:CBD strain like Pennywise.',
            explanation: 'Good examples include: specific strains, THC/CBD levels, terpenes, dosing, and timing'
          },
          bestPractices: [
            'Include specific product names and details',
            'Mention THC/CBD percentages when relevant',
            'Add dosing recommendations',
            'Include timing information',
            'Provide alternatives for different preferences',
            'Use natural, conversational language'
          ],
          actionLabel: 'Open Training Hub',
          action: () => {
            window.location.hash = '#unified-training';
            toast.success('Try adding this example to your training data');
          }
        },
        {
          id: 'th-3',
          title: 'Categories and Intent Mapping',
          description: 'Organize training data for optimal AI learning.',
          icon: <Filter className="w-4 h-4" />,
          tips: [
            'Medical: Health-related queries and recommendations',
            'Product: Specific product questions and features',
            'Effects: Desired effects and experiences',
            'Dosing: Consumption amounts and methods',
            'Legal: Compliance and regulatory questions',
            'General: Broad cannabis information'
          ],
          codeExample: {
            language: 'json',
            code: `{
  "category": "medical",
  "intent": "pain_relief",
  "input": "I have chronic back pain",
  "output": "For chronic back pain, consider high-CBD strains...",
  "confidence": 0.95,
  "tags": ["medical", "pain", "cbd", "chronic"]
}`
          }
        },
        {
          id: 'th-4',
          title: 'Bulk Import Training Data',
          description: 'Import large datasets to rapidly improve AI knowledge.',
          icon: <Upload className="w-4 h-4" />,
          codeExample: {
            language: 'json',
            code: `[
  {
    "input": "What's good for creativity?",
    "output": "For creativity, try sativa strains like Jack Herer or Green Crack...",
    "category": "effects"
  },
  {
    "input": "I'm new to cannabis",
    "output": "Welcome! For beginners, I recommend starting with low-THC strains...",
    "category": "general"
  }
]`
          },
          bestPractices: [
            'Validate JSON format before importing',
            'Include at least 50 examples per category',
            'Review imported data for accuracy',
            'Test AI responses after bulk import',
            'Keep backups before major imports'
          ],
          actionLabel: 'Download Import Template',
          action: async () => {
            const template = [
              { input: "Example question 1", output: "Example response 1", category: "medical" },
              { input: "Example question 2", output: "Example response 2", category: "product" }
            ];
            const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'training_template.json';
            a.click();
            toast.success('Template downloaded! Fill it with your training data');
          }
        },
        {
          id: 'th-5',
          title: 'Export and Backup Training Data',
          description: 'Preserve your valuable training data with regular exports.',
          icon: <Download className="w-4 h-4" />,
          tips: [
            'Export weekly for regular backups',
            'Export before major changes',
            'Use versioned filenames (e.g., training_v1_2024_01_15.json)',
            'Store backups in multiple locations',
            'Document what each export contains'
          ],
          actionLabel: 'Export Current Training Data',
          action: async () => {
            try {
              const response = await fetch(`${apiUrl}/api/v1/ai/training-examples/export`);
              if (response.ok) {
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `training_backup_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                toast.success('Training data exported successfully!');
              }
            } catch (error) {
              toast.error('Export failed. Check your connection.');
            }
          }
        }
      ]
    },

    // ============= PRODUCT TRAINING CONFIGURATION =============
    {
      id: 'product-training',
      title: '📦 Product Training Configuration',
      description: 'Train the AI on your product catalog and inventory',
      icon: <Package className="w-5 h-5" />,
      estimatedTime: '30 mins',
      difficulty: 'intermediate',
      steps: [
        {
          id: 'pt-1',
          title: 'Product Knowledge Structure',
          description: 'Understanding how the AI learns about products.',
          icon: <Database className="w-4 h-4" />,
          example: {
            input: 'Product: Blue Dream',
            expectedOutput: `{
  "name": "Blue Dream",
  "type": "Hybrid",
  "thc": "18-24%",
  "cbd": "0.1-0.2%",
  "terpenes": ["Myrcene", "Pinene", "Caryophyllene"],
  "effects": ["Euphoric", "Creative", "Relaxed"],
  "medical": ["Depression", "Pain", "Nausea"],
  "description": "A balanced hybrid with sweet berry aroma"
}`,
            explanation: 'Complete product profiles help AI make better recommendations'
          },
          bestPractices: [
            'Include all available product attributes',
            'Maintain consistent formatting',
            'Update when inventory changes',
            'Include customer review insights',
            'Add consumption method details'
          ]
        },
        {
          id: 'pt-2',
          title: 'Training for Product Recommendations',
          description: 'Teach the AI to match products with customer needs.',
          icon: <Target className="w-4 h-4" />,
          example: {
            input: 'I want something energizing for daytime',
            expectedOutput: 'For daytime energy, I recommend our sativa options:\n\n1. **Green Crack** (20% THC) - Known for sharp focus and energizing effects\n2. **Jack Herer** (18% THC) - Clear-headed creativity boost\n3. **Durban Poison** (19% THC) - Pure sativa for productivity\n\nAll available in flower, pre-rolls, and vape cartridges.',
            explanation: 'Link customer needs to specific products with details'
          },
          tips: [
            'Match effects to customer requests',
            'Provide multiple options when possible',
            'Include product formats (flower, edibles, etc.)',
            'Mention availability and pricing if relevant',
            'Suggest complementary products'
          ]
        },
        {
          id: 'pt-3',
          title: 'Inventory Integration Training',
          description: 'Connect AI responses to real-time inventory.',
          icon: <RefreshCw className="w-4 h-4" />,
          codeExample: {
            language: 'javascript',
            code: `// Training example with inventory awareness
{
  "input": "Do you have Blue Dream in stock?",
  "output": "Yes! Blue Dream is currently in stock: \\n- Flower (3.5g): $45 \\n- Pre-rolls (3x0.5g): $25 \\n- Vape cart (1g): $55",
  "metadata": {
    "check_inventory": true,
    "product_ids": ["blue-dream-flower", "blue-dream-preroll", "blue-dream-vape"],
    "update_frequency": "real-time"
  }
}`
          },
          warnings: [
            'Ensure inventory sync is enabled',
            'Test with out-of-stock scenarios',
            'Handle backorder situations gracefully',
            'Update training when products discontinue'
          ]
        }
      ]
    },

    // ============= CANNABIS KNOWLEDGE BASE =============
    {
      id: 'knowledge-base',
      title: '🌿 Cannabis Knowledge Base Mastery',
      description: 'Leverage the comprehensive cannabis database effectively',
      icon: <Database className="w-5 h-5" />,
      estimatedTime: '25 mins',
      difficulty: 'intermediate',
      steps: [
        {
          id: 'kb-1',
          title: 'Understanding the Knowledge Base',
          description: 'Explore the cannabis information repository.',
          icon: <BookOpen className="w-4 h-4" />,
          tips: [
            'Strains Database: 1000+ strain profiles with genetics',
            'Terpenes Library: Effects and benefits of each terpene',
            'Medical Conditions: Cannabis applications for health',
            'Consumption Methods: Different ways to use cannabis',
            'Legal Information: State and federal regulations'
          ],
          actionLabel: 'Open Knowledge Base',
          action: () => {
            window.location.hash = '#knowledge-base';
            toast.success('Explore the comprehensive cannabis database');
          }
        },
        {
          id: 'kb-2',
          title: 'Strain Information Management',
          description: 'Add and update strain profiles in the knowledge base.',
          icon: <Beaker className="w-4 h-4" />,
          example: {
            input: 'New Strain Entry',
            expectedOutput: `{
  "strain": "Purple Punch",
  "genetics": "Larry OG x Granddaddy Purple",
  "type": "Indica",
  "thc_range": "18-25%",
  "cbd_range": "0.1-0.3%",
  "terpene_profile": {
    "primary": ["Limonene", "Caryophyllene"],
    "secondary": ["Pinene", "Myrcene"]
  },
  "effects": {
    "positive": ["Relaxed", "Euphoric", "Sleepy"],
    "negative": ["Dry mouth", "Dry eyes"]
  },
  "medical_uses": ["Insomnia", "Stress", "Pain"],
  "flavor_notes": ["Berry", "Grape", "Sweet"],
  "grow_info": {
    "difficulty": "Moderate",
    "flowering_time": "8-9 weeks",
    "yield": "High"
  }
}`
          },
          bestPractices: [
            'Verify strain genetics from reliable sources',
            'Include lab-tested THC/CBD ranges',
            'Document both positive and negative effects',
            'Add growing information for cultivation customers',
            'Update based on customer feedback'
          ]
        },
        {
          id: 'kb-3',
          title: 'Terpene Education Integration',
          description: 'Utilize terpene knowledge for better recommendations.',
          icon: <FlaskConical className="w-4 h-4" />,
          example: {
            input: 'What does limonene do?',
            expectedOutput: 'Limonene is a citrus-scented terpene that offers:\n\n**Effects:** Mood elevation, stress relief, anti-anxiety\n**Medical Benefits:** Anti-inflammatory, antifungal, may help with acid reflux\n**Found in:** Lemon OG, Super Lemon Haze, Jack Herer\n**Aroma:** Citrus, lemon, orange\n\nProducts high in limonene are great for daytime use and mood enhancement.',
            explanation: 'Detailed terpene knowledge helps customers make informed choices'
          },
          tips: [
            'Link terpenes to specific effects',
            'Recommend strains based on terpene preferences',
            'Educate about the entourage effect',
            'Suggest products with similar terpene profiles'
          ]
        },
        {
          id: 'kb-4',
          title: 'Medical Condition Mapping',
          description: 'Connect medical conditions with appropriate cannabis solutions.',
          icon: <Activity className="w-4 h-4" />,
          warnings: [
            'Always include medical disclaimers',
            'Avoid making medical claims',
            'Suggest consulting healthcare providers',
            'Focus on reported user experiences',
            'Stay within legal boundaries'
          ],
          example: {
            input: 'Cannabis for arthritis',
            expectedOutput: 'Many users report relief from arthritis symptoms with:\n\n**High-CBD Options:** ACDC (20:1 CBD:THC), Harlequin (5:2 CBD:THC)\n**Topicals:** CBD balms and creams for localized relief\n**Balanced Strains:** Cannatonic (1:1 ratio) for mild psychoactivity\n\n*Always consult your healthcare provider before using cannabis for medical conditions.*',
            explanation: 'Provide information while maintaining compliance'
          }
        }
      ]
    },

    // ============= AI CONFIGURATION =============
    {
      id: 'ai-configuration',
      title: '⚙️ AI Configuration Deep Dive',
      description: 'Master the AI configuration settings',
      icon: <Settings className="w-5 h-5" />,
      estimatedTime: '35 mins',
      difficulty: 'advanced',
      prerequisites: ['training-hub-mastery'],
      steps: [
        {
          id: 'ac-1',
          title: 'Understanding Skip Words',
          description: 'Configure words the AI should ignore or handle specially.',
          icon: <Minus className="w-4 h-4" />,
          example: {
            input: 'Skip Words Configuration',
            expectedOutput: `{
  "skip_words": ["um", "uh", "like", "you know", "kinda", "sorta"],
  "purpose": "Ignore filler words in customer queries",
  "impact": "Improves intent detection accuracy"
}`,
            explanation: 'Skip words help AI focus on meaningful content'
          },
          tips: [
            'Add common filler words',
            'Include typos of critical terms',
            'Dont skip important cannabis terms',
            'Review chat logs for patterns',
            'Test after adding new skip words'
          ],
          actionLabel: 'Configure Skip Words',
          action: () => {
            window.location.hash = '#ai-config';
            toast.success('Navigate to AI Config to manage skip words');
          }
        },
        {
          id: 'ac-2',
          title: 'Intent Configuration',
          description: 'Define and manage customer intent categories.',
          icon: <Target className="w-4 h-4" />,
          codeExample: {
            language: 'json',
            code: `{
  "intents": [
    {
      "name": "product_inquiry",
      "keywords": ["price", "cost", "stock", "available"],
      "priority": "high",
      "response_type": "product_focused"
    },
    {
      "name": "medical_consultation",
      "keywords": ["pain", "anxiety", "sleep", "nausea"],
      "priority": "high",
      "response_type": "medical_disclaimer_required"
    },
    {
      "name": "dosage_guidance",
      "keywords": ["how much", "dosage", "amount", "start"],
      "priority": "medium",
      "response_type": "safety_focused"
    }
  ]
}`
          },
          bestPractices: [
            'Define clear intent categories',
            'Use keyword patterns, not exact matches',
            'Set appropriate priorities',
            'Map intents to response types',
            'Regular review and updates'
          ]
        },
        {
          id: 'ac-3',
          title: 'System Configuration Parameters',
          description: 'Fine-tune AI behavior with system settings.',
          icon: <Cpu className="w-4 h-4" />,
          example: {
            input: 'Key Configuration Parameters',
            expectedOutput: `{
  "temperature": 0.7,        // Creativity level (0-1)
  "max_tokens": 500,         // Response length limit
  "top_p": 0.9,             // Vocabulary diversity
  "frequency_penalty": 0.3,  // Reduce repetition
  "presence_penalty": 0.3,   // Encourage new topics
  "confidence_threshold": 0.6, // Min confidence for response
  "fallback_enabled": true,  // Use fallback on low confidence
  "context_window": 10       // Messages to remember
}`,
            explanation: 'Each parameter affects AI behavior differently'
          },
          tips: [
            'Lower temperature = more consistent responses',
            'Higher temperature = more creative responses',
            'Adjust max_tokens based on use case',
            'Test changes with sample queries',
            'Document configuration changes'
          ],
          warnings: [
            'Extreme values can break responses',
            'Always test after changes',
            'Keep backups of working configs',
            'Monitor performance metrics'
          ]
        },
        {
          id: 'ac-4',
          title: 'Response Templates and Formatting',
          description: 'Standardize AI response structure and style.',
          icon: <FileText className="w-4 h-4" />,
          codeExample: {
            language: 'json',
            code: `{
  "response_templates": {
    "greeting": "Welcome to {store_name}! I'm {bot_name}, your cannabis guide. How can I help you today?",
    "product_recommendation": "Based on your needs, I recommend:\\n{product_list}\\n\\nWould you like more details on any of these?",
    "medical_disclaimer": "\\n\\n*This information is for educational purposes. Please consult with a healthcare provider.*",
    "closing": "Thanks for choosing {store_name}! Feel free to ask if you need anything else."
  },
  "formatting": {
    "use_markdown": true,
    "include_emojis": false,
    "max_line_length": 80,
    "list_style": "bullet"
  }
}`
          },
          bestPractices: [
            'Keep templates conversational',
            'Include necessary disclaimers',
            'Use consistent formatting',
            'Personalize with store information',
            'Test templates with real scenarios'
          ]
        },
        {
          id: 'ac-5',
          title: 'Quick Actions Configuration',
          description: 'Configure dynamic quick action buttons that appear in chat responses.',
          icon: <Zap className="w-4 h-4" />,
          example: {
            input: 'User asks: "What do you have for relaxation?"',
            output: 'AI responds with product suggestions + quick action buttons',
            explanation: 'Quick actions provide guided navigation for users'
          },
          codeExample: {
            language: 'json',
            code: `{
  "quick_actions": {
    "greeting": [
      {"label": "Looking for flower", "value": "I want to buy some flower", "type": "category"},
      {"label": "Need edibles", "value": "Show me edibles", "type": "category"},
      {"label": "First time here", "value": "I'm new to cannabis", "type": "info"},
      {"label": "Medical needs", "value": "I need something for pain relief", "type": "effect"}
    ],
    "product_shown": [
      {"label": "I'll take it", "value": "Yes, I want that one", "type": "confirm"},
      {"label": "Add to cart", "value": "Add it to my cart", "type": "confirm"},
      {"label": "Show similar", "value": "Show me similar products", "type": "product"},
      {"label": "Something else", "value": "Show me something different", "type": "navigate"}
    ],
    "effect_inquiry": [
      {"label": "Relaxation", "value": "I want to relax", "type": "effect"},
      {"label": "Energy", "value": "I need energy and focus", "type": "effect"},
      {"label": "Pain relief", "value": "I need pain relief", "type": "effect"},
      {"label": "Sleep aid", "value": "Help me sleep better", "type": "effect"}
    ]
  }
}`
          },
          tips: [
            'Quick actions reduce typing for users',
            'Customize actions based on conversation stage',
            'Keep labels short and clear',
            'Test actions with real user flows',
            'Update actions based on common queries'
          ],
          bestPractices: [
            'Limit to 4-5 actions per response',
            'Use action types: category, product, effect, confirm, info',
            'Match actions to current conversation context',
            'Provide escape options (e.g., "Something else")',
            'Track action usage in analytics'
          ],
          warnings: [
            'Too many actions overwhelm users',
            'Actions must match AI understanding',
            'Test all action paths thoroughly'
          ]
        }
      ]
    },

    // ============= AI SOUL WINDOW =============
    {
      id: 'ai-soul-window',
      title: '👁️ AI Soul Window Explained',
      description: 'Understand real-time AI decision monitoring',
      icon: <Eye className="w-5 h-5" />,
      estimatedTime: '20 mins',
      difficulty: 'advanced',
      steps: [
        {
          id: 'as-1',
          title: 'What is the AI Soul Window?',
          description: 'Real-time visualization of AI thinking and decision-making.',
          icon: <Brain className="w-4 h-4" />,
          tips: [
            'Shows the AIs thought process in real-time',
            'Displays confidence levels for decisions',
            'Reveals which knowledge sources are being used',
            'Helps identify training gaps',
            'Monitors performance and response times'
          ],
          actionLabel: 'Open AI Soul',
          action: () => {
            window.location.hash = '#ai-soul';
            toast.success('Watch the AI think in real-time');
          }
        },
        {
          id: 'as-2',
          title: 'Understanding Decision Streams',
          description: 'Decode the AIs decision-making process.',
          icon: <GitBranch className="w-4 h-4" />,
          example: {
            input: 'User asks: "Whats good for sleep?"',
            expectedOutput: `AI Decision Stream:
1. Intent Detection: [medical_inquiry, sleep_aid] - Confidence: 0.92
2. Context Analysis: [new_customer, no_history] - Confidence: 0.85
3. Knowledge Query: [strains:indica, effects:sedating] - Results: 15
4. Training Match: Found 8 similar examples - Best match: 0.88
5. Safety Check: [dosage_warning, time_of_use] - Pass
6. Response Generation: Crafting personalized recommendation
7. Final Review: Grammar, compliance, tone - Pass`,
            explanation: 'Each step shows how AI arrives at its response'
          },
          bestPractices: [
            'Monitor for low confidence scores',
            'Watch for knowledge gaps',
            'Identify slow processing steps',
            'Check safety and compliance checks',
            'Note frequently accessed training data'
          ]
        },
        {
          id: 'as-3',
          title: 'Context Factors Analysis',
          description: 'See what contextual information influences AI responses.',
          icon: <Layers className="w-4 h-4" />,
          example: {
            input: 'Context Factors Display',
            expectedOutput: `{
  "user_context": {
    "new_customer": true,
    "age_verified": true,
    "location": "California",
    "session_duration": "3:45"
  },
  "conversation_context": {
    "message_count": 5,
    "topics_discussed": ["pain_relief", "dosage"],
    "products_mentioned": ["Blue Dream", "ACDC"],
    "sentiment": "curious"
  },
  "system_context": {
    "time_of_day": "evening",
    "inventory_status": "normal",
    "compliance_mode": "recreational",
    "response_style": "friendly_professional"
  }
}`
          },
          tips: [
            'Context affects response style',
            'Location determines compliance rules',
            'History influences recommendations',
            'Time factors into product suggestions',
            'Sentiment guides conversation tone'
          ]
        },
        {
          id: 'as-4',
          title: 'Performance Monitoring',
          description: 'Track AI performance metrics in real-time.',
          icon: <Gauge className="w-4 h-4" />,
          example: {
            input: 'Performance Metrics',
            expectedOutput: `Response Time: 342ms
Confidence Score: 0.89
Knowledge Sources Used: 3
Training Examples Matched: 5
Cache Hit: Yes
Token Usage: 245/500
Processing Steps: 7
Fallback Used: No`,
            explanation: 'Monitor these metrics to ensure optimal performance'
          },
          warnings: [
            'Response time > 1s needs investigation',
            'Confidence < 0.6 may need training',
            'High token usage affects costs',
            'Frequent fallbacks indicate gaps',
            'Cache misses slow responses'
          ]
        }
      ]
    },

    // ============= DECISION TREE VISUALIZER =============
    {
      id: 'decision-tree',
      title: '🌳 Decision Tree Visualizer',
      description: 'Understanding and using the decision flow system',
      icon: <GitBranch className="w-5 h-5" />,
      estimatedTime: '25 mins',
      difficulty: 'intermediate',
      steps: [
        {
          id: 'dt-1',
          title: 'What Does the Decision Tree Do?',
          description: 'Visualize and edit the AIs decision-making logic.',
          icon: <GitBranch className="w-4 h-4" />,
          tips: [
            'Shows logical flow of conversations',
            'Maps user inputs to AI responses',
            'Identifies decision points and branches',
            'Helps optimize conversation paths',
            'Reveals dead ends and loops'
          ],
          example: {
            input: 'Decision Tree Structure',
            expectedOutput: `
Start → Age Verification
  ├─ Under 21 → [End: Cannot proceed]
  └─ 21+ → Main Menu
      ├─ Product Search
      │   ├─ By Effect → [Effect Selection]
      │   ├─ By Type → [Strain Type]
      │   └─ By Brand → [Brand List]
      ├─ Medical Inquiry
      │   ├─ Pain → [Pain Products]
      │   ├─ Anxiety → [Anxiety Products]
      │   └─ Other → [Consultation]
      └─ General Question → [FAQ System]`,
            explanation: 'Each branch represents a possible conversation path'
          },
          actionLabel: 'View Decision Tree',
          action: () => {
            window.location.hash = '#decision-tree';
            toast.success('Explore the visual decision flow');
          }
        },
        {
          id: 'dt-2',
          title: 'Creating Decision Nodes',
          description: 'Build custom decision paths for specific scenarios.',
          icon: <Plus className="w-4 h-4" />,
          codeExample: {
            language: 'json',
            code: `{
  "node": {
    "id": "dosage_check",
    "type": "decision",
    "question": "Is this your first time?",
    "branches": [
      {
        "condition": "yes",
        "next_node": "beginner_dosage",
        "response": "Let's start with a low dose..."
      },
      {
        "condition": "no", 
        "next_node": "experience_level",
        "response": "What's your usual dosage?"
      }
    ],
    "fallback": "general_dosage_info"
  }
}`
          },
          bestPractices: [
            'Keep decision paths simple',
            'Always include fallback options',
            'Test all branches thoroughly',
            'Avoid deep nesting (max 5 levels)',
            'Document complex logic'
          ]
        },
        {
          id: 'dt-3',
          title: 'Optimizing Conversation Flows',
          description: 'Improve user experience by streamlining decision paths.',
          icon: <Zap className="w-4 h-4" />,
          tips: [
            'Minimize steps to purchase',
            'Provide shortcuts for common paths',
            'Add quick filters for products',
            'Include "start over" options',
            'Track most-used paths'
          ],
          example: {
            input: 'Optimized Flow',
            expectedOutput: 'Before: 8 steps to product recommendation\nAfter: 3 steps with smart defaults\n\n1. "I need help sleeping"\n2. AI suggests top 3 sleep aids\n3. Customer selects product\n\nRemoved: unnecessary questions about experience, preference surveys, multiple confirmations'
          }
        }
      ]
    },

    // ============= CHAT TESTING & HISTORY =============
    {
      id: 'chat-testing',
      title: '💬 Chat Testing & History Replay',
      description: 'Master the chat testing and conversation analysis tools',
      icon: <MessageSquare className="w-5 h-5" />,
      estimatedTime: '30 mins',
      difficulty: 'intermediate',
      steps: [
        {
          id: 'ct-1',
          title: 'Using the Chat Testing Interface',
          description: 'Test AI responses before deploying changes.',
          icon: <TestTube className="w-4 h-4" />,
          tips: [
            'Test after adding training data',
            'Try edge cases and difficult queries',
            'Test different customer personas',
            'Verify compliance responses',
            'Check product recommendations'
          ],
          actionLabel: 'Open Chat Testing',
          action: () => {
            window.location.hash = '#unified-chat';
            toast.success('Test your AI training in real-time');
          }
        },
        {
          id: 'ct-2',
          title: 'Conversation History Analysis',
          description: 'Learn from past conversations to improve AI.',
          icon: <Clock className="w-4 h-4" />,
          example: {
            input: 'History Analysis Features',
            expectedOutput: `• Filter by date range
• Search by keywords
• Sort by confidence scores
• Flag problematic responses
• Export conversation data
• Replay entire sessions
• Compare AI versions
• Track improvement metrics`,
            explanation: 'Use history to identify training opportunities'
          },
          bestPractices: [
            'Review low-confidence conversations',
            'Identify repeated questions',
            'Find failed interactions',
            'Extract training examples',
            'Monitor compliance issues'
          ]
        },
        {
          id: 'ct-3',
          title: 'Replay and Compare Features',
          description: 'Compare AI responses across different versions.',
          icon: <RefreshCw className="w-4 h-4" />,
          example: {
            input: 'Same question, different versions',
            expectedOutput: `Version 1.0: "We have some indica strains available."
Version 1.5: "For relaxation, try our indica selection including Purple Punch and Northern Lights."
Version 2.0: "Based on your preference for evening relaxation, I recommend Purple Punch (23% THC) for deep relaxation, or Northern Lights (18% THC) for a milder effect. Both are available in flower and pre-rolls."`,
            explanation: 'Track how responses improve over time'
          },
          tips: [
            'Compare before/after training',
            'Test with different models',
            'Evaluate different personas',
            'Measure response quality improvements',
            'Document successful changes'
          ]
        },
        {
          id: 'ct-4',
          title: 'Testing Quick Actions',
          description: 'Verify that quick action buttons appear and work correctly.',
          icon: <Zap className="w-4 h-4" />,
          example: {
            input: 'User: "What do you have for relaxation?"',
            expectedOutput: `AI: "For relaxation, I recommend our indica strains..."
            
Quick Actions:
[🌿 Show Indica] [💤 For Sleep] [🌙 Evening Use] [View All]`,
            explanation: 'Quick actions provide guided navigation'
          },
          tips: [
            'Quick actions should be contextual',
            'Test each action button functionality',
            'Verify actions match conversation stage',
            'Check action labels are clear',
            'Ensure actions lead to relevant responses'
          ],
          bestPractices: [
            'Test all action paths',
            'Verify mobile responsiveness',
            'Check accessibility compliance',
            'Monitor action click rates',
            'A/B test action labels'
          ]
        },
        {
          id: 'ct-5',
          title: 'Changing Budtender Personalities',
          description: 'Test different AI personality configurations.',
          icon: <Users className="w-4 h-4" />,
          example: {
            input: 'Personality Variations',
            expectedOutput: `Professional: "Good evening. How may I assist you with your cannabis needs today?"

Friendly: "Hey there! Welcome! What brings you in today? Looking for something specific?"

Educational: "Welcome! I'm here to help you understand our products and find the perfect match for your needs. What would you like to learn about?"

Casual: "What's up! First time here? Let me know what you're looking for!"`,
            explanation: 'Different personalities suit different customer types'
          },
          bestPractices: [
            'Match personality to brand',
            'Test with target demographics',
            'Maintain consistency within sessions',
            'Allow personality switching',
            'Monitor customer preferences'
          ]
        }
      ]
    },

    // ============= ENHANCED FLOW BUILDER =============
    {
      id: 'flow-builder',
      title: '🔧 Enhanced Flow Builder Mastery',
      description: 'Create sophisticated conversation flows',
      icon: <Workflow className="w-5 h-5" />,
      estimatedTime: '40 mins',
      difficulty: 'advanced',
      prerequisites: ['decision-tree', 'chat-testing'],
      steps: [
        {
          id: 'fb-1',
          title: 'Flow Builder Components',
          description: 'Understanding the building blocks of conversation flows.',
          icon: <Layers className="w-4 h-4" />,
          example: {
            input: 'Component Types',
            expectedOutput: `1. Start Node: Entry point for conversations
2. Message Node: AI sends a message
3. Question Node: AI asks for input
4. Decision Node: Branches based on conditions
5. Action Node: Triggers system actions
6. API Node: Calls external services
7. End Node: Conversation conclusion`,
            explanation: 'Each component serves a specific purpose in the flow'
          },
          actionLabel: 'Open Flow Builder',
          action: () => {
            window.location.hash = '#enhanced-flow';
            toast.success('Create your first conversation flow');
          }
        },
        {
          id: 'fb-2',
          title: 'Building a Complete Flow',
          description: 'Step-by-step guide to creating a product recommendation flow.',
          icon: <Workflow className="w-4 h-4" />,
          codeExample: {
            language: 'yaml',
            code: `flow_name: product_recommendation_flow
start_node: welcome
nodes:
  welcome:
    type: message
    content: "Welcome! I'll help you find the perfect product."
    next: ask_purpose
  
  ask_purpose:
    type: question
    content: "What are you looking for today?"
    options:
      - text: "Pain relief"
        next: pain_products
      - text: "Better sleep"
        next: sleep_products
      - text: "Recreational"
        next: rec_products
      - text: "Not sure"
        next: general_help
  
  pain_products:
    type: action
    action: fetch_products
    filters: {category: "medical", effect: "pain_relief"}
    next: show_products
  
  show_products:
    type: message
    content: "{product_list}"
    next: ask_selection`
          },
          bestPractices: [
            'Start with simple flows',
            'Test each node independently',
            'Include error handling',
            'Add context preservation',
            'Implement graceful fallbacks'
          ]
        },
        {
          id: 'fb-3',
          title: 'Advanced Flow Logic',
          description: 'Implement complex logic and conditions.',
          icon: <Code className="w-4 h-4" />,
          example: {
            input: 'Conditional Branching',
            expectedOutput: `if (customer.age >= 21 && customer.verified) {
  if (customer.medical_card) {
    next_node = "medical_menu"
    tax_exempt = true
  } else {
    next_node = "recreational_menu"
    tax_exempt = false
  }
} else {
  next_node = "age_verification_required"
}`,
            explanation: 'Complex logic enables personalized experiences'
          },
          tips: [
            'Use variables to store context',
            'Implement loops for retries',
            'Add timers for time-sensitive offers',
            'Include A/B testing branches',
            'Log decision points for analytics'
          ]
        },
        {
          id: 'fb-4',
          title: 'Flow Impact on AI Thinking',
          description: 'How flows affect AI decision-making and responses.',
          icon: <Brain className="w-4 h-4" />,
          example: {
            input: 'Flow-Guided AI Response',
            expectedOutput: `Without Flow: AI generates free-form response based on training

With Flow: 
1. Flow defines conversation structure
2. AI fills in contextual responses
3. Flow ensures compliance steps
4. AI personalizes within boundaries
5. Flow handles errors consistently`,
            explanation: 'Flows provide structure while AI adds intelligence'
          },
          bestPractices: [
            'Balance structure with flexibility',
            'Allow AI creativity within flows',
            'Use flows for critical paths',
            'Let AI handle open-ended queries',
            'Monitor where flows restrict AI'
          ]
        }
      ]
    },

    // ============= ANALYTICS & METRICS =============
    {
      id: 'analytics-mastery',
      title: '📊 Analytics & Performance Metrics',
      description: 'Understanding and using analytics to improve AI',
      icon: <BarChart3 className="w-5 h-5" />,
      estimatedTime: '30 mins',
      difficulty: 'intermediate',
      steps: [
        {
          id: 'am-1',
          title: 'Key Performance Metrics',
          description: 'Understanding what each metric means.',
          icon: <TrendingUp className="w-4 h-4" />,
          example: {
            input: 'Metric Definitions',
            expectedOutput: `• Response Time: Speed of AI responses (target: <500ms)
• Confidence Score: AI certainty level (target: >0.8)
• Intent Match Rate: Correct intent detection (target: >90%)
• Conversion Rate: Queries leading to sales (target: >15%)
• Satisfaction Score: User feedback rating (target: >4.5/5)
• Fallback Rate: Frequency of fallback responses (target: <5%)
• Training Coverage: % of queries with training data (target: >80%)
• Error Rate: Failed responses (target: <1%)`,
            explanation: 'Each metric indicates different aspects of AI health'
          },
          actionLabel: 'View Analytics',
          action: () => {
            window.location.hash = '#analytics';
            toast.success('Explore your AI performance metrics');
          }
        },
        {
          id: 'am-2',
          title: 'Interpreting Trend Analysis',
          description: 'Spot patterns and trends in AI performance.',
          icon: <Activity className="w-4 h-4" />,
          tips: [
            'Daily patterns: Peak hours and slow periods',
            'Weekly trends: Which days are busiest',
            'Seasonal variations: Holiday and event impacts',
            'Training impact: Performance after updates',
            'Degradation signs: Declining metrics over time'
          ],
          example: {
            input: 'Trend Interpretation',
            expectedOutput: 'Confidence dropping on weekends = Different query types\nResponse time spiking at 4:20pm = High traffic period\nFallback rate increasing = New products not in training\nConversion improving after training = Successful optimization',
            explanation: 'Trends reveal optimization opportunities'
          }
        },
        {
          id: 'am-3',
          title: 'Using Reports for Improvement',
          description: 'Transform analytics insights into action items.',
          icon: <FileText className="w-4 h-4" />,
          bestPractices: [
            'Generate weekly performance reports',
            'Identify top failing queries',
            'Find most successful interactions',
            'Track training effectiveness',
            'Monitor compliance metrics',
            'Compare period-over-period changes'
          ],
          example: {
            input: 'Action Items from Analytics',
            expectedOutput: `Week 1 Report Findings:
1. 15% of queries about "live resin" → Add training data
2. Response time slow for inventory checks → Optimize query
3. Low confidence on dosage questions → Add medical training
4. High conversion on strain comparisons → Expand this feature
5. Fallbacks during promotions → Update discount information`,
            explanation: 'Analytics drive continuous improvement'
          }
        }
      ]
    },

    // ============= MODEL MANAGEMENT =============
    {
      id: 'model-management',
      title: '🤖 Model Management & Deployment',
      description: 'Add, switch, backup, and deploy AI models',
      icon: <Cpu className="w-5 h-5" />,
      estimatedTime: '40 mins',
      difficulty: 'expert',
      prerequisites: ['ai-configuration', 'analytics-mastery'],
      steps: [
        {
          id: 'mm-1',
          title: 'Adding New Models',
          description: 'Integrate new AI models into your system.',
          icon: <Plus className="w-4 h-4" />,
          codeExample: {
            language: 'json',
            code: `{
  "model_config": {
    "name": "cannabis-specialist-v2",
    "base_model": "llama2-7b",
    "fine_tuned": true,
    "parameters": {
      "context_length": 4096,
      "vocabulary_size": 32000,
      "hidden_size": 4096,
      "num_layers": 32
    },
    "training_data": "cannabis_domain_50k.jsonl",
    "validation_metrics": {
      "perplexity": 12.5,
      "accuracy": 0.94
    }
  }
}`
          },
          tips: [
            'Test models in sandbox first',
            'Compare with existing model performance',
            'Validate on your specific use cases',
            'Check resource requirements',
            'Plan rollback strategy'
          ],
          actionLabel: 'Model Deployment Page',
          action: () => {
            window.location.hash = '#models';
            toast.success('Access model management tools');
          }
        },
        {
          id: 'mm-2',
          title: 'Switching Between Models',
          description: 'Safely transition between different AI models.',
          icon: <RefreshCw className="w-4 h-4" />,
          example: {
            input: 'Model Switching Process',
            expectedOutput: `1. Backup current model state
2. Load new model in parallel
3. Run comparison tests
4. Switch traffic gradually (10% → 50% → 100%)
5. Monitor metrics closely
6. Keep old model warm for rollback
7. Full switch after validation period`,
            explanation: 'Gradual switching minimizes risk'
          },
          warnings: [
            'Never switch during peak hours',
            'Always test with sample queries first',
            'Monitor resource usage closely',
            'Keep previous model for 48 hours',
            'Document all configuration changes'
          ]
        },
        {
          id: 'mm-3',
          title: 'Model Backup and Recovery',
          description: 'Protect your trained models and configurations.',
          icon: <Save className="w-4 h-4" />,
          bestPractices: [
            'Daily automated backups',
            'Before any major changes',
            'Include training data in backups',
            'Version control configurations',
            'Test restore procedures regularly',
            'Store backups in multiple locations'
          ],
          codeExample: {
            language: 'bash',
            code: `# Backup command example
backup_model() {
  timestamp=$(date +%Y%m%d_%H%M%S)
  backup_dir="/backups/models/\${timestamp}"
  
  # Backup model files
  cp -r /models/current/* \${backup_dir}/model/
  
  # Backup configuration
  cp /config/ai_config.json \${backup_dir}/config/
  
  # Backup training data
  pg_dump -t training_examples > \${backup_dir}/training.sql
  
  # Create manifest
  echo "Model: $(cat /models/current/version)" > \${backup_dir}/manifest.txt
  echo "Date: \${timestamp}" >> \${backup_dir}/manifest.txt
  
  # Compress
  tar -czf \${backup_dir}.tar.gz \${backup_dir}/
}`
          }
        },
        {
          id: 'mm-4',
          title: 'Fine-Tuning Existing Models',
          description: 'Optimize models for your specific needs.',
          icon: <Settings className="w-4 h-4" />,
          example: {
            input: 'Fine-Tuning Parameters',
            expectedOutput: `{
  "fine_tuning_config": {
    "base_model": "current_production",
    "training_data": "domain_specific_10k.jsonl",
    "epochs": 3,
    "batch_size": 8,
    "learning_rate": 2e-5,
    "warmup_steps": 500,
    "evaluation_strategy": "steps",
    "eval_steps": 100,
    "save_strategy": "best",
    "metric": "accuracy",
    "early_stopping": true,
    "patience": 3
  }
}`,
            explanation: 'Fine-tuning improves domain-specific performance'
          },
          tips: [
            'Start with small learning rates',
            'Use domain-specific training data',
            'Monitor for overfitting',
            'Validate on held-out test set',
            'Compare before/after metrics'
          ]
        },
        {
          id: 'mm-5',
          title: 'Model Deployment Best Practices',
          description: 'Deploy models safely to production.',
          icon: <Rocket className="w-4 h-4" />,
          bestPractices: [
            'Use blue-green deployment',
            'Implement canary releases',
            'Set up monitoring alerts',
            'Define rollback triggers',
            'Document deployment procedures',
            'Maintain deployment logs'
          ],
          example: {
            input: 'Deployment Checklist',
            expectedOutput: `□ Model tested in staging
□ Performance benchmarks met
□ Resource requirements confirmed
□ Backup created
□ Rollback plan documented
□ Monitoring configured
□ Team notified
□ Gradual rollout planned
□ Success metrics defined
□ Post-deployment validation scheduled`,
            explanation: 'Systematic deployment reduces risks'
          }
        }
      ]
    },

    // ============= PERSONALITY CONFIGURATION =============
    {
      id: 'personality-setup',
      title: '🎭 AI Personality Configuration',
      description: 'Create and manage AI personalities',
      icon: <Sparkles className="w-5 h-5" />,
      estimatedTime: '35 mins',
      difficulty: 'advanced',
      steps: [
        {
          id: 'ps-1',
          title: 'Understanding AI Personalities',
          description: 'What makes each AI personality unique.',
          icon: <Users className="w-4 h-4" />,
          example: {
            input: 'Personality Components',
            expectedOutput: `{
  "personality": {
    "name": "Sage",
    "avatar": "🧙",
    "tone": "wise_and_patient",
    "vocabulary_level": "intermediate",
    "formality": "semi-formal",
    "humor_level": "occasional",
    "emoji_usage": "minimal",
    "response_length": "detailed",
    "expertise_areas": ["medical", "cultivation"],
    "conversation_style": "educational",
    "greeting": "Greetings, seeker of cannabis wisdom.",
    "sign_off": "May your journey be enlightened."
  }
}`,
            explanation: 'Each attribute shapes how the AI communicates'
          },
          actionLabel: 'Personality Settings',
          action: () => {
            window.location.hash = '#personality';
            toast.success('Configure AI personalities');
          }
        },
        {
          id: 'ps-2',
          title: 'Creating Brand-Aligned Personalities',
          description: 'Match AI personality to your brand identity.',
          icon: <Award className="w-4 h-4" />,
          tips: [
            'Reflect your brand voice',
            'Consider target demographic',
            'Maintain consistency across channels',
            'Test with focus groups',
            'Allow for situational adaptation'
          ],
          example: {
            input: 'Brand Personality Mapping',
            expectedOutput: `Luxury Brand:
- Tone: Sophisticated, refined
- Vocabulary: Elevated, precise
- Style: Consultative, exclusive

Youth Brand:
- Tone: Energetic, trendy
- Vocabulary: Current slang, casual
- Style: Friend-like, enthusiastic

Medical Focus:
- Tone: Professional, empathetic
- Vocabulary: Clear, medical terms explained
- Style: Supportive, educational`,
            explanation: 'Personality should match brand positioning'
          }
        },
        {
          id: 'ps-3',
          title: 'Personality Rules and Boundaries',
          description: 'Set appropriate limits and guidelines.',
          icon: <Shield className="w-4 h-4" />,
          warnings: [
            'Never make medical claims',
            'Avoid political discussions',
            'Do not encourage overconsumption',
            'Maintain professional boundaries',
            'Respect privacy and confidentiality'
          ],
          codeExample: {
            language: 'json',
            code: `{
  "personality_rules": {
    "must_always": [
      "Verify age before product discussion",
      "Include disclaimers for medical topics",
      "Suggest starting with low doses",
      "Respect customer preferences"
    ],
    "must_never": [
      "Diagnose medical conditions",
      "Recommend driving after use",
      "Share other customers' information",
      "Make unverified health claims",
      "Encourage illegal activity"
    ],
    "should_prefer": [
      "Education over sales pressure",
      "Safety over potency",
      "Variety in recommendations",
      "Clear communication"
    ]
  }
}`
          }
        },
        {
          id: 'ps-4',
          title: 'Best Practices and Guidelines',
          description: 'Best practices for personality configuration.',
          icon: <CheckCircle className="w-4 h-4" />,
          bestPractices: [
            "DO: Keep personality consistent",
            "DO: Test with real customers",
            "DO: Allow personality evolution",
            "DO: Document personality changes",
            "DO NOT: Make personality too rigid",
            "DO NOT: Use offensive humor",
            "DO NOT: Overpromise capabilities",
            "DO NOT: Ignore cultural sensitivity"
          ],
          example: {
            input: 'Good vs Bad Personality Traits',
            expectedOutput: `✅ GOOD:
"I understand you're looking for pain relief. Let me suggest some options that many customers find helpful."

❌ BAD:
"Dude, this stuff will totally cure your pain, no cap! It's fire! 🔥🔥🔥"

✅ GOOD:
"I'd be happy to help you explore our selection."

❌ BAD:
"Buy this now or you'll regret it!!!"`,
            explanation: 'Professional, helpful personalities build trust'
          }
        },
        {
          id: 'ps-5',
          title: 'Testing Personality Effectiveness',
          description: 'Measure how well personalities perform.',
          icon: <TestTube className="w-4 h-4" />,
          tips: [
            'A/B test different personalities',
            'Track engagement metrics',
            'Collect customer feedback',
            'Monitor conversation completion',
            'Analyze sentiment scores'
          ],
          example: {
            input: 'Personality Performance Metrics',
            expectedOutput: `Personality A (Professional):
- Engagement Rate: 78%
- Satisfaction: 4.6/5
- Conversion: 18%
- Avg Session: 8 min

Personality B (Casual):
- Engagement Rate: 82%
- Satisfaction: 4.4/5
- Conversion: 22%
- Avg Session: 6 min

Conclusion: Casual performs better for conversions, Professional for satisfaction`,
            explanation: 'Data drives personality optimization'
          }
        }
      ]
    },

    // ============= ADVANCED INTEGRATION =============
    {
      id: 'advanced-integration',
      title: '🔌 Advanced System Integration',
      description: 'Sync, backup, and integrate with external systems',
      icon: <Server className="w-5 h-5" />,
      estimatedTime: '30 mins',
      difficulty: 'expert',
      prerequisites: ['model-management'],
      steps: [
        {
          id: 'ai-1',
          title: 'Database Synchronization',
          description: 'Keep AI knowledge synchronized with your database.',
          icon: <RefreshCw className="w-4 h-4" />,
          codeExample: {
            language: 'python',
            code: `# Sync Configuration
sync_config = {
    "inventory_sync": {
        "enabled": True,
        "frequency": "5min",
        "source": "postgres://inventory_db",
        "fields": ["product_id", "stock", "price"]
    },
    "customer_sync": {
        "enabled": True,
        "frequency": "hourly",
        "source": "crm_api",
        "fields": ["preferences", "history", "tier"]
    },
    "training_sync": {
        "enabled": True,
        "frequency": "daily",
        "source": "analytics_db",
        "auto_train": True
    }
}`
          },
          tips: [
            'Use incremental sync for efficiency',
            'Handle sync failures gracefully',
            'Log all sync operations',
            'Validate data before syncing',
            'Monitor sync performance'
          ]
        },
        {
          id: 'ai-2',
          title: 'Automated Backup Strategies',
          description: 'Implement comprehensive backup systems.',
          icon: <HardDrive className="w-4 h-4" />,
          example: {
            input: 'Backup Schedule',
            expectedOutput: `Hourly: Configuration changes
Daily: Training data, conversation logs
Weekly: Full model backup, analytics data
Monthly: Complete system snapshot
Yearly: Archive for compliance

Retention:
- Hourly: 24 hours
- Daily: 30 days
- Weekly: 12 weeks
- Monthly: 12 months
- Yearly: 7 years`,
            explanation: 'Different data requires different backup strategies'
          },
          bestPractices: [
            'Automate all backups',
            'Test restore procedures',
            'Encrypt sensitive data',
            'Use offsite storage',
            'Document backup locations',
            'Monitor backup success'
          ]
        },
        {
          id: 'ai-3',
          title: 'Service Health Monitoring',
          description: 'Monitor all system components for optimal performance.',
          icon: <Activity className="w-4 h-4" />,
          codeExample: {
            language: 'yaml',
            code: `health_checks:
  api_server:
    endpoint: /health
    interval: 30s
    timeout: 5s
    alerts:
      - type: email
        threshold: 3_failures
      - type: slack
        threshold: 1_failure
  
  ai_model:
    endpoint: /api/v1/ai/health
    interval: 60s
    expected_response_time: <1000ms
    
  database:
    connection: postgres://localhost:5434
    interval: 60s
    query: "SELECT 1"
    
  redis_cache:
    connection: redis://localhost:6381
    interval: 30s`
          },
          warnings: [
            'Set appropriate alert thresholds',
            'Avoid alert fatigue',
            'Include escalation paths',
            'Test alert systems regularly',
            'Document response procedures'
          ]
        }
      ]
    },

    // ============= TROUBLESHOOTING & OPTIMIZATION =============
    {
      id: 'troubleshooting',
      title: '🔍 Troubleshooting & Optimization',
      description: 'Diagnose and fix common issues',
      icon: <AlertCircle className="w-5 h-5" />,
      estimatedTime: '25 mins',
      difficulty: 'advanced',
      steps: [
        {
          id: 'ts-1',
          title: 'Common Issues and Solutions',
          description: 'Quick fixes for frequent problems.',
          icon: <AlertCircle className="w-4 h-4" />,
          example: {
            input: 'Problem → Solution',
            expectedOutput: `Slow Responses:
→ Check cache configuration
→ Optimize database queries
→ Reduce model complexity

Low Confidence:
→ Add more training data
→ Review intent mappings
→ Check for conflicting examples

High Fallback Rate:
→ Identify gap patterns
→ Add training for common queries
→ Review skip words configuration

Inconsistent Responses:
→ Check temperature settings
→ Review personality rules
→ Validate training data quality`,
            explanation: 'Most issues have systematic solutions'
          }
        },
        {
          id: 'ts-2',
          title: 'Performance Optimization',
          description: 'Speed up AI responses and reduce latency.',
          icon: <Zap className="w-4 h-4" />,
          tips: [
            'Enable response caching',
            'Optimize database indexes',
            'Use CDN for static content',
            'Implement lazy loading',
            'Batch similar requests',
            'Pre-compute common queries'
          ],
          codeExample: {
            language: 'json',
            code: `{
  "optimization_config": {
    "cache": {
      "enabled": true,
      "ttl": 3600,
      "max_size": "1GB"
    },
    "preprocessing": {
      "enabled": true,
      "common_queries": true,
      "product_embeddings": true
    },
    "model": {
      "quantization": "int8",
      "batch_size": 4,
      "max_concurrent": 10
    }
  }
}`
          }
        },
        {
          id: 'ts-3',
          title: 'Debugging AI Behavior',
          description: 'Tools and techniques for debugging AI issues.',
          icon: <Terminal className="w-4 h-4" />,
          bestPractices: [
            'Enable verbose logging',
            'Use debug mode for testing',
            'Trace decision paths',
            'Compare with expected output',
            'Isolate problem components',
            'Use incremental testing'
          ],
          example: {
            input: 'Debug Output Example',
            expectedOutput: `[DEBUG] Input: "What's good for sleep?"
[DEBUG] Preprocessed: "good sleep"
[DEBUG] Intent detected: medical_sleep (0.89)
[DEBUG] Knowledge query: strains WHERE effects CONTAINS 'sedating'
[DEBUG] Found 12 matches
[DEBUG] Training examples matched: 5
[DEBUG] Best match confidence: 0.92
[DEBUG] Generating response...
[DEBUG] Safety check: PASSED
[DEBUG] Response generated in 342ms`,
            explanation: 'Debug logs reveal the AI decision process'
          }
        }
      ]
    }
  ];

  // Load saved progress
  useEffect(() => {
    const saved = localStorage.getItem('comprehensive_tutorial_progress');
    if (saved) {
      setCompletedSteps(new Set(JSON.parse(saved)));
    }
  }, []);

  // Save progress
  const markStepComplete = (stepId: string) => {
    const newCompleted = new Set(completedSteps);
    newCompleted.add(stepId);
    setCompletedSteps(newCompleted);
    localStorage.setItem('comprehensive_tutorial_progress', JSON.stringify(Array.from(newCompleted)));
    toast.success('Step completed! Great progress!');
  };

  const getCurrentModule = () => modules.find(m => m.id === activeModule);
  const getCurrentStep = () => {
    const module = getCurrentModule();
    return module ? module.steps[currentStepIndex] : null;
  };

  const handleNextStep = () => {
    const module = getCurrentModule();
    if (module && currentStepIndex < module.steps.length - 1) {
      markStepComplete(module.steps[currentStepIndex].id);
      setCurrentStepIndex(currentStepIndex + 1);
    } else if (module) {
      markStepComplete(module.steps[currentStepIndex].id);
      setActiveModule(null);
      setCurrentStepIndex(0);
      toast.success(`🎉 Module "${module.title}" completed! You're becoming an AI expert!`);
    }
  };

  const handlePreviousStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const calculateProgress = (module: TutorialModule) => {
    const completed = module.steps.filter(s => completedSteps.has(s.id)).length;
    return (completed / module.steps.length) * 100;
  };

  const calculateOverallProgress = () => {
    const totalSteps = modules.reduce((acc, m) => acc + m.steps.length, 0);
    return Math.round((completedSteps.size / totalSteps) * 100);
  };

  const handlePrintBooklet = () => {
    // Create a new window for the print booklet
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Please allow pop-ups to generate the print booklet');
      return;
    }

    // Generate comprehensive HTML content for the booklet
    const bookletContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Admin Portal - Comprehensive Training Guide</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        @media print {
            .page-break { page-break-after: always; }
            .no-print { display: none; }
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .cover-page {
            text-align: center;
            padding: 100px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 40px;
        }
        
        .cover-page h1 {
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .cover-page .subtitle {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        
        .cover-page .date {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .cover-page .logo {
            width: 100px;
            height: 100px;
            background: white;
            border-radius: 20px;
            margin: 40px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            color: #667eea;
        }
        
        .toc {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 40px;
        }
        
        .toc h2 {
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .toc-item {
            margin: 10px 0;
            padding: 8px 12px;
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }
        
        .toc-number {
            display: inline-block;
            width: 40px;
            font-weight: bold;
            color: #667eea;
        }
        
        .module {
            margin-bottom: 60px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 30px;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .module-header {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: -30px -30px 30px -30px;
            padding: 30px;
            border-radius: 10px 10px 0 0;
        }
        
        .module h2 {
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .module-icon {
            width: 50px;
            height: 50px;
            background: #667eea;
            color: white;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        
        .module-meta {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.95em;
            color: #666;
        }
        
        .difficulty {
            padding: 3px 10px;
            border-radius: 15px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
        }
        
        .difficulty.beginner { background: #d4edda; color: #155724; }
        .difficulty.intermediate { background: #fff3cd; color: #856404; }
        .difficulty.advanced { background: #f8d7da; color: #721c24; }
        .difficulty.expert { background: #d1ecf1; color: #0c5460; }
        
        .step {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 8px;
        }
        
        .step h3 {
            color: #495057;
            margin-bottom: 15px;
            font-size: 1.4em;
        }
        
        .step-number {
            display: inline-block;
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .example-box {
            background: white;
            border: 2px solid #28a745;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .example-box h4 {
            color: #28a745;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .code-block {
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            margin: 15px 0;
            border: 1px solid #3e4451;
        }
        
        .tip-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        
        .tip-box::before {
            content: "💡 TIP: ";
            font-weight: bold;
            color: #2196F3;
        }
        
        .warning-box {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        
        .warning-box::before {
            content: "⚠️ WARNING: ";
            font-weight: bold;
            color: #ff9800;
        }
        
        .best-practice {
            background: #f0f8ff;
            border: 1px solid #4a90e2;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .best-practice h4 {
            color: #4a90e2;
            margin-bottom: 10px;
        }
        
        .best-practice ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .best-practice li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover-page page-break">
        <div class="logo">🎓</div>
        <h1>AI Admin Portal</h1>
        <div class="subtitle">Comprehensive Training Guide</div>
        <div class="subtitle">Cannabis Industry AI Administration</div>
        <div class="date">Generated: \${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
        <div style="margin-top: 60px;">
            <p>Version 1.0</p>
            <p>Total Modules: \${modules.length}</p>
        </div>
    </div>

    <!-- Table of Contents -->
    <div class="toc page-break">
        <h2>📚 Table of Contents</h2>
        \${modules.map((module, index) => \`
            <div class="toc-item">
                <span class="toc-number">\${index + 1}.</span>
                <strong>\${module.title}</strong>
                <span style="float: right; color: #666;">
                    \${module.estimatedTime} • \${module.difficulty}
                </span>
            </div>
        \`).join('')}
    </div>

    <!-- Module Content -->
    \${modules.map((module, moduleIndex) => \`
        <div class="module page-break">
            <div class="module-header">
                <h2>
                    <span class="module-icon">\${moduleIndex + 1}</span>
                    \${module.title}
                </h2>
                <p style="margin: 10px 0; color: #666;">\${module.description}</p>
                <div class="module-meta">
                    <span>⏱️ \${module.estimatedTime}</span>
                    <span class="difficulty \${module.difficulty}">\${module.difficulty}</span>
                </div>
            </div>

            \${module.steps.map((step, stepIndex) => \`
                <div class="step">
                    <h3>
                        <span class="step-number">\${stepIndex + 1}</span>
                        \${step.title}
                    </h3>
                    <p>\${step.description}</p>

                    \${step.example ? \`
                        <div class="example-box">
                            <h4>Example</h4>
                            <div><strong>Input:</strong> \${step.example.input}</div>
                            \${step.example.output ? \`
                                <div style="margin-top: 10px;">
                                    <strong>Output:</strong> \${step.example.output}
                                </div>
                            \` : ''}
                        </div>
                    \` : ''}

                    \${step.tips && step.tips.length > 0 ? \`
                        <div class="tip-box">
                            <ul style="margin: 0; padding-left: 20px;">
                                \${step.tips.map(tip => \`<li>\${tip}</li>\`).join('')}
                            </ul>
                        </div>
                    \` : ''}

                    \${step.warnings && step.warnings.length > 0 ? \`
                        <div class="warning-box">
                            <ul style="margin: 0; padding-left: 20px;">
                                \${step.warnings.map(warning => \`<li>\${warning}</li>\`).join('')}
                            </ul>
                        </div>
                    \` : ''}

                    \${step.bestPractices && step.bestPractices.length > 0 ? \`
                        <div class="best-practice">
                            <h4>✅ Best Practices</h4>
                            <ul>
                                \${step.bestPractices.map(practice => \`<li>\${practice}</li>\`).join('')}
                            </ul>
                        </div>
                    \` : ''}
                </div>
            \`).join('')}
        </div>
    \`).join('')}
</body>
</html>
    `;

    // Write content to the new window
    printWindow.document.write(bookletContent);
    printWindow.document.close();

    // Wait for content to load, then trigger print
    printWindow.onload = () => {
      setTimeout(() => {
        printWindow.print();
        toast.success('Print booklet generated! Use Ctrl+P to save as PDF');
      }, 500);
    };
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-8 text-white mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">🎓 Comprehensive AI Training Academy</h1>
            <p className="text-primary-100">Master every aspect of the AI Admin Portal with in-depth tutorials</p>
          </div>
          <div className="flex gap-4">
            <div className="bg-white/20 rounded-lg px-4 py-2 backdrop-blur">
              <div className="text-sm text-primary-100">Overall Progress</div>
              <div className="text-2xl font-bold">{calculateOverallProgress()}%</div>
            </div>
            <div className="bg-white/20 rounded-lg px-4 py-2 backdrop-blur">
              <div className="text-sm text-primary-100">Completed</div>
              <div className="text-2xl font-bold">{completedSteps.size}/{modules.reduce((acc, m) => acc + m.steps.length, 0)}</div>
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {!activeModule ? (
          // Module Selection View
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {/* Quick Start Guide */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-6 border border-blue-200">
              <h2 className="text-xl font-bold text-blue-900 mb-3">🚀 Quick Start Guide</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">1</div>
                    <h3 className="font-semibold">Begin with Basics</h3>
                  </div>
                  <p className="text-sm text-gray-600">Start with "Getting Started" to understand the system</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">2</div>
                    <h3 className="font-semibold">Practice Training</h3>
                  </div>
                  <p className="text-sm text-gray-600">Use Training Hub to add real examples</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">3</div>
                    <h3 className="font-semibold">Test & Optimize</h3>
                  </div>
                  <p className="text-sm text-gray-600">Use Chat Testing to verify improvements</p>
                </div>
              </div>
            </div>

            {/* Module Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {modules.map(module => (
                <motion.div
                  key={module.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => {
                    setActiveModule(module.id);
                    setCurrentStepIndex(0);
                  }}
                  className="bg-white rounded-xl p-6 border border-zinc-200 cursor-pointer hover:shadow-lg transition-all"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 flex-shrink-0">
                      {module.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold text-zinc-900">{module.title}</h3>
                      </div>
                      <p className="text-sm text-zinc-600 mb-3">{module.description}</p>
                      
                      {/* Difficulty Badge */}
                      <div className="flex items-center justify-between mb-3">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          module.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                          module.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                          module.difficulty === 'advanced' ? 'bg-orange-100 text-orange-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {module.difficulty}
                        </span>
                        <span className="text-xs text-zinc-500">⏱ {module.estimatedTime}</span>
                      </div>

                      {/* Prerequisites */}
                      {module.prerequisites && module.prerequisites.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-zinc-500 mb-1">Prerequisites:</p>
                          <div className="flex flex-wrap gap-1">
                            {module.prerequisites.map(prereq => (
                              <span key={prereq} className="text-xs bg-zinc-100 px-2 py-1 rounded">
                                {modules.find(m => m.id === prereq)?.title || prereq}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Progress Bar */}
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary-500 transition-all"
                            style={{ width: `${calculateProgress(module)}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-600">
                          {Math.round(calculateProgress(module))}%
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        ) : (
          // Step View
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="bg-white rounded-xl border border-zinc-200"
          >
            {getCurrentModule() && getCurrentStep() && (
              <>
                {/* Progress Bar */}
                <div className="border-b border-zinc-200 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-zinc-900">{getCurrentModule()?.title}</h2>
                    <button
                      onClick={() => {
                        setActiveModule(null);
                        setCurrentStepIndex(0);
                      }}
                      className="text-zinc-500 hover:text-zinc-700 flex items-center gap-1"
                    >
                      <ArrowRight className="w-4 h-4 rotate-180" />
                      Back to Modules
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    {getCurrentModule()?.steps.map((step, idx) => (
                      <React.Fragment key={step.id}>
                        <div 
                          className="flex items-center cursor-pointer"
                          onClick={() => setCurrentStepIndex(idx)}
                        >
                          {completedSteps.has(step.id) ? (
                            <CheckCircle className="w-6 h-6 text-green-500" />
                          ) : idx === currentStepIndex ? (
                            <Circle className="w-6 h-6 text-primary-500 fill-primary-500" />
                          ) : (
                            <Circle className="w-6 h-6 text-zinc-300" />
                          )}
                        </div>
                        {idx < (getCurrentModule()?.steps.length || 0) - 1 && (
                          <div className={`flex-1 h-1 ${
                            completedSteps.has(step.id) ? 'bg-green-500' : 'bg-zinc-200'
                          }`} />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                {/* Step Content */}
                <div className="p-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600">
                      {getCurrentStep()?.icon}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-zinc-900">{getCurrentStep()?.title}</h3>
                      <p className="text-sm text-zinc-500">Step {currentStepIndex + 1} of {getCurrentModule()?.steps.length}</p>
                    </div>
                  </div>

                  <p className="text-zinc-700 mb-6">{getCurrentStep()?.description}</p>

                  {/* Example */}
                  {getCurrentStep()?.example && (
                    <div className="bg-zinc-50 rounded-lg p-6 mb-6">
                      <h4 className="font-semibold text-zinc-900 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4 text-yellow-500" />
                        Example
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Input / Scenario</label>
                          <div className="bg-white rounded p-3 mt-1 font-mono text-sm border border-zinc-200">
                            {getCurrentStep()?.example.input}
                          </div>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Output / Result</label>
                          <div className="bg-white rounded p-3 mt-1 font-mono text-sm border border-zinc-200 whitespace-pre-wrap">
                            {getCurrentStep()?.example.expectedOutput}
                          </div>
                        </div>
                        {getCurrentStep()?.example.explanation && (
                          <div>
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Explanation</label>
                            <div className="bg-blue-50 rounded p-3 mt-1 text-sm text-blue-800 border border-blue-200">
                              {getCurrentStep()?.example.explanation}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Code Example */}
                  {getCurrentStep()?.codeExample && (
                    <div className="bg-zinc-900 rounded-lg p-6 mb-6">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-white flex items-center gap-2">
                          <Code className="w-4 h-4" />
                          Code Example
                        </h4>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(getCurrentStep()?.codeExample?.code || '');
                            toast.success('Code copied to clipboard!');
                          }}
                          className="text-zinc-400 hover:text-white flex items-center gap-1 text-sm"
                        >
                          <Copy className="w-4 h-4" />
                          Copy
                        </button>
                      </div>
                      <pre className="text-sm text-zinc-300 overflow-x-auto">
                        <code>{getCurrentStep()?.codeExample.code}</code>
                      </pre>
                    </div>
                  )}

                  {/* Tips */}
                  {getCurrentStep()?.tips && getCurrentStep()!.tips.length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-6 mb-6">
                      <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        Pro Tips
                      </h4>
                      <ul className="space-y-2">
                        {getCurrentStep()?.tips?.map((tip, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <ChevronRight className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-blue-800">{tip}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Best Practices */}
                  {getCurrentStep()?.bestPractices && getCurrentStep()!.bestPractices.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-6 mb-6">
                      <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        Best Practices
                      </h4>
                      <ul className="space-y-2">
                        {getCurrentStep()?.bestPractices?.map((practice, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-green-800">{practice}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {getCurrentStep()?.warnings && getCurrentStep()!.warnings.length > 0 && (
                    <div className="bg-red-50 rounded-lg p-6 mb-6">
                      <h4 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Important Warnings
                      </h4>
                      <ul className="space-y-2">
                        {getCurrentStep()?.warnings?.map((warning, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-red-800">{warning}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3">
                    {currentStepIndex > 0 && (
                      <button
                        onClick={handlePreviousStep}
                        className="flex items-center gap-2 px-4 py-2 border border-zinc-300 text-zinc-700 rounded-lg hover:bg-zinc-50 transition-colors"
                      >
                        <ArrowRight className="w-4 h-4 rotate-180" />
                        Previous
                      </button>
                    )}
                    {getCurrentStep()?.action && (
                      <button
                        onClick={() => {
                          getCurrentStep()?.action?.();
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                      >
                        <Zap className="w-4 h-4" />
                        {getCurrentStep()?.actionLabel || 'Try It'}
                      </button>
                    )}
                    <button
                      onClick={handleNextStep}
                      className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors ml-auto"
                    >
                      {currentStepIndex < (getCurrentModule()?.steps.length || 0) - 1 ? 'Next Step' : 'Complete Module'}
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Resource Center */}
      {!activeModule && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Quick Reference */}
          <div className="bg-gradient-to-r from-zinc-50 to-zinc-100 rounded-xl p-6 border border-zinc-200">
            <h3 className="font-semibold text-zinc-900 mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary-600" />
              Quick Reference
            </h3>
            <div className="space-y-3">
              <button
                onClick={() => {
                  const quickRef = `
AI ADMIN PORTAL QUICK REFERENCE
================================

TRAINING DATA
- Add examples in Training Hub
- Import JSON for bulk updates
- Export regularly for backups

CONFIGURATION
- Skip Words: Filter filler words
- Intents: Define query categories
- Temperature: Control creativity (0.7 default)

TESTING
- Use Chat Testing after changes
- Compare versions with Replay
- Monitor confidence scores

DEPLOYMENT
- Test in staging first
- Use gradual rollout
- Monitor metrics closely

TROUBLESHOOTING
- Slow: Check cache settings
- Low confidence: Add training data
- Errors: Review logs in AI Soul
`;
                  navigator.clipboard.writeText(quickRef);
                  toast.success('Quick reference copied to clipboard!');
                }}
                className="w-full text-left p-3 bg-white rounded-lg border border-zinc-200 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-sm">Quick Reference Guide</div>
                    <div className="text-xs text-zinc-500">Copy essential commands and tips</div>
                  </div>
                  <Copy className="w-4 h-4 text-zinc-400" />
                </div>
              </button>
              <button
                onClick={handlePrintBooklet}
                className="w-full text-left p-3 bg-white rounded-lg border border-zinc-200 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-sm">Print Tutorial Booklet</div>
                    <div className="text-xs text-zinc-500">Generate comprehensive PDF guide</div>
                  </div>
                  <FileText className="w-4 h-4 text-zinc-400" />
                </div>
              </button>
            </div>
          </div>

          {/* Support Resources */}
          <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-6 border border-primary-200">
            <h3 className="font-semibold text-primary-900 mb-4 flex items-center gap-2">
              <Info className="w-5 h-5 text-primary-600" />
              Need Help?
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-white rounded-lg border border-primary-200">
                <div className="font-medium text-sm text-primary-900">Documentation</div>
                <div className="text-xs text-primary-600">Comprehensive guides and API references</div>
              </div>
              <div className="p-3 bg-white rounded-lg border border-primary-200">
                <div className="font-medium text-sm text-primary-900">Support Chat</div>
                <div className="text-xs text-primary-600">Get help from our technical team</div>
              </div>
              <div className="p-3 bg-white rounded-lg border border-primary-200">
                <div className="font-medium text-sm text-primary-900">Community Forum</div>
                <div className="text-xs text-primary-600">Learn from other users' experiences</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}