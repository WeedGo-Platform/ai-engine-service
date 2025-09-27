/**
 * Learning Type Definitions
 * Covers all learning and pattern recognition data structures
 */

export interface ILearningMetrics {
  patternCount: number;
  feedbackPositive: number; // percentage
  adaptationsToday: number;
  learningRate: number;
  confidenceScore: number;
  improvement_rate?: number;
  model_accuracy?: number;
}

export interface IPattern {
  id: string;
  type: 'conversation_flow' | 'user_behavior' | 'error_pattern' | 'optimization' | 'custom';
  name?: string;
  frequency: number;
  confidence: number;
  last_seen: string;
  first_seen?: string;
  occurrences?: number;
  evolution?: Array<{
    timestamp: string;
    accuracy: number;
    frequency: number;
  }>;
  related_patterns?: string[];
}

export interface IFeedback {
  id: string;
  timestamp: string;
  type: 'positive' | 'negative' | 'neutral';
  rating?: number; // 1-5
  message?: string;
  user_id?: string;
  session_id?: string;
  agent_id?: string;
  categories?: string[];
  sentiment?: {
    score: number;
    magnitude: number;
  };
  improvement_suggestions?: string[];
}

export interface IFeedbackAnalysis {
  total_feedback: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  average_rating: number;
  categories: Array<{
    name: string;
    rating: number;
    count: number;
  }>;
  improvement_areas: string[];
  trending_topics?: string[];
}

export interface IAdaptation {
  id: string;
  timestamp: string;
  type: 'parameter' | 'strategy' | 'model' | 'rule';
  description: string;
  old_value?: any;
  new_value?: any;
  reason?: string;
  impact?: {
    performance_change: number;
    accuracy_change: number;
  };
  rollback_available?: boolean;
}

export interface ILearningHistory {
  date: string;
  metrics: ILearningMetrics;
  patterns_discovered: number;
  adaptations_made: number;
  feedback_received: number;
  performance_score: number;
}