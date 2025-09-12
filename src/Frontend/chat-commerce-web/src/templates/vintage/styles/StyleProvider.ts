import { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Crimson+Text:wght@400;600&display=swap');
      
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        font-family: 'Crimson Text', Georgia, serif;
        background: linear-gradient(135deg, #F5E6D3 0%, #E6D7C3 100%);
        color: #3E2723;
        line-height: 1.6;
      }
      
      .vintage-layout {
        background: linear-gradient(135deg, #F5E6D3 0%, #E6D7C3 100%);
        color: #3E2723;
      }
      
      /* Vintage Scrollbar */
      ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
      }
      
      ::-webkit-scrollbar-track {
        background: #F5E6D3;
        border: 1px solid #8B4513;
      }
      
      ::-webkit-scrollbar-thumb {
        background: #8B4513;
        border-radius: 2px;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: #654321;
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      container: 'max-w-6xl mx-auto px-4',
      card: 'bg-cornsilk border-2 border-saddle-brown rounded p-6 shadow-lg',
      'button-primary': 'bg-saddle-brown text-cornsilk hover:bg-sienna px-4 py-2 rounded',
      input: 'border-2 border-saddle-brown rounded px-3 py-2 bg-ivory',
    };
    
    return styles[component] || '';
  }
}