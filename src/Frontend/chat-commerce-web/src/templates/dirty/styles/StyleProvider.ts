import { IStyleProvider } from '../../../core/contracts/template.contracts';

export class StyleProvider implements IStyleProvider {
  getGlobalStyles(): string {
    return `
      @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600&family=Barlow:wght@400;500;700&display=swap');
      
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        font-family: 'Barlow', sans-serif;
        background: linear-gradient(135deg, #1C1C1C 0%, #2B2B2B 50%, #1A1A1A 100%);
        color: #D3D3D3;
        line-height: 1.6;
      }
      
      .dirty-layout {
        background: linear-gradient(135deg, #1C1C1C 0%, #2B2B2B 50%, #1A1A1A 100%);
        color: #D3D3D3;
      }
      
      /* Dirty/Grunge Scrollbar */
      ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
      }
      
      ::-webkit-scrollbar-track {
        background: #1C1C1C;
        border: 1px solid #333;
      }
      
      ::-webkit-scrollbar-thumb {
        background: #555;
        border: 1px solid #666;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: #777;
      }
    `;
  }

  getComponentStyles(component: string): string {
    const styles: Record<string, string> = {
      container: 'max-w-7xl mx-auto px-4',
      card: 'bg-black/80 border border-gray-800 rounded-none p-6 shadow-2xl',
      'button-primary': 'bg-gray-800 text-gray-200 hover:bg-gray-700 px-4 py-2 border border-gray-600',
      input: 'bg-black/60 border border-gray-700 text-gray-300 px-3 py-2',
    };
    
    return styles[component] || '';
  }
}