import { createContext, useContext, type ReactNode } from 'react';
import type { 
  ITemplateProvider,
  ITemplateFactory,
  TemplateComponents,
  ILayout,
  IStyleProvider,
  ITheme
} from '../contracts/template.contracts';

// Template Context
const TemplateContext = createContext<ITemplateProvider | null>(null);

// Template Provider Hook
export function useTemplate() {
  const context = useContext(TemplateContext);
  if (!context) {
    throw new Error('useTemplate must be used within a TemplateProvider');
  }
  return context;
}

// Template Provider Component
export function TemplateProvider({ 
  children, 
  provider 
}: { 
  children: ReactNode; 
  provider: ITemplateProvider;
}) {
  return (
    <TemplateContext.Provider value={provider}>
      {children}
    </TemplateContext.Provider>
  );
}

// Base Template Provider Implementation
export abstract class BaseTemplateProvider implements ITemplateProvider {
  constructor(public name: string) {}

  abstract getComponent<T extends keyof TemplateComponents>(
    component: T
  ): TemplateComponents[T];
  
  abstract getLayout(): ILayout;
  abstract getStyles(): IStyleProvider;
  abstract getTheme(): ITheme;
}

// Template Factory Implementation
export class TemplateFactory implements ITemplateFactory {
  private templates = new Map<string, ITemplateProvider>();

  register(templateName: string, provider: ITemplateProvider): void {
    this.templates.set(templateName, provider);
  }

  create(templateName: string): ITemplateProvider {
    const provider = this.templates.get(templateName);
    if (!provider) {
      // Fallback to default template
      const defaultProvider = this.templates.get('weedgo');
      if (!defaultProvider) {
        throw new Error(`Template "${templateName}" not found and no default available`);
      }
      console.warn(`Template "${templateName}" not found, using default "weedgo"`);
      return defaultProvider;
    }
    return provider;
  }

  getAvailableTemplates(): string[] {
    return Array.from(this.templates.keys());
  }
}

// Singleton factory instance
let templateFactory: TemplateFactory | null = null;

export function getTemplateFactory(): TemplateFactory {
  if (!templateFactory) {
    templateFactory = new TemplateFactory();
  }
  return templateFactory;
}

// Dynamic component loader
export function DynamicComponent<T extends keyof TemplateComponents>({
  component,
  ...props
}: {
  component: T;
} & (TemplateComponents[T] extends (...args: any) => any ? Parameters<TemplateComponents[T]>[0] : any)) {
  const template = useTemplate();
  const Component = template.getComponent(component) as any;
  
  if (!Component) {
    console.error(`Component "${component}" not found in template`);
    return <div>Component {component} not found</div>;
  }
  
  // Just try to render it - React will throw a proper error if it's not valid
  try {
    return <Component {...props} />;
  } catch (error) {
    console.error(`Error rendering component "${component}":`, error, Component);
    return <div>Error rendering component: {component}</div>;
  }
}

// Layout wrapper
export function TemplateLayout({ children, ...props }: Parameters<ILayout>[0]) {
  const template = useTemplate();
  const Layout = template.getLayout();
  return <Layout {...props}>{children}</Layout>;
}