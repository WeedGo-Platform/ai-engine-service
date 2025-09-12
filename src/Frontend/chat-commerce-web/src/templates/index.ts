import { getTemplateFactory } from '../core/providers/template.provider';
import { PotPalaceTemplateProvider } from './pot-palace/provider';
import { ModernMinimalTemplateProvider } from './modern-minimal/provider';
import { DarkTechTemplateProvider } from './dark-tech/provider';
import { RastaVibesTemplateProvider } from './rasta-vibes/provider';
import { WeedGoTemplateProvider } from './weedgo/provider';
import { VintageTemplateProvider } from './vintage/provider';
import { DirtyTemplateProvider } from './dirty/provider';
import { MetalTemplateProvider } from './metal/provider';

// Register all templates
export function registerTemplates() {
  const factory = getTemplateFactory();
  
  // Register WeedGo theme (default professional)
  factory.register('weedgo', new WeedGoTemplateProvider());
  
  // Register Pot Palace theme
  factory.register('pot-palace', new PotPalaceTemplateProvider());
  
  // Register Modern/Minimal theme
  factory.register('modern-minimal', new ModernMinimalTemplateProvider());
  
  // Register Dark/Tech theme
  factory.register('dark-tech', new DarkTechTemplateProvider());
  
  // Register Rasta Vibes theme
  factory.register('rasta-vibes', new RastaVibesTemplateProvider());
  
  // Register Vintage theme
  factory.register('vintage', new VintageTemplateProvider());
  
  // Register Dirty theme
  factory.register('dirty', new DirtyTemplateProvider());
  
  // Register Metal theme
  factory.register('metal', new MetalTemplateProvider());
}

// Export template names
export const TEMPLATE_NAMES = {
  WEEDGO: 'weedgo',
  POT_PALACE: 'pot-palace',
  MODERN_MINIMAL: 'modern-minimal',
  DARK_TECH: 'dark-tech',
  RASTA_VIBES: 'rasta-vibes',
  VINTAGE: 'vintage',
  DIRTY: 'dirty',
  METAL: 'metal',
} as const;

// Export default template - Modern Minimal theme
export const DEFAULT_TEMPLATE = TEMPLATE_NAMES.MODERN_MINIMAL;