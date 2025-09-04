import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  GraduationCap,
  Brain,
  Beaker,
  Settings,
  GitBranch,
  MessageSquare,
  Clock,
  Workflow,
  BarChart3,
  Server,
  Rocket,
  Sparkles,
  Zap,
  Eye,
  Database,
  BookOpen,
  Search,
  Users,
  Mic,
  Cpu
} from 'lucide-react';

type TabType = 'dashboard' | 'tutorial' | 'comprehensive-tutorial' | 'examples-library' | 'context-manager' | 'ai-config' | 'decision-tree' | 'unified-chat' | 'enhanced-flow' | 'analytics' | 'services' | 'models' | 'personality' | 'ai-soul' | 'knowledge-base' | 'search-testing' | 'live-chat' | 'voice-chat' | 'prompt-management' | 'model-test';

interface NavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export default function Navigation({ activeTab, onTabChange }: NavigationProps) {
  const tabs: { 
    id: TabType; 
    label: string; 
    icon: any;
    description?: string;
  }[] = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: LayoutDashboard,
      description: 'Overview & metrics'
    },
    { 
      id: 'tutorial', 
      label: 'Tutorial', 
      icon: BookOpen,
      description: 'Interactive training guide'
    },
    { 
      id: 'comprehensive-tutorial', 
      label: 'Academy', 
      icon: GraduationCap,
      description: 'Comprehensive AI training academy'
    },
    { 
      id: 'examples-library', 
      label: 'Examples Library', 
      icon: Brain,
      description: 'Manage conversation examples'
    },
    { 
      id: 'context-manager', 
      label: 'Context Manager', 
      icon: Database,
      description: 'Manage conversation context'
    },
    { 
      id: 'ai-config', 
      label: 'AI Config', 
      icon: Settings,
      description: 'Configuration'
    },
    { 
      id: 'ai-soul', 
      label: 'AI Soul', 
      icon: Eye,
      description: 'Decision monitoring'
    },
    { 
      id: 'knowledge-base', 
      label: 'Knowledge', 
      icon: Database,
      description: 'Cannabis database'
    },
    { 
      id: 'decision-tree', 
      label: 'Decision Tree', 
      icon: GitBranch,
      description: 'Logic flows'
    },
    { 
      id: 'unified-chat', 
      label: 'Chat & Replay', 
      icon: MessageSquare,
      description: 'Test & analyze evolution'
    },
    { 
      id: 'enhanced-flow', 
      label: 'Flow Builder', 
      icon: Zap,
      description: 'AI-powered flows'
    },
    { 
      id: 'analytics', 
      label: 'Analytics', 
      icon: BarChart3,
      description: 'Performance data'
    },
    { 
      id: 'services', 
      label: 'Services', 
      icon: Server,
      description: 'System services'
    },
    { 
      id: 'models', 
      label: 'Deploy', 
      icon: Rocket,
      description: 'Deploy to production'
    },
    { 
      id: 'personality', 
      label: 'AI Personality', 
      icon: Sparkles,
      description: 'Customize AI persona'
    },
    { 
      id: 'search-testing', 
      label: 'Search Test', 
      icon: Search,
      description: 'Test product search API'
    },
    { 
      id: 'live-chat', 
      label: 'Live Chat', 
      icon: Users,
      description: 'Chat with customers'
    },
    { 
      id: 'voice-chat', 
      label: 'Voice Chat', 
      icon: Mic,
      description: 'Voice-enabled multilingual chat'
    },
    { 
      id: 'model-test', 
      label: 'Model Test', 
      icon: Cpu,
      description: 'Test raw model capabilities'
    },
    { 
      id: 'prompt-management', 
      label: 'Prompts', 
      icon: Settings,
      description: 'Manage AI prompts'
    },
  ];

  return (
    <nav className="bg-white border-b border-zinc-200">
      <div className="max-w-7xl mx-auto">
        <div className="flex space-x-1 px-4 sm:px-6 lg:px-8 overflow-x-auto custom-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  relative flex items-center gap-2 px-4 py-3 
                  text-sm font-medium transition-all duration-200
                  whitespace-nowrap group
                  ${isActive 
                    ? 'text-primary-600' 
                    : 'text-zinc-500 hover:text-zinc-900'
                  }
                `}
              >
                <Icon className={`
                  w-4 h-4 transition-all duration-200
                  ${isActive ? 'text-primary-600' : 'text-zinc-400 group-hover:text-zinc-600'}
                `} />
                
                <span className="relative">
                  {tab.label}
                </span>
                
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
                    initial={false}
                    transition={{
                      type: "spring",
                      stiffness: 500,
                      damping: 30
                    }}
                  />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

// Alternative Vertical Sidebar Navigation Component
export function SidebarNavigation({ activeTab, onTabChange }: NavigationProps) {
  const tabs: { 
    id: TabType; 
    label: string; 
    icon: any;
    description?: string;
    category?: string;
  }[] = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: LayoutDashboard,
      category: 'Overview'
    },
    { 
      id: 'chat', 
      label: 'Live Testing', 
      icon: MessageSquare,
      category: 'Testing'
    },
    { 
      id: 'examples-library', 
      label: 'Examples Library', 
      icon: GraduationCap,
      category: 'AI Management'
    },
    { 
      id: 'context-manager', 
      label: 'Context Manager', 
      icon: Brain,
      category: 'AI Management'
    },
    { 
      id: 'model-management', 
      label: 'Model Management', 
      icon: Beaker,
      category: 'AI Management'
    },
    { 
      id: 'personality', 
      label: 'AI Personality', 
      icon: Sparkles,
      category: 'AI Management'
    },
    { 
      id: 'ai-config', 
      label: 'Configuration', 
      icon: Settings,
      category: 'Settings'
    },
    { 
      id: 'decision-tree', 
      label: 'Decision Tree', 
      icon: GitBranch,
      category: 'Workflows'
    },
    { 
      id: 'flow-builder', 
      label: 'Flow Builder', 
      icon: Workflow,
      category: 'Workflows'
    },
    { 
      id: 'analytics', 
      label: 'Analytics', 
      icon: BarChart3,
      category: 'Insights'
    },
    { 
      id: 'history', 
      label: 'History', 
      icon: Clock,
      category: 'Insights'
    },
    { 
      id: 'services', 
      label: 'Services', 
      icon: Server,
      category: 'System'
    },
    { 
      id: 'models', 
      label: 'Deploy', 
      icon: Rocket,
      category: 'System'
    },
  ];

  // Group tabs by category
  const groupedTabs = tabs.reduce((acc, tab) => {
    const category = tab.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(tab);
    return acc;
  }, {} as Record<string, typeof tabs>);

  return (
    <aside className="w-64 bg-white border-r border-zinc-200 min-h-screen">
      <div className="p-4 space-y-6">
        {Object.entries(groupedTabs).map(([category, categoryTabs]) => (
          <div key={category}>
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 px-3">
              {category}
            </h3>
            <div className="space-y-1">
              {categoryTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                      text-sm font-medium transition-all duration-200
                      ${isActive 
                        ? 'bg-primary-50 text-primary-600' 
                        : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900'
                      }
                    `}
                  >
                    <Icon className={`
                      w-4 h-4 transition-colors duration-200
                      ${isActive ? 'text-primary-600' : 'text-zinc-400'}
                    `} />
                    
                    <span className="flex-1 text-left">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}