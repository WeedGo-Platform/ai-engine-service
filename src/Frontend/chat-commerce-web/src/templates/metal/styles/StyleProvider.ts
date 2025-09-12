import { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;600;700&display=swap');
      
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        font-family: 'Rajdhani', sans-serif;
        background: linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 50%, #0F0F0F 100%);
        color: #C0C0C0;
        line-height: 1.6;
      }
      
      .metal-layout {
        background: linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 50%, #0F0F0F 100%);
        color: #C0C0C0;
      }
      
      /* Metal Scrollbar */
      ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
      }
      
      ::-webkit-scrollbar-track {
        background: #0A0A0A;
        border: 1px solid #333;
      }
      
      ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #666 0%, #333 100%);
        border: 1px solid #777;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #888 0%, #555 100%);
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      container: 'max-w-7xl mx-auto px-4',
      card: 'bg-gray-900/90 border border-gray-700 rounded-sm p-6 shadow-2xl',
      'button-primary': 'bg-gradient-to-r from-gray-700 to-gray-800 text-white hover:from-gray-600 hover:to-gray-700 px-4 py-2',
      input: 'bg-black/70 border border-gray-600 text-gray-300 px-3 py-2',
    };
    
    return styles[component] || '';
  }
}
