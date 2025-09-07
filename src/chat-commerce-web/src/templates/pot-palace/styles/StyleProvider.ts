import type { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
      }
      
      .animate-float {
        animation: float 3s ease-in-out infinite;
      }
      
      .animate-pulse {
        animation: pulse 2s ease-in-out infinite;
      }
      
      .gradient-text {
        background: linear-gradient(135deg, #E91ED4 0%, #FF006E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .glass-effect {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
      }
      
      .pot-palace-button {
        background: linear-gradient(135deg, #E91ED4 0%, #FF006E 100%);
        transition: all 0.3s ease;
      }
      
      .pot-palace-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(233, 30, 212, 0.3);
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      TopMenuBar: `
        .top-menu-bar {
          background: linear-gradient(135deg, #E91ED4 0%, #FF006E 100%);
          border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
      `,
      ChatMessages: `
        .user-message {
          background: rgba(233, 30, 212, 0.1);
          border-left: 3px solid #E91ED4;
        }
        .assistant-message {
          background: rgba(255, 255, 255, 0.95);
          border-left: 3px solid #FF006E;
        }
      `,
      ConfigurationPanel: `
        .config-panel {
          background: rgba(255, 255, 255, 0.98);
          box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
        }
      `,
    };
    
    return styles[component] || '';
  }
}