import { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  private styles: string[] = [];

  constructor() {
    this.initializeStyles();
  }

  private initializeStyles(): void {
    // Import CSS files
    this.styles = [
      '/src/templates/rasta-vibes/styles/scrollbar.css',
      '/src/templates/rasta-vibes/styles/animations.css',
    ];

    // Add Google Fonts for Rasta typography
    this.injectFonts();
  }

  private injectFonts(): void {
    if (typeof window !== 'undefined' && !document.getElementById('rasta-vibes-fonts')) {
      const link = document.createElement('link');
      link.id = 'rasta-vibes-fonts';
      link.rel = 'stylesheet';
      link.href = 'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rubik:wght@300;400;500;600;700&family=Ubuntu:wght@300;400;500;700&family=Fira+Code:wght@400;500;600&display=swap';
      document.head.appendChild(link);
    }
  }

  getStyles(): string[] {
    return this.styles;
  }

  getGlobalStyles(): string {
    return `
      /* Global Rasta Vibes Theme Styles */
      .rasta-vibes-theme {
        --rasta-red: #DC2626;
        --rasta-gold: #FCD34D;
        --rasta-green: #16A34A;
        --rasta-black: #000000;
        --rasta-brown: #8B4513;
      }
    `;
  }

  getComponentStyles(componentName: string): string {
    const componentStyles: Record<string, string> = {
      'ChatWindow': `
        .rasta-chat-window {
          background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(51, 51, 51, 0.85) 100%);
          border: 3px solid transparent;
          border-image: linear-gradient(45deg, #DC2626, #FCD34D, #16A34A) 1;
        }
      `,
      'ChatInput': `
        .rasta-chat-input {
          background: rgba(0, 0, 0, 0.6);
          border: 2px solid rgba(252, 211, 77, 0.3);
          color: #FCD34D;
        }
        .rasta-chat-input:focus {
          border-color: #FCD34D;
          box-shadow: 0 0 20px rgba(252, 211, 77, 0.2);
        }
      `,
      'Button': `
        .rasta-button {
          background: linear-gradient(135deg, #DC2626 0%, #FCD34D 50%, #16A34A 100%);
          background-size: 200% 200%;
          animation: rasta-gradient 3s ease infinite;
        }
      `
    };
    
    return componentStyles[componentName] || '';
  }

  injectStyles(): void {
    if (typeof window !== 'undefined') {
      this.styles.forEach(style => {
        if (!document.querySelector(`link[href="${style}"]`)) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = style;
          document.head.appendChild(link);
        }
      });

      // Inject inline styles for global Rasta theme
      if (!document.getElementById('rasta-vibes-global-styles')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'rasta-vibes-global-styles';
        styleElement.innerHTML = `
          /* Global Rasta Vibes Styles */
          .rasta-vibes-theme {
            --rasta-red: #DC2626;
            --rasta-gold: #FCD34D;
            --rasta-green: #16A34A;
            --rasta-black: #000000;
            --rasta-brown: #8B4513;
          }

          /* Floating Music Notes Background */
          .rasta-vibes-theme::before {
            content: '♪ ♫ ♪';
            position: fixed;
            top: 10%;
            left: 5%;
            font-size: 2rem;
            color: rgba(252, 211, 77, 0.1);
            animation: float-notes 20s linear infinite;
            pointer-events: none;
            z-index: 0;
          }

          .rasta-vibes-theme::after {
            content: '♫ ♪ ♫';
            position: fixed;
            top: 50%;
            right: 5%;
            font-size: 2.5rem;
            color: rgba(22, 163, 74, 0.1);
            animation: float-notes 25s linear infinite reverse;
            pointer-events: none;
            z-index: 0;
          }

          /* Lion of Judah Watermark */
          .rasta-lion-watermark {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 100px;
            height: 100px;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="60" fill="rgba(252,211,77,0.1)">👑</text><text x="50%" y="80%" text-anchor="middle" dy=".3em" font-size="30" fill="rgba(252,211,77,0.1)">🦁</text></svg>') no-repeat center;
            opacity: 0.3;
            pointer-events: none;
            z-index: 0;
            animation: lion-glow 4s ease-in-out infinite;
          }

          /* Rasta Border Gradient */
          .rasta-border-gradient {
            position: relative;
            background: #1A1A1A;
            border-radius: 1rem;
          }

          .rasta-border-gradient::before {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            background: linear-gradient(45deg, #DC2626, #FCD34D, #16A34A, #DC2626);
            border-radius: 1rem;
            background-size: 300% 300%;
            animation: rasta-wave 4s ease infinite;
            z-index: -1;
          }

          /* Custom Selection Colors */
          .rasta-vibes-theme ::selection {
            background: rgba(252, 211, 77, 0.3);
            color: #FCD34D;
          }

          .rasta-vibes-theme ::-moz-selection {
            background: rgba(252, 211, 77, 0.3);
            color: #FCD34D;
          }

          /* Focus Styles */
          .rasta-vibes-theme *:focus {
            outline: 2px solid rgba(252, 211, 77, 0.5);
            outline-offset: 2px;
          }

          /* Transitions */
          .rasta-vibes-theme * {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          }
        `;
        document.head.appendChild(styleElement);
      }
    }
  }

  removeStyles(): void {
    if (typeof window !== 'undefined') {
      // Remove style links
      this.styles.forEach(style => {
        const link = document.querySelector(`link[href="${style}"]`);
        if (link) {
          link.remove();
        }
      });

      // Remove fonts
      const fontsLink = document.getElementById('rasta-vibes-fonts');
      if (fontsLink) {
        fontsLink.remove();
      }

      // Remove global styles
      const globalStyles = document.getElementById('rasta-vibes-global-styles');
      if (globalStyles) {
        globalStyles.remove();
      }
    }
  }
}