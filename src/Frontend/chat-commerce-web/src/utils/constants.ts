import { ConversationTemplate } from '../types';

export const CONVERSATION_TEMPLATES: ConversationTemplate[] = [
  {
    id: 'first-time',
    category: 'General',
    icon: '🌱',
    title: 'First Time Customer',
    message: "I'm new to cannabis. What would you recommend for a beginner?"
  },
  {
    id: 'pain',
    category: 'Medical',
    icon: '💊',
    title: 'Pain Relief',
    message: "I'm looking for something to help with chronic pain. What strains work best?"
  },
  {
    id: 'sleep',
    category: 'Medical',
    icon: '😴',
    title: 'Sleep Aid',
    message: "I have trouble sleeping. What products can help with insomnia?"
  },
  {
    id: 'anxiety',
    category: 'Medical',
    icon: '😰',
    title: 'Anxiety Relief',
    message: "I need something for anxiety that won't make me too drowsy. Any recommendations?"
  },
  {
    id: 'creative',
    category: 'Effects',
    icon: '🎨',
    title: 'Creative Boost',
    message: "I want something that enhances creativity and focus. What do you suggest?"
  },
  {
    id: 'social',
    category: 'Effects',
    icon: '🎉',
    title: 'Social Enhancement',
    message: "What's good for social situations? I want to feel relaxed but still engaged."
  },
  {
    id: 'indica-sativa',
    category: 'Education',
    icon: '📚',
    title: 'Indica vs Sativa',
    message: "Can you explain the difference between indica and sativa?"
  },
  {
    id: 'edibles',
    category: 'Products',
    icon: '🍪',
    title: 'Edibles Info',
    message: "How do edibles work differently than smoking? What should I know?"
  },
  {
    id: 'dosing',
    category: 'Education',
    icon: '⚖️',
    title: 'Proper Dosing',
    message: "How do I find the right dose for me? I don't want to overdo it."
  },
  {
    id: 'terpenes',
    category: 'Advanced',
    icon: '🧪',
    title: 'Terpene Effects',
    message: "Can you explain how different terpenes affect the cannabis experience?"
  }
];