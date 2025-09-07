import { getTemplateFactory } from '../core/providers/template.provider';
import { PotPalaceTemplateProvider } from './pot-palace/provider';
import { ModernMinimalTemplateProvider } from './modern-minimal/provider';
import { DarkTechTemplateProvider } from './dark-tech/provider';

// Register all templates
export function registerTemplates() {
  const factory = getTemplateFactory();
  
  // Register Pot Palace theme
  factory.register('pot-palace', new PotPalaceTemplateProvider());
  
  // Register Modern/Minimal theme
  factory.register('modern-minimal', new ModernMinimalTemplateProvider());
  
  // Register Dark/Tech theme
  factory.register('dark-tech', new DarkTechTemplateProvider());
}

// Export template names
export const TEMPLATE_NAMES = {
  POT_PALACE: 'pot-palace',
  MODERN_MINIMAL: 'modern-minimal',
  DARK_TECH: 'dark-tech',
} as const;

// Export default template
export const DEFAULT_TEMPLATE = TEMPLATE_NAMES.POT_PALACE;