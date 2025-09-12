import type { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
      
      body {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
      }
      
      @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); }
        50% { box-shadow: 0 0 30px rgba(0, 255, 136, 0.8); }
      }
      
      @keyframes scan {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
      }
      
      @keyframes flicker {
        0%, 100% { opacity: 1; }
        92% { opacity: 1; }
        93% { opacity: 0.8; }
        94% { opacity: 1; }
        95% { opacity: 0.9; }
        96% { opacity: 1; }
      }
      
      .tech-glow {
        animation: glow 2s ease-in-out infinite;
      }
      
      .tech-flicker {
        animation: flicker 3s ease-in-out infinite;
      }
      
      .tech-button {
        background: linear-gradient(135deg, #00FF88 0%, #00D4FF 100%);
        color: #0A0E1A;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
      }
      
      .tech-button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
      }
      
      .tech-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
      }
      
      .tech-button:hover::before {
        left: 100%;
      }
      
      .tech-input {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(0, 255, 136, 0.3);
        color: #E0E6ED;
        transition: all 0.3s ease;
      }
      
      .tech-input:focus {
        border-color: #00FF88;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        outline: none;
      }
      
      .tech-card {
        background: rgba(26, 31, 46, 0.9);
        border: 1px solid rgba(0, 255, 136, 0.2);
        position: relative;
      }
      
      .tech-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00FF88, transparent);
        animation: scan 3s linear infinite;
      }
      
      .terminal-text {
        font-family: 'JetBrains Mono', monospace;
        color: #00FF88;
      }
      
      ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }
      
      ::-webkit-scrollbar-track {
        background: #0A0E1A;
      }
      
      ::-webkit-scrollbar-thumb {
        background: rgba(0, 255, 136, 0.3);
        border-radius: 4px;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 255, 136, 0.5);
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      TopMenuBar: `
        .top-menu-bar {
          background: rgba(10, 14, 26, 0.95);
          border-bottom: 1px solid rgba(0, 255, 136, 0.3);
          backdrop-filter: blur(10px);
        }
        .menu-text {
          color: #00FF88;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 500;
        }
      `,
      ChatMessages: `
        .user-message {
          background: rgba(0, 255, 136, 0.1);
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-left: 3px solid #00FF88;
        }
        .assistant-message {
          background: rgba(26, 31, 46, 0.9);
          border: 1px solid rgba(0, 212, 255, 0.3);
          border-left: 3px solid #00D4FF;
        }
        .message-text {
          font-family: 'JetBrains Mono', monospace;
        }
      `,
      ConfigurationPanel: `
        .config-panel {
          background: rgba(26, 31, 46, 0.95);
          border-left: 1px solid rgba(0, 255, 136, 0.3);
          backdrop-filter: blur(10px);
        }
        .config-title {
          color: #00FF88;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
      `,
      ChatInputArea: `
        .input-area {
          background: rgba(10, 14, 26, 0.95);
          border-top: 1px solid rgba(0, 255, 136, 0.3);
        }
      `,
      Notification: `
        .notification {
          background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 212, 255, 0.2));
          border: 1px solid rgba(0, 255, 136, 0.5);
          color: #E0E6ED;
        }
      `,
    };
    
    return styles[component] || '';
  }
}