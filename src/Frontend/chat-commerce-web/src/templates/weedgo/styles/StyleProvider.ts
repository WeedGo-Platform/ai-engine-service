import type { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      
      body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      }
      
      .minimal-transition {
        transition: all 0.2s ease;
      }
      
      .minimal-button {
        background: #000000;
        color: white;
        border: 1px solid #000000;
        transition: all 0.2s ease;
      }
      
      .minimal-button:hover {
        background: white;
        color: #000000;
      }
      
      .minimal-input {
        border: 1px solid #E0E0E0;
        background: white;
        transition: border-color 0.2s ease;
      }
      
      .minimal-input:focus {
        border-color: #000000;
        outline: none;
      }
      
      .minimal-card {
        background: white;
        border: 1px solid #E0E0E0;
      }
      
      .minimal-shadow {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      TopMenuBar: `
        .top-menu-bar {
          background: white;
          border-bottom: 1px solid #E0E0E0;
        }
        .menu-text {
          color: #000000;
          font-weight: 500;
        }
      `,
      ChatMessages: `
        .user-message {
          background: #F5F5F5;
          border-radius: 0.25rem;
        }
        .assistant-message {
          background: white;
          border: 1px solid #E0E0E0;
          border-radius: 0.25rem;
        }
      `,
      ConfigurationPanel: `
        .config-panel {
          background: white;
          border-left: 1px solid #E0E0E0;
        }
        .config-title {
          font-weight: 600;
          color: #000000;
        }
      `,
      ChatInputArea: `
        .input-area {
          background: white;
          border-top: 1px solid #E0E0E0;
        }
      `,
    };
    
    return styles[component] || '';
  }
}